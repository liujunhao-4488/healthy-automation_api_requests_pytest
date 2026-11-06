# test_cases/user/test_diet_preference.py
# 【A 档 · 单例写入 + 局部更新语义】饮食偏好
#
# ============ 为什么这个接口值得单独一批用例 ============
# 覆盖矩阵把它列在 A 档、开工顺序第三位，理由是「有写，且直接影响推荐结果」。
# 具体一点：
#   · 整个系统里**只有这两个接口**能看/改饮食偏好（前端"个人中心"是唯一入口）；
#   · 它是 `/recommend/*` 的输入项 —— 偏好错了，推荐就错，但不报任何错；
#   · 一个用户只有**一行**数据，PUT 是 upsert + 局部更新，
#     没写的字段该不该保留，是这类接口最经典的坑。
#
# ============ 这个接口有一处反直觉的行为，先说清楚 ============
# **PUT 的响应体不是"更新后的状态"，而是"请求内容 + 旧记录的 id"拼出来的回显。**
#
#   库里已有 allergies="海鲜"
#   PUT {"dietType":"低碳水"}
#   → 响应 {"dietType":"低碳水", "allergies":null, ...}   ← 看着像被清空了
#   → 紧接着 GET {"dietType":"低碳水", "allergies":"海鲜"} ← 实际没被清空
#
# 所以本文件里**所有"改完对不对"的断言都走 GET 或查库，绝不用 PUT 的返回值**。
# 这不是洁癖：前端如果拿 PUT 的响应直接渲染，用户会看到"过敏原被清空了"，
# 而实际上还在 —— 这个不一致已作为缺陷 #16 记录，并有一条 xfail 钉住。

import pytest

from common import db

pytestmark = pytest.mark.requires_db

# 一套完整的偏好，用来测"全量写入后再读回来一不一致"
FULL_PREFERENCE = {
    "dietType": "素食",
    "allergies": "花生",
    "dislikes": "香菜",
    "favorites": "豆腐",
    "mealFrequency": 4,
    "snackPreference": 0,
}


def _read(api, who):
    """读某人的偏好（真实存储值，不是回显）。"""
    body = api.assert_ok(
        api.user.get_diet_preference(headers=who["headers"]),
        f"用户 {who['userId']} 读取饮食偏好应成功",
    )
    return body["data"]


def _read_db(user_id):
    """直接查库，确认"接口说的"和"库里存的"是一回事。"""
    return db.query(
        "SELECT diet_type, allergies, dislikes, favorites, meal_frequency, snack_preference "
        "FROM user_diet_preference WHERE user_id = %s", (user_id,), one=True,
    )


# ==================== 一、新用户的默认状态 ====================

def test_new_user_has_no_preference_row_but_gets_defaults(api, preference_pair):
    """新注册用户没有偏好数据，接口给"空壳 + 默认值"，不报 404。

    ══ 为什么这个细节要专门测 ══
    它决定了前端怎么判断"用户填过没有"：
      · 看 id 是否为 null → 对（id 为 null 说明库里还没这行）
      · 看 dietType 是否为 null → 也对，但不可靠（用户可能真的只选了餐次）
      · 看整个 data 是否为 null → **错**，接口永远返回对象，不是 null
    最后那种写法会让"未填写"的引导浮层永远不出现，新用户打开就是一片空白。

    ══ 实测的默认值 ══
        mealFrequency = 3、snackPreference = 1（一天三餐、吃零食）
    这两个值来自 DTO 默认值，不是库里读出来的（因为库里根本没有这行）。
    """
    owner = preference_pair["owner"]

    data = _read(api, owner)

    assert data["id"] is None, (
        f"新用户库里还没有偏好行，id 应该是 null，实际 {data['id']!r}。\n"
        f"→ 如果这里变成有值，说明 GET 顺手插了一行 —— 那「有没有填过」就判断不了了。"
    )
    assert data["userId"] == owner["userId"], "返回的 userId 必须是当前登录用户（只认 token）"
    assert data["mealFrequency"] == 3, f"默认餐次应该是 3，实际 {data['mealFrequency']}"
    assert data["snackPreference"] == 1, f"默认零食应该是 1，实际 {data['snackPreference']}"

    assert _read_db(owner["userId"]) is None, (
        "GET 不应该产生写入（库里不该有这行）—— 否则每个用户看一眼偏好就多一行空数据"
    )


# ==================== 二、全量写入 → 读回一致 ====================

