# test_cases/test_auth.py
# 第一组测试：登录接口。
# 两类核心思路：
#   1) 正常路径（happy path）—— 对的账号密码 → 成功。
#   2) 异常路径 —— 错的密码 → 被拒绝（业务 code=400）。

from config import TEST_USER


def test_login_success(api):
    """正常路径：账号密码正确 → 登录成功，返回 token。"""
    resp = api.post("/auth/login", json=TEST_USER)

    # 一行断定"成功"：HTTP 200 + 业务 code==200，并直接拿到解析好的 body
    body = api.assert_ok(resp)
    assert body["message"] == "登录成功"

    # 关键数据：成功登录必须给 token，否则后续接口没法用
    assert "token" in body["data"]
    assert body["data"]["userId"] == 2


def test_login_wrong_password(api):
    """异常路径：密码错误 → 应当被拒绝（业务 code=400）。"""
    wrong = {**TEST_USER, "password": "this_is_wrong"}  # 复制账号，只改密码
    resp = api.post("/auth/login", json=wrong)

    body = resp.json()
    # 密码错属于"业务失败"，文档里登录失败返回 400（见 API.md 第 3 节）
    assert body["code"] == 400
    # 失败时不应下发 token
    assert "token" not in body.get("data", {})
