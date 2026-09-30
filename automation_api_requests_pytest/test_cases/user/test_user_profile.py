# 【任务 #4.3：用户资料 —— 单例资源的读改 + 字段白名单 + 越权】
#
# /user/profile 是「单例资源」：一个账号只有一份资料，GET 读它、PUT 改它。
# 骨架和 /health/info 一样（写读回环），但这个接口有 3 个自己特有的考点：
#
#   ① 【鉴权】没 token / 假 token / 被篡改的 token → 401
#   ② 【字段白名单】哪些字段传了能改、哪些传了等于没传
#   ③ 【越权】怎么设法读/改"别人的"资料 —— 结论：读不到，本文把路全堵一遍
#
# ⚠️ 下面每条断言都来自 2026-09-30 的**实测**，不是照文档推的。实测结论：
#   · 无 token / 伪 token → 401，且**响应体为空**（不是 JSON！不能调 resp.json()）
#   · 身份来自 token 里的 sub（=userId），query / 路径 / header 都塞不进别人的 id
#   · PUT 是**局部更新**：只传 phone，username / email / avatar 都保留
#   · 可改字段：username（1~50 字符 + 查重）、phone（必须 11 位数字）、avatar
#   · 不可改字段：email / role / status / userId / createTime / updateTime
#     —— 传了既不生效、也**不报错**（照样返回 200「更新成功」）
#
# ⚠️ 文件末尾有一条 xfail（缺陷 #9），别以为是写错了。

import base64
import json
import time
from datetime import datetime

import pytest

from common.db import execute, query
from config import TEST_USER
from test_cases.toolbox.logger import log_response

# updateTime 的格式。实测精度只到**秒**：'2026-09-30T17:04:30'
TS_FMT = "%Y-%m-%dT%H:%M:%S"

# GET /user/profile 返回的字段全集（实测 9 个）
EXPECTED_FIELDS = {
    "userId", "username", "email", "phone", "avatar",
    "role", "status", "createTime", "updateTime",
}


# ============================================================
# 夹具
# ============================================================


@pytest.fixture
def other_user(api):
    """第二个身份：注册一个新账号（注册即返回 token，一步到位），用完删掉。

    ⚠️ 夹具粒度：它**只服务于"需要双身份"的用例**。
       pytest 夹具是懒加载的 —— 用例函数签名里没写 other_user，它就一次都不会执行，
       所以不会白白多注册一堆账号（这是本项目的约定：夹具粒度要匹配用例需求）。
    """
    stamp = int(time.time() * 1000)
    email = f"tmp_profile_{stamp}@qq.com"
    body = api.assert_ok(api.post("/auth/register", json={
        "username": f"tmp_profile_{stamp}",
        "email": email,
        "password": "123456",
        "phone": "17888888888",
    }))
    d = body["data"]
    yield {
        "userId": d["userId"],
        "username": d["username"],
        "email": email,
        "headers": {"Authorization": f"Bearer {d['token']}"},
    }
    execute("delete from `user` where email = %s", (email,))


@pytest.fixture
def restore_profile(api, auth_headers):
    """用例开始前记下主账号的资料原貌，结束后原样写回。

    为什么必须还原？profile 是**单例**：改它等于改全局状态，
    后面每条读 profile 的用例都会看到被你改过的值 —— 这叫"用例间互相污染"。
    用 yield 夹具还原，比写在用例最后一行可靠：中间断言挂了也照样执行。

    ⚠️ 只还原 username 和 phone。avatar 传 null / 空串都会被后端忽略（实测），
       还原不回去，所以本文件里没有用例去动 avatar。
    """
    before = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]
    yield before
    api.put("/user/profile", headers=auth_headers,
            json={"username": before["username"], "phone": before["phone"]})


def _uniq_name(total_len: int) -> str:
    """造一个"长度正好 total_len、且带时间戳"的用户名，避免和库里已有的撞车。"""
    base = f"tmp{int(time.time() * 1000)}"
    return (base + "x" * max(0, total_len - len(base)))[:total_len]


# ============================================================
# 组 1：鉴权 —— 没身份 / 假身份 / 被篡改的身份
# ============================================================


