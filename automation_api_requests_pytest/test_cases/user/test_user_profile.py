# test_cases/user/test_user_profile.py
# 【任务：用户资料接口 · 鉴权 + PUT 写库副作用】
#
# 这个文件有两个"第一次"，都值得记住：
#   ① 第一次测**要 token** 的接口 → 用 conftest 的 auth_headers 夹具；
#   ② 第一次测 **PUT**（改数据）→ 跟注册一样有副作用，
#      所以用一个"用完就扔"的临时靶子账号，不污染测试账号张三。
#
# 期望值全部来自实测（见数据文件注释），不靠猜。

import time
import uuid

import pytest

from common import db
from common.data_loader import load_cases
from config.config import TEST_USER

# 本模块会直接查库对账/清理；数据库不可用时由根 conftest 跳过。
pytestmark = pytest.mark.requires_db

# 数据来源：data/user_profile_cases.yaml（6 类失败场景）
CASES = load_cases("user_profile_cases.yaml")


def case_name(case):
    """用数据里的 name 字段当中文用例名。"""
    return case["name"]


# ==================== 夹具 ====================

@pytest.fixture
def temp_user(api):
    """造一个临时靶子账号，供 PUT 用例改；用例跑完从库里删掉。

    为什么不用张三？因为 PUT 是**写操作**，会把账号资料真改掉。
    造一个"用完就扔"的账号当靶子：既真实（它真的是个登录用户，
    有自己的 userId 和 token），又不会把别人的档案弄脏。

    yield 之前 = 造数据；yield 之后 = 清理。
    **不管用例成功还是失败，清理都会执行**（所以断言挂了也留不下垃圾账号）。
    """
    uniq = "pf_" + uuid.uuid4().hex[:10]
    data = {"username": uniq, "password": "123456", "email": uniq + "@example.com"}
    body = api.assert_ok(api.auth.register(data), "注册靶子账号应成功")

    user = {
        "userId": body["data"]["userId"],
        "email": data["email"],
        "username": uniq,
        "headers": {"Authorization": "Bearer " + body["data"]["token"]},
    }
    yield user

    # ---- 清理：用例跑完才轮到这儿 ----
    affected = db.execute("DELETE FROM `user` WHERE email = %s", (user["email"],))
    print(f"\n[清理] 删除靶子账号 {user['email']}，affected={affected}")


def _free_phone():
    """找一个库里还没被占用的手机号。

    为什么要动态找？实测发现所谓的"经典测试号"13800138000 **真的被占用了**
    （库里 id=100182 正在用）。写死任何号码都可能某天撞车 → 用例假红。
    所以现查现用：随机生成，查到库里没有才拿来用。
    """
    import random
    for _ in range(20):
        phone = "135" + "".join(random.choice("0123456789") for _ in range(8))
        exists = db.query("SELECT COUNT(*) AS n FROM `user` WHERE phone = %s",
                          (phone,), one=True)["n"]
        if exists == 0:
            return phone
    raise RuntimeError("连续 20 次都没找到空闲手机号（库里的号有这么密吗？）")


# ==================== GET：读取资料 ====================

def test_get_profile_success(api, auth_headers):
    """带 token 读资料 → 200，返回固定的 9 个字段，且就是登录账号本人。"""
    resp = api.user.get_profile(headers=auth_headers)
    body = api.assert_ok(resp, "获取个人资料应成功")

    assert body["message"] == "获取个人资料成功"

    data = body["data"]
    assert set(data) == {
        "userId", "username", "email", "phone", "avatar",
        "status", "createTime", "updateTime", "role",
    }, f"返回字段与预期不符：{sorted(data)}"

    # 读到的就是测试账号本人（不是别人）—— 证明 userId 是从 token 解出来的
    assert data["email"] == TEST_USER["email"]


def test_get_profile_without_token(api):
    """/user/profile 必须带 token：不带 → 401，且**响应体是空的**。

    注意断言里没有 resp.json() —— 401 是空体，读 json 会直接抛异常。
    这类"只断状态码"的写法，本身就是一条契约：**401 不给 body**。
    """
    resp = api.user.get_profile()
    assert resp.status_code == 401, f"无 token 应 401，实际 {resp.status_code}"
    assert resp.text == "", f"401 响应体应为空，实际 {resp.text!r}"


def test_get_profile_with_bad_token(api):
    """伪造的 token → 同样 401 + 空体（后端验签不过）。"""
    resp = api.user.get_profile(headers={"Authorization": "Bearer abc.def.ghi"})
    assert resp.status_code == 401, f"伪 token 应 401，实际 {resp.status_code}"
    assert resp.text == ""


# ==================== PUT：各类失败（在临时靶子上跑）====================

@pytest.mark.parametrize("case", CASES, ids=case_name)
def test_update_profile_fail(api, temp_user, case):
    """PUT 失败：6 类非法输入，期望值全部来自数据文件。

    在**靶子账号**上跑（不是张三）—— 尤其"用户名已存在/手机号已被使用"
    这两条：后端判重会放过"自己"，只有在别的账号上提交才触发 400。
    """
    resp = api.user.update_profile(case["body"], headers=temp_user["headers"])

    assert resp.status_code == case["want_http"], \
        f"期望 HTTP {case['want_http']}，实际 {resp.status_code}"

    body = resp.json()
    assert body["code"] == case["want_code"], \
        f"期望 code={case['want_code']}，实际 {body.get('code')}"
    assert body["message"] == case["want_msg"], \
        f"期望 message={case['want_msg']}，实际 {body.get('message')}"


