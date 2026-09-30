# 【任务 #4.2b：食谱搜索 /recipe/search】
#
# 本文件原来混在 auth/test_param_boundary.py 里（那是个"按知识点切"的文件，
# 里面 9 条打 /auth/login、7 条打 /recipe/search —— 一个文件两个资源）。
# 按 README 约定 5「按资源切文件」拆出来，登录那 9 条归入 auth/test_login.py。
#
# 本文件只讲一件事：搜索接口的健壮性 + 两条"文档与实现不一致"的记录。
#
# 本文件用例数：5 + 2 = 7

import pytest


# ===================== 第 1 组：搜索关键词的健壮性 =====================
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
    print(len(body["data"]))
    assert isinstance(data, list), f"[{case_name}] data 应为列表"
    assert (len(data) > 0) == expect_non_empty, f"[{case_name}] 结果条数({len(data)})不符合预期"


# ============ 第 2 组：两条"文档与实现不一致"的记录（非参数化）============

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