def test_profile_without_token(api):
    """不带 token → 401。

    ⚠️ 这里的 401 是**空响应体**（不是 JSON），所以只能断 status_code，
       写成 resp.json() 会直接抛 JSONDecodeError。
    """
    resp = api.get("/user/profile")
    assert resp.status_code == 401, f"无 token 应被拒，实际 {resp.status_code}"
    assert resp.content == b"", "401 应为空体（实测契约）"


FORMAT_ERROR_HEADERS = [
    ("少一段", "Bearer abc.def"),
    ("非 base64", "Bearer !!!"),
    ("缺 Bearer 前缀", "abc.def.ghi"),
    ("Basic 前缀", "Basic abc.def.ghi"),
    ("Bearer 后为空", "Bearer "),
    ("bearer 小写", "bearer abc.def.ghi"),
]


@pytest.mark.parametrize("case_name,auth_value", FORMAT_ERROR_HEADERS,
                         ids=[c[0] for c in FORMAT_ERROR_HEADERS])
def test_profile_with_format_error_token(api, case_name, auth_value):
    """token 形式不对 → 401。

    顺带证明一件事：`Bearer` 前缀是**大小写敏感**的（小写 bearer 照样被拒）。
    """
    resp = api.get("/user/profile", headers={"Authorization": auth_value})
    assert resp.status_code == 401, f"{case_name} 应被拒，实际 {resp.status_code}"
    assert resp.content == b""


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64d(txt: str) -> bytes:
    return base64.urlsafe_b64decode(txt + "=" * (-len(txt) % 4))


def _tamper_signature(token):
    """把签名那段换成乱码。"""
    h, p, _ = token.split(".")
    return f"{h}.{p}.AAAAAAAA"


def _tamper_subject(token):
    """把 JWT 里的 sub（=userId）改成 1 —— 试图"变成别人"。

    JWT 的 payload 只是 base64，**不是加密**，任何人都能解开改。
    能不能得逞，全看后端验不验签名。
    """
    h, p, sig = token.split(".")
    payload = json.loads(_b64d(p))
    payload["sub"] = "1"
    new_p = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    return f"{h}.{new_p}.{sig}"          # payload 改了，签名还是老的


def _tamper_alg_none(token):
    """经典手法：把 header 里的 alg 改成 none，签名置空。"""
    h, p, _ = token.split(".")
    new_h = _b64e(json.dumps({"alg": "none"}, separators=(",", ":")).encode())
    return f"{new_h}.{p}."


TAMPER_CASES = [
    ("签名乱改", _tamper_signature),
    ("改 sub 冒充别人", _tamper_subject),
    ("alg=none 空签名", _tamper_alg_none),
]


@pytest.mark.parametrize("case_name,forge", TAMPER_CASES, ids=[c[0] for c in TAMPER_CASES])
def test_profile_with_tampered_token(api, token, case_name, forge):
    """篡改 token → 必须 401。

    这是"变成别人"的**唯一可能路径**（其余塞 id 的位置实测都无效），
    所以值得单独守一条：一旦哪天放开签名校验或换了弱密钥，这条会立刻变红。
    """
    resp = api.get("/user/profile", headers={"Authorization": f"Bearer {forge(token)}"})
    assert resp.status_code == 401, f"{case_name} 竟然通过了！"
    assert resp.content == b""


# ============================================================
# 组 2：GET 的契约
# ============================================================


def test_get_user_profile(api, auth_headers):
    """GET 返回的字段集合必须**精确等于**这 9 个。

    为什么用"集合相等"而不是"包含"？包含式断言漏字段抓不出来。
    用相等：后端哪天多给一个字段（可能要同步给前端）、少给一个（前端可能正在用），
    都会被发现，值得人看一眼。

    （这条原来是只调 log_response 打印、没有断言的版本 ——
      没有断言的用例**永远是绿的**，跑一万次也不会告诉你任何问题。
      打印是给自己看的，断言才是给 CI 看的。现在把断言补上。）
    """
    resp = api.get("/user/profile", headers=auth_headers)
    log_response(resp)                       # 想细看返回体时留着这行
    data = api.assert_ok(resp)["data"]

    assert set(data.keys()) == EXPECTED_FIELDS, (
        f"字段集合变了：多出 {set(data) - EXPECTED_FIELDS}，"
        f"少了 {EXPECTED_FIELDS - set(data)}"
    )
    assert data["email"] == TEST_USER["email"]
    assert data["userId"] == 2               # 测试账号固定是 userId=2（实测）
    assert data["role"] == "user"