def test_full_update_then_read_matches(api, preference_pair):
    """整套偏好写进去，读回来必须逐个字段都对得上。

    ══ 为什么六个字段全断 ══
    diet_type / allergies / dislikes / favorites 都是 varchar/text，
    meal_frequency 是 int，snack_preference 是 tinyint(0/1)。
    后端如果漏了一个字段的 set，接口照样 200，只有那个字段永远是 null ——
    用户会觉得"我明明填了不喜欢香菜，怎么还推荐香菜"。
    """
    owner = preference_pair["owner"]

    api.assert_ok(
        api.user.update_diet_preference(FULL_PREFERENCE, headers=owner["headers"]),
        "更新饮食偏好应成功",
    )

    data = _read(api, owner)
    assert data["dietType"] == "素食"
    assert data["allergies"] == "花生"
    assert data["dislikes"] == "香菜"
    assert data["favorites"] == "豆腐"
    assert data["mealFrequency"] == 4
    assert data["snackPreference"] == 0

    row = _read_db(owner["userId"])
    assert row is not None, "接口返回更新成功，但库里查不到这一行"
    assert row["diet_type"] == "素食" and row["allergies"] == "花生", (
        f"库里存的和接口返回的不一致：{row}"
    )


def test_second_update_overwrites_not_inserts(api, preference_pair):
    """第二次 PUT 是**更新**那一行，不是再插一行（一个用户只能有一行）。

    ══ 为什么这条重要 ══
    表上有 user_id 索引但**没有唯一键**（看 schema）。如果后端写成了纯 INSERT，
    库里会悄悄累积多行，而 GET 只取其中一行 —— 用户看到的偏好会随机地
    "变回上一次的设置"，这种 bug 极难复现，因为取决于查询返回哪一行。
    """
    owner = preference_pair["owner"]

    api.assert_ok(api.user.update_diet_preference(
        {"dietType": "素食", "mealFrequency": 3}, headers=owner["headers"]), "第一次更新应成功")
    api.assert_ok(api.user.update_diet_preference(
        {"dietType": "低碳水", "mealFrequency": 5}, headers=owner["headers"]), "第二次更新应成功")

    n = db.query("SELECT COUNT(*) AS n FROM user_diet_preference WHERE user_id = %s",
                 (owner["userId"],), one=True)["n"]
    assert n == 1, f"更新两次之后库里有 {n} 行 —— UPSERT 写成了 INSERT"


# ==================== 三、局部更新语义（最核心的一组）====================

def test_partial_update_keeps_untouched_fields(api, preference_pair):
    """只传一个字段，其他字段**必须原样保留**。

    ══ 依据（为什么是"必须保留"而不是"清空"）══
    这是同一个项目里已经确立的约定：`PUT /user/profile` 实测是局部更新
    （"body 只传 phone → username/email/avatar 全部保留"，
    写进了覆盖矩阵第六节「其余可测点」）。
    同一套 API 里两个 update 接口的语义应当一致 —— 否则前端每改一个开关
    都得把整份表单回传，漏一个就清一个。

    ══ 为什么断言要读 GET 而不是读 PUT 的响应 ══
    PUT 响应是回显（见文件头），读它只会看到"全 null"，误判成"被清空了"。
    """
    owner = preference_pair["owner"]

    api.assert_ok(api.user.update_diet_preference(FULL_PREFERENCE, headers=owner["headers"]),
                  "先写入整套偏好")
    api.assert_ok(api.user.update_diet_preference({"dietType": "低碳水"},
                                                  headers=owner["headers"]),
                  "只改 dietType 应成功")

    data = _read(api, owner)
    assert data["dietType"] == "低碳水", "改的那个字段没生效"
    assert data["allergies"] == "花生", (
        f"只改了 dietType，allergies 却被清成了 {data['allergies']!r} —— 这是全量覆盖，不是局部更新"
    )
    assert data["dislikes"] == "香菜", f"dislikes 被清成了 {data['dislikes']!r}"
    assert data["favorites"] == "豆腐", f"favorites 被清成了 {data['favorites']!r}"
    assert data["mealFrequency"] == 4, f"mealFrequency 被重置成 {data['mealFrequency']}"


def test_empty_update_is_noop(api, preference_pair):
    """空 body {} → 200「更新成功」，但一个字段都不该变。

    ⚠️ **观察点，不是缺陷**：`PUT /user/profile` 的实测行为完全一样
       （空 body 也返回 200「个人资料更新成功」），属这套 API 的一致风格。
       这里记录的是"它不会把偏好清空"—— 如果哪天变成清空，
       用户点一次"保存"没填东西，过敏信息就静默没了。
    """
    owner = preference_pair["owner"]

    api.assert_ok(api.user.update_diet_preference(FULL_PREFERENCE, headers=owner["headers"]),
                  "先写入整套偏好")
    before = _read(api, owner)

    api.assert_ok(api.user.update_diet_preference({}, headers=owner["headers"]),
                  "空 body 更新当前返回成功")

    after = _read(api, owner)
    for key in ("dietType", "allergies", "dislikes", "favorites", "mealFrequency", "snackPreference"):
        assert after[key] == before[key], (
            f"空 body 更新把 {key} 从 {before[key]!r} 改成了 {after[key]!r} —— 空请求不该产生副作用"
        )


# ==================== 四、越权 ====================

