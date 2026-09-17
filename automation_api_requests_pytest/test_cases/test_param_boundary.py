# test_cases/test_param_boundary.py
# 【任务 #3：参数化 + 边界/异常】
#
# 本文件只引入一个新概念：@pytest.mark.parametrize —— 让"一条用例"吃"一组输入"。
# 比喻：以前一张卷子只考一道题；现在同一个题目模板，发 N 份"不同数据的答题卡"，
#       每份单独判分（在报告里显示成 N 条独立用例）。
#
# 重要原则：下面所有"期望值"都来自我先真实跑过后端的结果，不是拍脑袋写的。
#          这正是测试用例的价值——期望必须来自"被测系统的真实契约"。
import json
import pytest

from config import TEST_USER

EMAIL = TEST_USER["email"]
PWD = TEST_USER["password"]


# ===================== 第 1 组：登录接口的参数化 =====================
# 每行 = (用例名, 请求体, 期望HTTP, 期望业务code, 期望message包含的内容)
LOGIN_CASES = [
    ("正常登录",   {"email": EMAIL, "password": PWD},              200, 200, "登录成功"),
    ("密码错误",   {"email": EMAIL, "password": "wrong"},          400, 400, "密码错误"),
    ("用户不存在", {"email": "nobody_x@qq.com", "password": PWD},  400, 400, "用户不存在"),
    ("密码为空",   {"email": EMAIL, "password": ""},               400, 400, "密码不能为空"),
    ("缺密码字段", {"email": EMAIL},                                400, 400, "密码不能为空"),
    ("邮箱为空",   {"email": "", "password": PWD},                 400, 400, "邮箱不能为空"),
    ("邮箱格式错", {"email": "not-an-email", "password": PWD},      400, 400, "邮箱格式不正确"),
    ("超长邮箱",   {"email": "a" * 200 + "@qq.com", "password": PWD}, 400, 400, "邮箱格式不正确"),
    ("SQL注入串",  {"email": EMAIL + "' OR '1'='1", "password": PWD}, 400, 400, "邮箱格式不正确"),
]


@pytest.mark.parametrize(
    "case_name, payload, want_http, want_code, want_msg",
    LOGIN_CASES,
    ids=[c[0] for c in LOGIN_CASES],  # 用每行第一列做报告里的用例名，中文可读
)
def test_login_param(api, case_name, payload, want_http, want_code, want_msg):
    """一条函数覆盖 9 种输入：正常 / 密码错 / 缺字段 / 空值 / 格式 / 超长 / 注入。"""
    resp = api.post("/auth/login", json=payload)

    assert resp.status_code == want_http, f"[{case_name}] HTTP 应为 {want_http}，实际 {resp.status_code}"
    body = resp.json()
    print(body)
    assert body["code"] == want_code, f"[{case_name}] code 应为 {want_code}，实际 {body.get('code')}"
    assert want_msg in body["message"], f"[{case_name}] message 应含『{want_msg}』，实际『{body.get('message')}』"


# ===================== 第 2 组：搜索关键词的健壮性 =====================
# 每行 = (用例名, 关键词, 结果是否应为非空)
SEARCH_CASES = [
    ("命中的词",   "三文鱼",            True),    # 应搜到结果
    ("空串(全量)", "",              True),    # 空关键词 → 返回全部
    ("无匹配词",   "zzzzzz",        False),   # 应搜不到
    ("SQL注入串",  "' OR 1=1 --",   False),   # 注入串不应生效（更不该返回全量）
    ("超长关键词", "a" * 300,       False),   # 超长不应 500 崩溃
]


@pytest.mark.parametrize(
    "case_name, keyword, expect_non_empty",
    SEARCH_CASES,
    ids=[c[0] for c in SEARCH_CASES],
)
def test_search_keyword(api, auth_headers, case_name, keyword, expect_non_empty):
    """五条搜索输入共用一条用例：重点看"不崩、不 500、注入不生效"。"""
    resp = api.get("/recipe/search", params={"keyword": keyword}, headers=auth_headers)
    body = api.assert_ok(resp)          # HTTP 200 + code 200
    data = body["data"]
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    assert isinstance(data, list), f"[{case_name}] data 应为列表"
    assert (len(data) > 0) == expect_non_empty, f"[{case_name}] 结果条数({len(data)})不符合预期"


# ============ 第 3 组：两条"文档与实现不一致"的记录（非参数化）============

def test_search_missing_keyword(api, auth_headers):
    """缺 keyword 参数 → HTTP 400。

    【发现】这里返回的不是统一信封（没有 code/message），而是 Spring 默认错误响应，
    与文档第 2 节"统一响应结构"的约定不一致 —— 记一条缺陷候选。
    所以这条只断言 HTTP 状态码，不去断言 code。
    """
    resp = api.get("/recipe/search", headers=auth_headers)
    assert resp.status_code == 400


def test_search_requires_token(api):
    """【发现】文档第 9 节写 `/recipe/search` 无需认证，实测不带 token → 401。

    按"实际行为"断言，并把文档不一致记录在案（留给后端确认是文档错还是实现错）。
    """
    resp = api.get("/recipe/search", params={"keyword": "鸡"})
    assert resp.status_code == 401