def test_get_profile_never_exposes_password(api, auth_headers):
    """响应里绝不能出现密码。

    安全底线断言：哪怕是加密后的哈希也不该返回给前端。
    这里在整个响应文本里搜 "password"，比逐个字段看更严 ——
    防止密码藏在某个嵌套结构里。
    """
    resp = api.get("/user/profile", headers=auth_headers)
    api.assert_ok(resp)
    assert "password" not in resp.text.lower()


def test_get_profile_is_idempotent(api, auth_headers):
    """连读两次结果必须一模一样 —— 读操作不该有副作用。"""
    first = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]
    second = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]
    assert first == second, "同一份资料，两次 GET 的结果竟然不一致"


# ============================================================
# 组 3：PUT —— 局部更新 + 字段白名单
# ============================================================


def test_update_single_field_keeps_others(api, auth_headers, restore_profile):
    """PUT 是**局部更新**：只传一个字段，其余字段原地不动。

    ⚠️ 这条守的是真实项目里最常见的事故："改完手机号，头像没了"。
       如果后端实现成全量覆盖，没传的字段就被 null 冲掉了。
    """
    before = restore_profile

    api.assert_ok(api.put("/user/profile", headers=auth_headers,
                          json={"phone": "17800009999"}))

    after = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]
    assert after["phone"] == "17800009999"              # 传了的：生效
    assert after["username"] == before["username"]      # 没传的：原封不动
    assert after["email"] == before["email"]
    assert after["avatar"] == before["avatar"]
    assert after["userId"] == before["userId"]
    assert after["createTime"] == before["createTime"]


def test_update_ignores_non_editable_fields(api, auth_headers, restore_profile, other_user):
    """一次请求里混传「可改」和「不可改」字段：可改的生效，不可改的原地不动。

    哪些算"不可改"？看前端编辑页 + API.md —— 只有 用户名 / 手机号 / 头像 三个输入框，
    所以 email、role、status、userId、时间戳**都不该动**。

    ⚠️ 这里断言的是"它们不会被动"，**不是**"它们应该能改"。
       （曾把"email 传了不生效"当缺陷报，那是错的 —— 需求里就没有改邮箱这个功能。
         真正的风险只是"传了却回 200 更新成功"、调用方无法察觉，属于契约清晰度问题。）
    """
    before = restore_profile
    new_name = _uniq_name(20)

    api.assert_ok(api.put("/user/profile", headers=auth_headers, json={
        "username": new_name,                   # 可改 → 应生效
        "email": other_user["email"],           # 不可改 → 不该动
        "role": "admin",                        # 提权尝试 → 不该动
        "status": 0,                            # 想禁用自己 → 不该动
        "userId": other_user["userId"],         # 想把身份指向别人 → 不该动
        "createTime": "1970-01-01T00:00:00",    # 篡改时间 → 不该动
    }))

    after = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]

    assert after["username"] == new_name, "可改字段应当生效"
    assert after["email"] == before["email"], "邮箱不是可编辑字段，不该被改"
    assert after["role"] == "user", "普通用户不能通过改资料给自己提权成 admin"
    assert after["status"] == before["status"], "不能通过改资料禁用自己的账号"
    assert after["userId"] == before["userId"], "身份只能来自 token，不能被 body 覆盖"
    assert after["createTime"] == before["createTime"], "创建时间不可篡改"


# ============================================================
# 组 4：PUT —— 唯一性与字段边界
# ============================================================


def test_update_username_to_existing_rejected(api, auth_headers, restore_profile, other_user):
    """改用别人已占用的用户名 → 400「用户名已存在」，且自己的资料不受影响。"""
    resp = api.put("/user/profile", headers=auth_headers,
                   json={"username": other_user["username"]})

    # ⚠️ "期望失败"的用例**不能**用 api.assert_ok（它是专门断言成功的），要手写三层断言
    assert resp.status_code == 400, f"抢占别人的用户名竟然成功了：{resp.status_code}"
    body = resp.json()
    assert body["code"] == 400
    assert body["message"] == "用户名已存在"          # 实测原文

    after = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]
    assert after["username"] == restore_profile["username"], "被拒之后自己的名字不该被改"