# ==================== PUT：各类成功（会写库，在临时靶子上跑）====================

def test_update_username_success(api, temp_user):
    """改用户名成功：200，库里真的变了，且**没提交的字段不受影响**（局部更新）。"""
    new_name = "renamed_" + uuid.uuid4().hex[:6]

    resp = api.user.update_profile({"username": new_name}, headers=temp_user["headers"])
    body = api.assert_ok(resp, "改用户名应成功")

    assert body["message"] == "个人资料更新成功"
    assert body["data"]["username"] == new_name
    assert body["data"]["email"] == temp_user["email"], "email 不在可改字段里，不该变"

    # 不只信响应，去库里核对（接口 + DB 双重验证）
    row = db.query("SELECT username, email, phone, avatar FROM `user` WHERE email = %s",
                   (temp_user["email"],), one=True)
    assert row["username"] == new_name
    assert row["phone"] is None, "没提交 phone，就应保持原样（这里是 null）"
    assert row["avatar"] is None, "没提交 avatar，就应保持原样"


def test_update_phone_success(api, temp_user):
    """改手机号成功：用一个"库里确实没人用"的号，200 且库里变了。"""
    phone = _free_phone()

    resp = api.user.update_profile({"phone": phone}, headers=temp_user["headers"])
    body = api.assert_ok(resp, "改手机号应成功")

    assert body["data"]["phone"] == phone
    row = db.query("SELECT phone FROM `user` WHERE email = %s",
                   (temp_user["email"],), one=True)
    assert row["phone"] == phone


def test_update_avatar_then_clear(api, temp_user):
    """头像可以先设、再清空：传空串时库里存 NULL（不是空字符串）。

    这是"清空字段"这条完整链路的验收：DTO 放行空串 → Service 想清空 →
    实体上的 updateStrategy=IGNORED 让 NULL 真的写进 SQL。
    少一环，这里就会失败（比如库里残留空串、或老值删不掉）。
    """
    # 1) 先设上
    body = api.assert_ok(
        api.user.update_profile({"avatar": "http://x/y.png"}, headers=temp_user["headers"]),
        "设置头像应成功")
    assert body["data"]["avatar"] == "http://x/y.png"

    # 2) 再清空（传空串）
    body = api.assert_ok(
        api.user.update_profile({"avatar": ""}, headers=temp_user["headers"]),
        "清空头像应成功")
    assert body["data"]["avatar"] is None, "清空后响应里 avatar 应是 null"

    row = db.query("SELECT avatar FROM `user` WHERE email = %s",
                   (temp_user["email"],), one=True)
    assert row["avatar"] is None, "清空后库里应是 NULL"


def test_readonly_fields_ignored(api, temp_user):
    """email / role / status / userId 传了也没用：仍返回 200，但一个都不改。

    这是安全相关的一条：如果这些字段真能被 PUT 改掉，就能越权把自己改成 admin。
    实测是"静默忽略"（200 但值不变），所以这里顺便把结论钉住。
    """
    resp = api.user.update_profile(
        {"email": "hacker@evil.com", "role": "admin", "status": 0, "userId": 999},
        headers=temp_user["headers"],
    )
    body = api.assert_ok(resp, "只读字段应被忽略但仍返回 200")

    data = body["data"]
    assert data["email"] == temp_user["email"], "email 不该被改"
    assert data["role"] == "user", "role 不该被改成 admin"
    assert data["status"] == 1, "status 不该被改"
    assert data["userId"] == temp_user["userId"], "userId 不该被改"


def test_empty_body_no_change(api, temp_user):
    """空体 {} → 200，但什么都不改（局部更新：没说改的都不动）。"""
    resp = api.user.update_profile({}, headers=temp_user["headers"])
    body = api.assert_ok(resp, "空体应成功（不改任何字段）")

    assert body["data"]["username"] == temp_user["username"]
    assert body["data"]["email"] == temp_user["email"]


# ==================== 已知缺陷（先 xfail 钉住）====================

@pytest.mark.xfail(reason="已知缺陷：PUT /user/profile 不刷新 update_time", strict=True)
def test_update_profile_refreshes_update_time(api, temp_user):
    """PUT 之后 update_time 应该刷新成新的时间戳 —— 但实测**不会变**。

    这是缺陷：账号资料改了，更新时间却还停在注册那一刻。
    根因大概是 Service 直接 updateById(user)，把 DB 的
    `ON UPDATE CURRENT_TIMESTAMP` 盖掉了（实体带旧值进 SQL）。

    先 xfail 钉住它：
      · 现在跑 → XFAIL（预期内失败，不算红）；
      · 后端哪天修了 → XPASS，strict=True 会把它变成失败，提醒我们摘掉这个标记。
    """
    before = db.query("SELECT update_time FROM `user` WHERE email = %s",
                      (temp_user["email"],), one=True)["update_time"]

    time.sleep(1.2)   # 跨过秒边界，保证"时间真的往前走了一秒"

    api.user.update_profile({"username": "renamed_" + uuid.uuid4().hex[:6]},
                            headers=temp_user["headers"])

    after = db.query("SELECT update_time FROM `user` WHERE email = %s",
                     (temp_user["email"],), one=True)["update_time"]
    assert after > before, f"update_time 应刷新，实际没变（{before}）"
