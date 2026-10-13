# test_cases/auth/test_login.py
# 【任务：登录接口 · 数据驱动 DDT】数据不再写在代码里，改从 data/ 文件读。

import pytest

from common.data_loader import load_cases

# 数据来源：data/login_cases.yaml
# 想换格式？只改这一行的文件名即可（json / csv / xlsx 都支持，用例一个字不用动）。
#   ⚠️ 只有 CSV 需要多写一个参数 int_fields=("want_http", "want_code")，
#      因为 CSV 读出来**全是字符串**，200 会变成 "200"。
CASES = load_cases("login_cases.yaml")


def case_name(case):
    """用数据里的 name 字段当中文用例名。"""
    return case["name"]


@pytest.mark.parametrize("case", CASES, ids=case_name)
def test_login(api, case):
    """登录：成功 + 各类失败，期望值全部来自数据文件，代码里没有任何硬编码。"""
    resp = api.auth.login({"email": case["email"], "password": case["password"]})

    assert resp.status_code == case["want_http"], \
        f"期望 HTTP {case['want_http']}，实际 {resp.status_code}"

    body = resp.json()
    assert body["code"] == case["want_code"], \
        f"期望 code={case['want_code']}，实际 {body.get('code')}"
    assert body["message"] == case["want_msg"], \
        f"期望 message={case['want_msg']}，实际 {body.get('message')}"

    # 成功用例额外验证：返回里要带 token
    if case["want_code"] == 200:
        assert "token" in body["data"], "登录成功必须返回 token"