def test_update_username_to_own_value_ok(api, auth_headers, restore_profile):
    """把用户名改成"自己现在这个名字" → 应该成功，不能报"已存在"。

    这是唯一性校验最容易写错的地方：查重时忘了排除自己，
    结果用户不改名字、只想改手机号都会 400。这条专门守这个边界。
    """
    resp = api.put("/user/profile", headers=auth_headers,
                   json={"username": restore_profile["username"]})
    api.assert_ok(resp)

    after = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]
    assert after["username"] == restore_profile["username"]


USERNAME_LEN_CASES = [
    ("空串", "", 400),
    ("1 字符", "a", 200),                   # 实测 'a' 未被占用
    ("50 字符", _uniq_name(50), 200),       # 上限
    ("51 字符", "c" * 51, 400),             # 越界 1
]


@pytest.mark.parametrize("case_name,username,expected", USERNAME_LEN_CASES,
                         ids=[c[0] for c in USERNAME_LEN_CASES])
def test_update_username_length_boundary(api, auth_headers, restore_profile,
                                         case_name, username, expected):
    """用户名长度边界：1~50 合法，0 和 51 越界。

    为什么专挑 0/1 和 50/51？—— 边界值法：**错误最常发生在边界上**。
    51 和 100 报的是同一句错，所以只测 51 就够，不必再测 100。
    """
    resp = api.put("/user/profile", headers=auth_headers, json={"username": username})

    assert resp.status_code == expected, (
        f"{case_name}：期望 {expected}，实际 {resp.status_code}，body={resp.text[:200]}"
    )
    if expected == 400:
        assert resp.json()["message"] == "用户名长度需在 1 到 50 个字符之间"


PHONE_CASES = [
    ("纯字母", "abc"),
    ("位数不足", "123"),
    ("带横线", "139-0000-0000"),
    ("空串", ""),
    ("超长", "139000000000000000000"),
]


@pytest.mark.parametrize("case_name,phone", PHONE_CASES, ids=[c[0] for c in PHONE_CASES])
def test_update_phone_invalid_format_rejected(api, auth_headers, restore_profile,
                                              case_name, phone):
    """手机号格式不对 → 400「手机号格式不正确」。

    实测规则：必须是 11 位纯数字（13900000000 通过，其余全部 400）。
    """
    resp = api.put("/user/profile", headers=auth_headers, json={"phone": phone})

    assert resp.status_code == 400, f"{case_name} 应被拒，实际 {resp.status_code}"
    body = resp.json()
    assert body["code"] == 400
    assert body["message"] == "手机号格式不正确"


# ============================================================
# 组 5：越权 —— 能不能拿到 / 改到别人的资料
# ============================================================


PROBE_POSITIONS = [
    ("query userId", {}, {"userId": 1}),
    ("query id", {}, {"id": 1}),
    ("query user_id", {}, {"user_id": 1}),
    ("header X-User-Id", {"X-User-Id": "1"}, {}),
]


@pytest.mark.parametrize("case_name,extra_headers,params", PROBE_POSITIONS,
                         ids=[c[0] for c in PROBE_POSITIONS])
def test_cannot_read_others_via_request(api, auth_headers, restore_profile,
                                        case_name, extra_headers, params):
    """把"别人的 id"塞进请求的不同位置 → 返回的必须还是**自己的**资料。

    这是通用越权试探清单：**query / 路径 / header / token 自身**，本例覆盖前三处。
    这个接口的身份只认 token，所以塞哪儿都没用 —— 断言的正是这一点。

    ⚠️ 踩坑：伪造的请求头要**叠加**在鉴权头之上（`{**auth_headers, **extra_headers}`）。
       第一版写成 `api.get(..., headers=auth_headers, **kwargs)`，
       而 kwargs 里也含 headers → `TypeError: got multiple values for keyword argument 'headers'`。
       Python 的关键字参数重名不会自动合并，**只会报错**，得自己 merge 字典。
    """
    mine = restore_profile
    headers = {**auth_headers, **extra_headers}      # 鉴权头 + 伪造头

    after = api.assert_ok(api.get("/user/profile", headers=headers, params=params))["data"]

    assert after["userId"] == mine["userId"], "塞了别人的 id 竟然读到别人的资料！"
    assert after["email"] == TEST_USER["email"]


