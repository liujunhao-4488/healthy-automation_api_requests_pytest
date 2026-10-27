# test_cases/auth/test_login.py
# 【任务：登录接口 · 数据驱动 DDT】数据不再写在代码里，改从 data/ 文件读。

import pytest

from common.accounts import ensure_login_seed_account
from common.data_loader import load_cases


@pytest.fixture(scope="module", autouse=True)
def seed_login_account():
    """确保数据文件依赖的 123456@qq.com 存在。

    seed_test.sql 是主路径；这里兜底，防止"只建了表没导种子"时
    正常登录用例红成"用户不存在"。
    """
    ensure_login_seed_account()

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
    """登录：成功 + 各类失败，期望值全部来自数据文件，代码里没有任何硬编码。

    ⚠️ 这份数据里**成功和失败混在一起**，所以按 want_code 分流：
       200 → assert_ok   其余 → assert_error
       以前两种情况都套同一套三层断言，读代码的人得先看数据才知道这条是成功还是失败。
    """
    resp = api.auth.login({"email": case["email"], "password": case["password"]})

    if case["want_code"] == 200:
        body = api.assert_ok(resp, "登录应成功")
        assert "token" in body["data"], "登录成功必须返回 token"
    else:
        api.assert_error(
            resp, case["want_code"], case["want_msg"], http=case["want_http"]
        )
