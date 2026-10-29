# test_cases/health/test_health_info.py
# 【任务：健康档案接口 · upsert 写库 + 数值校验 + 顶层 analysis】
#
# 这个文件有三处"第一次"，都值得记住：
#   ① 第一次测 **upsert**（POST 既可能是"新建"也可能是"更新"）；
#   ② 第一次遇到 **analysis 挂在信封顶层**（body["analysis"]，不是 body["data"]["analysis"]）；
#   ③ 第一次发现**清库有外键顺序**（history 表有外键指向 user，得先删它）。
#
# 期望值全部来自实测（2026-10-10 真打后端），不靠猜。

import pytest

from common import db
from common.data_loader import load_cases

# 数据来源：data/health_健康档案_cases.yaml（13 类校验失败场景）
CASES = load_cases("health_健康档案_cases.yaml")

# 一份合法的基础档案，供成功用例复用。
VALID_INFO = {"age": 30, "gender": "male", "height": 175.0, "weight": 70.0}


def case_name(case):
    """用数据里的 name 字段当中文用例名。"""
    return case["name"]


# ==================== GET：读取档案 ====================

def test_get_info_without_record(api, health_user):
    """新账号还没建档 → 200，data 是 null，但信封顶层**仍然有 analysis**。

    注意最后一行：analysis 在**顶层**（body["analysis"]），不在 data 里。
    这是后端 controller 直接 response.put("analysis", ...) 决定的，
    写断言时千万别写成 body["data"]["analysis"]（那是 None，会炸）。
    """
    resp = api.health.get_info(headers=health_user["headers"])
    body = api.assert_ok(resp, "获取健康信息应成功")

    assert body["message"] == "获取健康信息成功"
    assert body["data"] is None, "没建档时 data 应为 null"
    assert body["analysis"]["overallLevel"] == "待完善", "没档案时分析等级应是'待完善'"


def test_get_info_without_token(api):
    """必须带 token：不带 → 401，且**响应体为空**（只断状态码，不读 body）。"""
    resp = api.health.get_info()
    assert resp.status_code == 401, f"无 token 应 401，实际 {resp.status_code}"
    assert resp.text == "", f"401 响应体应为空，实际 {resp.text!r}"


def test_get_info_with_bad_token(api):
    """伪造 token → 同样 401 + 空体（后端验签不过）。"""
    resp = api.health.get_info(headers={"Authorization": "Bearer abc.def.ghi"})
    assert resp.status_code == 401
    assert resp.text == ""


# ==================== POST：新增 / 更新（upsert）====================

def test_save_info_create(api, health_user):
    """首次 POST → 建档案，200；bmi 由后端算好，analysis 在顶层。"""
    resp = api.health.save_info(VALID_INFO, headers=health_user["headers"])
    body = api.assert_ok(resp, "保存健康信息应成功")

    assert body["message"] == "健康信息保存成功"

    data = body["data"]
    assert data["userId"] == health_user["userId"], "档案应挂在自己账号下"
    assert data["age"] == 30
    assert data["gender"] == "male"
    assert data["height"] == 175.0
    assert data["weight"] == 70.0

    # bmi 不由前端传，是后端按 weight/(height/100)^2 算出来的：
    #   70 / (1.75^2) = 22.857142857142858
    assert abs(data["bmi"] - 22.857142857142858) < 1e-6, f"bmi 计算不符：{data['bmi']}"

    assert "analysis" in body and "overallLevel" in body["analysis"], \
        "analysis 应在信封顶层"


def test_save_info_is_upsert(api, health_user):
    """再 POST 一次 → **更新同一条**（id 不变），不是插入第二条。

    upsert = update or insert。这个接口的语义是"一个用户一份档案"，
    所以第二次提交应该是改，而不是新增。
    """
    b1 = api.assert_ok(api.health.save_info(VALID_INFO, headers=health_user["headers"]))
    id1 = b1["data"]["id"]

    b2 = api.assert_ok(api.health.save_info(
        dict(VALID_INFO, weight=72.5), headers=health_user["headers"]))
    id2 = b2["data"]["id"]

    assert id1 == id2, f"upsert 应更新同一条（id 不变），实际 {id1} → {id2}"
    assert b2["data"]["weight"] == 72.5, "第二次提交的体重应生效"
    assert abs(b2["data"]["bmi"] - 23.6734693877551) < 1e-6, "bmi 应随体重一起重算"

    # 不只信响应，去库里核对：这个用户只应有一条档案
    n = db.query("SELECT COUNT(*) AS n FROM health_info WHERE user_id = %s",
                 (health_user["userId"],), one=True)["n"]
    assert n == 1, f"upsert 后库里该用户只应有 1 条档案，实际 {n}"


def test_get_info_after_save(api, health_user):
    """存完再读，字段一致（接口 + DB 双向核对）。"""
    api.assert_ok(api.health.save_info(VALID_INFO, headers=health_user["headers"]))

    body = api.assert_ok(api.health.get_info(headers=health_user["headers"]))
    data = body["data"]
    assert data["age"] == 30
    assert data["height"] == 175.0

    row = db.query("SELECT age, gender, height, weight FROM health_info WHERE user_id = %s",
                   (health_user["userId"],), one=True)
    assert row["age"] == 30, "接口返回和库里应一致"
    assert row["gender"] == "male"


def test_save_info_appends_history(api, health_user):
    """每 POST 一次就往 history 追加一条 —— 这是写操作的副作用，值得钉住。

    很多新人会以为"upsert 就是覆盖，不会留痕"，实测证明它会留：
    每次保存都在 health_info_history 里追加一条快照（记 weight / bmi / 日期）。
    """
    api.assert_ok(api.health.save_info(VALID_INFO, headers=health_user["headers"]))
    api.assert_ok(api.health.save_info(
        dict(VALID_INFO, weight=68.0), headers=health_user["headers"]))

    body = api.assert_ok(api.health.get_history(headers=health_user["headers"]))
    rows = body["data"]
    assert len(rows) == 2, f"两次保存应产生 2 条历史，实际 {len(rows)}"
    assert rows[0]["weight"] == 70.0
    assert rows[1]["weight"] == 68.0


# ==================== POST：校验失败（参数化）====================

@pytest.mark.parametrize("case", CASES, ids=case_name)
def test_save_info_fail(api, health_user, case):
    """校验失败：13 类非法输入，期望值全部来自数据文件。"""
    resp = api.health.save_info(case["body"], headers=health_user["headers"])

    api.assert_error(resp, case["want_code"], case["want_msg"], http=case["want_http"])


def test_save_info_without_token(api):
    """POST 同样必须带 token → 401 + 空体。"""
    resp = api.health.save_info(VALID_INFO)
    assert resp.status_code == 401
    assert resp.text == ""