def test_no_id_based_profile_route(api, auth_headers):
    """/user/profile/{id} 这类"按 id 查资料"的路由**不存在**（404）。

    也就是说：这个接口从设计上就没开"查别人"的口子 ——
    不是它检查得严，而是压根没有那个入口。
    真要练 IDOR，得去带 {id} 的接口（/record/detail/{recordId} 等）。
    """
    assert api.get("/user/profile/1", headers=auth_headers).status_code == 404
    assert api.get("/user/1/profile", headers=auth_headers).status_code == 404


def test_admin_api_forbidden_for_normal_user(api, auth_headers):
    """普通用户打管理员接口 → 403。

    管理员接口才是"一次拿到所有人资料"的最大口子，所以值得守。
    ⚠️ 403 走的是 Spring 默认错误体（{timestamp,status,error,path}），
       **不是**统一信封 —— 所以这里只能断状态码，别去读 code/message。
    """
    for path in ("/user/admin/list", "/admin/overview"):
        resp = api.get(path, headers=auth_headers)
        assert resp.status_code == 403, f"{path} 没拦住普通用户，实际 {resp.status_code}"


def test_profile_isolated_between_users(api, auth_headers, other_user):
    """横向隔离：两个身份各拿各的 token，谁也看不到谁。

    ⚠️ 只断言"userId 不同"是**弱证据** —— 那只证明"两个 token 对应两个账号"。
       真正的隔离证明是**交叉比对**：我的响应里必须出现我的邮箱、绝不能出现你的。
    """
    me = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]
    other = api.assert_ok(api.get("/user/profile", headers=other_user["headers"]))["data"]

    assert me["userId"] != other["userId"]
    assert me["email"] == TEST_USER["email"], "A 拿到的不该是别人的邮箱"
    assert other["email"] == other_user["email"], "B 拿到的该是自己注册时的邮箱"
    # 交叉污染检查
    assert other_user["email"] not in json.dumps(me, ensure_ascii=False)
    assert TEST_USER["email"] not in json.dumps(other, ensure_ascii=False)


# ============================================================
# 组 6：跨层对质 —— 接口说的 vs 库里真存的
# ============================================================


def test_profile_matches_database(api, auth_headers):
    """接口返回的字段 vs 数据库里的真实值，必须对得上。

    为什么要跨层？"接口说改了"和"库里真的改了"是两件事 ——
    只信接口返回，等于只信被告人的口供。

    （用 common/db.py 的 query；它的连接是 autocommit 的，
      不会像手动建的连接那样读到旧事务快照。）
    """
    data = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]

    row = query(
        "select username, email, phone, role, status from `user` where email = %s",
        (TEST_USER["email"],), one=True,
    )
    assert row is not None, "测试账号在库里查不到，先检查测试数据"
    assert row["username"] == data["username"]
    assert row["email"] == data["email"]
    assert row["phone"] == data["phone"]
    assert row["role"] == data["role"]


# ============================================================
# 组 7：缺陷固化（xfail）
# ============================================================


@pytest.mark.xfail(reason="已知缺陷 #9：PUT /user/profile 后 updateTime 不刷新"
                          "（与 /health/info 的缺陷 #6 同源，待后端修复）")
def test_update_time_refreshed_on_profile_write(api, auth_headers, restore_profile):
    """写完之后，updateTime 应该刷新成"刚才那一刻"。

    ⚠️ 两件事：
      1) updateTime 精度只到**秒**，所以要 sleep 跨过秒边界再写，
         否则两次写入落在同一秒，断言会**假失败**（health 那边踩过这个坑）；
      2) 判定写成"离现在有多近"，而不是"变了没有" —— 后者在秒级精度下不可靠。

    当前状态：缺陷 #9。实测 updateTime 一直停在 2026-03-15（注册时间）不动，
    所以这条会 XFAIL。后端修好后它会自己变成 XPASS —— 那时把 xfail 标记摘掉即可。
    """
    time.sleep(1.2)                                   # 跨过秒边界

    api.assert_ok(api.put("/user/profile", headers=auth_headers,
                          json={"phone": "17800008888"}))

    after = api.assert_ok(api.get("/user/profile", headers=auth_headers))["data"]
    written_at = datetime.strptime(after["updateTime"], TS_FMT)
    gap = abs((datetime.now() - written_at).total_seconds())

    assert gap <= 60, (
        f"updateTime 没刷新：{after['updateTime']}，距离现在 {gap:.0f} 秒"
        f"（createTime 是 {after['createTime']}）"
    )
