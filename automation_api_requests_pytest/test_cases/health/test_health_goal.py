# test_cases/health/test_health_goal.py
# 【任务：饮食目标接口 · upsert 写库 + 跨字段日期校验 + 非统一信封缺陷】
#
# 跟 test_health_info.py 是姊妹篇，结构一样。多了一个新东西：
#   **跨字段校验**（endDate 不能早于 startDate）—— 单字段注解表达不了，
#   后端用 @AssertTrue 挂在 getter 上做类级校验，报错同样走统一信封。

import pytest

from common import db
from common.data_loader import load_cases

# 数据来源：data/health_goal_cases.yaml（5 类校验失败场景）
CASES = load_cases("health_goal_cases.yaml")

# 一份合法的目标，供成功用例复用。
VALID_GOAL = {
    "goalType": "lose_weight", "targetWeight": 65.0, "targetCalories": 1800.0,
    "proteinRatio": 30.0, "carbsRatio": 45.0, "fatRatio": 25.0,
    "proteinTarget": 135.0, "carbsTarget": 200.0, "fatTarget": 50.0,
    "waterTarget": 2000, "status": 1,
    "startDate": "2026-10-01", "endDate": "2026-12-31",
    "reminderEnabled": 1, "reminderTime": "08:00:00",
}


def case_name(case):
    """用数据里的 name 字段当中文用例名。"""
    return case["name"]


# ==================== GET：读取目标 ====================

def test_get_goal_without_record(api, health_user):
    """新账号还没设目标 → 200，data 是 null（goal 没有 analysis）。"""
    resp = api.health.get_goal(headers=health_user["headers"])
    body = api.assert_ok(resp, "获取饮食目标应成功")

    assert body["message"] == "获取饮食目标成功"
    assert body["data"] is None, "没设目标时 data 应为 null"


def test_get_goal_without_token(api):
    """无 token → 401 + 空体。"""
    resp = api.health.get_goal()
    assert resp.status_code == 401
    assert resp.text == ""


def test_get_goal_with_bad_token(api):
    """伪造 token → 401 + 空体。"""
    resp = api.health.get_goal(headers={"Authorization": "Bearer abc.def.ghi"})
    assert resp.status_code == 401
    assert resp.text == ""


# ==================== POST：新增 / 更新（upsert）====================

def test_save_goal_create(api, health_user):
    """首次 POST → 建目标，200，字段落库正确。"""
    resp = api.health.save_goal(VALID_GOAL, headers=health_user["headers"])
    body = api.assert_ok(resp, "设置饮食目标应成功")

    assert body["message"] == "饮食目标设置成功"

    data = body["data"]
    assert data["userId"] == health_user["userId"]
    assert data["goalType"] == "lose_weight"
    assert data["targetCalories"] == 1800.0
    assert data["startDate"] == "2026-10-01"
    assert data["endDate"] == "2026-12-31"


def test_save_goal_is_upsert(api, health_user):
    """再 POST → 更新同一条（id 不变），库里只留一条。"""
    b1 = api.assert_ok(api.health.save_goal(VALID_GOAL, headers=health_user["headers"]))
    id1 = b1["data"]["id"]

    b2 = api.assert_ok(api.health.save_goal(
        dict(VALID_GOAL, targetCalories=1900.0), headers=health_user["headers"]))
    id2 = b2["data"]["id"]

    assert id1 == id2, f"upsert 应更新同一条（id 不变），实际 {id1} → {id2}"
    assert b2["data"]["targetCalories"] == 1900.0

    n = db.query("SELECT COUNT(*) AS n FROM diet_goal WHERE user_id = %s",
                 (health_user["userId"],), one=True)["n"]
    assert n == 1, f"upsert 后该用户只应有 1 条目标，实际 {n}"


def test_save_goal_same_day_allowed(api, health_user):
    """endDate == startDate **允许**（当天的单日目标）—— 边界不能误判成倒挂。

    跨字段校验 `!endDate.isBefore(startDate)` 的合理解读是"允许相等"，
    这条用例就是守住这个边界：不是所有"看起来可疑"的日期都该拦。
    """
    goal = {"goalType": "lose_weight", "targetCalories": 1800.0,
            "startDate": "2026-10-10", "endDate": "2026-10-10"}
    resp = api.health.save_goal(goal, headers=health_user["headers"])
    body = api.assert_ok(resp, "同一天的起止日期应被允许")

    assert body["data"]["startDate"] == "2026-10-10"
    assert body["data"]["endDate"] == "2026-10-10"


def test_save_goal_end_date_optional(api, health_user):
    """endDate 可以不传（目标长期有效）→ 200，库里 endDate 为 null。"""
    goal = {"goalType": "lose_weight", "targetCalories": 1800.0, "startDate": "2026-10-01"}
    body = api.assert_ok(api.health.save_goal(goal, headers=health_user["headers"]))

    assert body["data"]["endDate"] is None
    row = db.query("SELECT end_date FROM diet_goal WHERE user_id = %s",
                   (health_user["userId"],), one=True)
    assert row["end_date"] is None


# ==================== POST：校验失败（参数化）====================

@pytest.mark.parametrize("case", CASES, ids=case_name)
def test_save_goal_fail(api, health_user, case):
    """校验失败：5 类非法输入，期望值全部来自数据文件。"""
    resp = api.health.save_goal(case["body"], headers=health_user["headers"])

    api.assert_error(resp, case["want_code"], case["want_msg"], http=case["want_http"])


def test_save_goal_without_token(api):
    """POST 必须带 token → 401 + 空体。"""
    resp = api.health.save_goal(VALID_GOAL)
    assert resp.status_code == 401
    assert resp.text == ""


# ==================== 已知缺陷（钉住，不修）====================

def test_save_goal_bad_date_format_response_not_unified(api, health_user):
    """已知缺陷 #7：非法日期格式 → 400，但**响应体不是统一信封**。

    传 `startDate: "2026/13/45"` 时，请求根本到不了业务代码 ——
    Spring 在反序列化 JSON 成 LocalDate 时就失败了，直接吐它自带的错误体
    `{timestamp, status, error, path}`，**没有 code / message**。

    这跟"统一响应结构"的约定冲突：客户端没法用同一套逻辑解析所有错误。
    这条用例不用 xfail —— 它断言的**就是"现在这个不一致的样子"**，
    是把它固化成可回归的契约。等后端统一了错误体，这条会红，
    提醒我们把它改成正常断言。
    """
    resp = api.health.save_goal(
        {"goalType": "lose_weight", "targetCalories": 1800.0, "startDate": "2026/13/45"},
        headers=health_user["headers"])

    assert resp.status_code == 400, f"非法日期格式应 400，实际 {resp.status_code}"

    body = resp.json()
    assert "code" not in body, f"统一信封本该有 code，实际 {sorted(body)}"
    assert "message" not in body, f"统一信封本该有 message，实际 {sorted(body)}"
    assert set(body) == {"timestamp", "status", "error", "path"}, \
        f"实际错误体字段：{sorted(body)}"