def test_cannot_update_others_preference_via_body_user_id(api, preference_pair):
    """在 body 里塞别人的 userId → 被忽略，改的仍是自己。

    ══ 这是"提权"最基本的形态 ══
    接口本来没有 id 入参（只认 token），但如果 DTO 里有 userId 字段
    且后端直接拿它写库，攻击者传谁的 id 就能改谁的偏好。
    实测被忽略 —— 这条用例把它钉住。
    """
    owner, other = preference_pair["owner"], preference_pair["other"]

    api.assert_ok(api.user.update_diet_preference(
        {"dietType": "偷渡", "userId": other["userId"]}, headers=owner["headers"]),
        "带别人 userId 的更新请求本身会成功（只是不该改到别人）")

    other_data = _read(api, other)
    assert other_data["dietType"] is None, (
        f"A 在 body 里塞了 B 的 userId，B 的 dietType 变成了 {other_data['dietType']!r} —— "
        f"后端直接拿 body 里的 userId 写库了，越权成功。"
    )

    own_data = _read(api, owner)
    assert own_data["dietType"] == "偷渡", "后端忽略了 body 里的 userId，但也没改到 A 自己"


def test_get_requires_token(api):
    """读取偏好不带 token → 401。"""
    resp = api.user.get_diet_preference(headers=None)
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)


def test_update_requires_token(api, preference_pair):
    """更新偏好不带 token → 401，且数据没变。"""
    owner = preference_pair["owner"]
    api.assert_ok(api.user.update_diet_preference(FULL_PREFERENCE, headers=owner["headers"]),
                  "先写入一套基线偏好")
    before = _read(api, owner)

    resp = api.user.update_diet_preference({"dietType": "未登录改的"}, headers=None)
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)

    after = _read(api, owner)
    assert after["dietType"] == before["dietType"] == "素食", (
        f"未登录的更新被 401 拒绝了，但数据变了：{before['dietType']!r} → {after['dietType']!r}"
    )


# ==================== 五、已知缺陷（xfail 钉住）====================

@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #16：PUT /user/diet-preference 的响应体是请求回显，不是更新后的真实状态"
           "（PUT 只带 dietType 时，响应里 allergies=null，但库里仍是原值）",
)
def test_bug_update_response_is_request_echo_not_real_state(api, preference_pair):
    """PUT 的响应体必须能当"更新后的状态"用 —— 现在不能。

    ══ 依据（为什么这是缺陷）══
    同一个项目里，`PUT /user/profile` 实测返回的是**真实最新数据**
    （"PUT 改成自己的 username → 200，GET 与 PUT 响应一致"）。
    同一套 API 的两个 update 接口，一个返回真值、一个返回回显，这是实现不一致。

    ══ 真实影响 ══
    前端保存偏好后通常直接拿响应当新状态渲染（省一次 GET）。
    这里会渲染出"过敏原：无"—— 用户以为自己把过敏信息清掉了，
    或者反过来，以为设置没保存上、反复点保存。
    对一个"过敏提示"功能来说，显示错误的信息比不显示更危险。
    """
    owner = preference_pair["owner"]

    api.assert_ok(api.user.update_diet_preference(FULL_PREFERENCE, headers=owner["headers"]),
                  "先写入 allergies=花生")
    body = api.assert_ok(api.user.update_diet_preference({"dietType": "低碳水"},
                                                         headers=owner["headers"]),
                         "只改 dietType 应成功")

    echoed = body["data"]["allergies"]
    real = _read(api, owner)["allergies"]

    assert echoed == real == "花生", (
        f"PUT 响应里 allergies={echoed!r}，但真实存储是 {real!r}。\n"
        f"→ 响应体是拿请求 DTO 拼的回显（没写的字段填 null），不是查库后的真实值。\n"
        f"→ 前端若直接用响应渲染，用户会看到过敏原被清空。"
    )


@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #19：mealFrequency 无范围校验，0 和 99 都能入库",
)
def test_bug_meal_frequency_out_of_range_accepted(api, preference_pair):
    """每餐次数应该是 1~6，传 0 或 99 必须被拒 —— 实测都返回 200 并入库。

    ══ 依据 ══
    库表定义 `meal_frequency int DEFAULT '3' COMMENT '每日餐次'`，
    语义上"每日餐次"不可能是 0 或 99。
    更硬的依据是**团队先例**：缺陷 #4（age=-1、weight=-5 都能入库）
    的处置是"给 DTO 补 @Min/@Max"，说明标准是「数值字段要有范围校验」。
    同一系统里另一个 DTO 没做，属实现不一致。

    ══ 影响 ══
    餐次是热量分配算法的分母之一。0 会导致除零或"每餐 0 大卡"，
    99 会让单餐热量算成个位数 —— 都不报错，只是推荐变得莫名其妙。
    """
    owner = preference_pair["owner"]

    for bad in (0, 99):
        resp = api.user.update_diet_preference({"mealFrequency": bad},
                                               headers=owner["headers"])
        assert resp.status_code == 400, (
            f"mealFrequency={bad} 被接受了（HTTP {resp.status_code}），"
            f"但每日餐次的合理范围是 1~6"
        )
