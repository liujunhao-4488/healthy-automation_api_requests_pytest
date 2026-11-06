# test_cases/article/test_article_读类契约.py
# 【B 档 · 薄测】健康文章 5 个读接口
#
# ============ 一个前提要先说清楚：测试库里一篇文章都没有 ============
# health_article 在 health_diet_test 里是**空表**（2026-11-06 实测 total=0）。
# 这直接决定这批用例能测什么：
#   ✅ 能测：分页结构形状、鉴权、参数缺失的行为、"查不到"时的语义
#   ❌ 测不了：文章内容、评论树、点赞/收藏状态 —— 没有靶子，
#            硬写只能写"返回 200 就算过"，那种绿灯比红灯更糟（让人以为测过了）
#
# 要补这部分，得先造文章靶子（data 里塞一篇文章）。那是下一轮的事，
# 覆盖矩阵 §三 已把它归到 B 档"article 写类"，不在本次范围内。
#
# ============ 这批用例最值钱的一条 ============
# `/article/list` 的 data 是**标准分页对象** {total, pageSize, page, list, tags}，
# 而 `/record/list` 的 data 是**裸数组**。同一个项目两种风格。
# 这不算缺陷（都能用），但必须有人记着 —— 前端每接一个列表接口都得确认一次。
# 用例里钉住它，以后谁要"统一响应格式"，这就是那个清单。

import pytest


# ==================== 鉴权 ====================

@pytest.mark.parametrize("call", [
    lambda api: api.article.list_articles(headers=None),
    lambda api: api.article.tags(headers=None),
    lambda api: api.article.detail(1, headers=None),
    lambda api: api.article.search("健康", headers=None),
    lambda api: api.article.comments(1, headers=None),
], ids=["list", "tags", "detail", "search", "comments"])
def test_read_endpoints_require_token(api, call):
    """5 个读接口不带 token 全部 401（API.md 写的是"无需认证"/"可选用户"）。

    ⚠️ API.md 给 /article/list、/detail、/recommend 标的是「**可选**用户」——
       意思是"带不带 token 都能读"（带 token 时多返回"我的点赞状态"）。
       实测是**必须**带 token，匿名用户直接 401。
       这比 recipe 那个更严重：健康文章是典型的**面向未登录访客**内容，
       如果前端真按"无需登录也能看"来做落地页，会直接白屏。
    """
    resp = call(api)
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)


# ==================== 分页结构（本文件的核心）====================

def test_list_returns_pagination_object(api, auth_headers):
    """/article/list 的 data 是**分页对象**，不是数组。

    ══ 和 /record/list 对照着看 ══
        /article/list → {"total": 0, "pageSize": 10, "page": 1, "list": [], "tags": []}
        /record/list  → []
    两种风格并存。这条用例的作用是**把这个事实固定在代码里**，
    而不是靠某个人记得"那个接口返回的不一样"。
    """
    body = api.assert_ok(api.article.list_articles(headers=auth_headers),
                         "读取文章列表应成功")
    data = body["data"]

    assert isinstance(data, dict), (
        f"/article/list 的 data 应该是分页对象，实际 {type(data).__name__}：{str(data)[:200]}\n"
        f"→ 如果变成了数组，说明有人统一了响应格式；请同步检查 /record/list 是否也改了。"
    )
    for field in ("total", "pageSize", "page", "list", "tags"):
        assert field in data, f"分页对象缺少字段 {field}，当前字段：{sorted(data)}"

    assert isinstance(data["list"], list), "list 字段必须是数组（哪怕是空的）"
    assert data["total"] == len(data["list"]), (
        f"total={data['total']} 和 list 的长度 {len(data['list'])} 对不上。\n"
        f"→ 空表时两者都该是 0。对不上说明 total 查的是另一张表或者没加过滤条件。"
    )


def test_list_echoes_page_params(api, auth_headers):
    """pageSize 传什么就回显什么 —— 至少参数被接收了。

    ⚠️ 注意这条**只验回显，不验真的分页了**。
       文章表是空的，无法验证"第 2 页返回第 2 批"。
       对比 /record/list（有数据、pageSize 完全不生效，缺陷 #17）——
       这里的"回显正确"不能推断出"分页有效"，两件事。
       等有文章靶子之后再补真正的分页断言。
    """
    body = api.assert_ok(api.article.list_articles(page=2, page_size=3, headers=auth_headers),
                         "带分页参数读取应成功")
    data = body["data"]
    assert data["page"] == 2, f"请求 page=2，回显 page={data['page']}"
    assert data["pageSize"] == 3, f"请求 pageSize=3，回显 pageSize={data['pageSize']}"


# ==================== 查不到的语义 ====================

def test_missing_article_returns_business_400(api, auth_headers):
    """不存在的文章 → **业务 400「文章不存在」**，不是 404。

    ══ 为什么专门记这点 ══
    同一个项目里三种风格并存（这就是要写用例的原因）：
        /article/detail      → 400 业务错误（统一信封）
        /recipe/detail       → 200 + {recipe:null}
        /ingredient/detail   → 200 + data:null
    写前端的人如果按 REST 直觉写 `if (res.status === 404)`，这个分支永远走不到，
    "文章已删除"的友好提示永远不会出现。
    """
    resp = api.article.detail(999999999, headers=auth_headers)
    api.assert_error(resp, 400, "文章不存在")


def test_empty_tags_returns_array(api, auth_headers):
    """空表时标签返回 []，不是 null。"""
    body = api.assert_ok(api.article.tags(headers=auth_headers), "读取标签应成功")
    assert body["data"] == [], f"空表时应该返回空数组，实际 {body['data']!r}"


def test_comments_of_missing_article_returns_empty_array(api, auth_headers):
    """给不存在的文章查评论 → 200 + []（不报错）。

    ⚠️ 和 /article/detail 的处理方式**不一致**：详情不存在报 400，
       评论不存在返回空数组。不算缺陷（评论列表天然允许空），
       但值得记下来 —— 写前端的人会踩"为什么这里不报错"。
    """
    body = api.assert_ok(api.article.comments(999999999, headers=auth_headers),
                         "查不存在文章的评论应成功返回空")
    assert body["data"] == [], f"应该返回空数组，实际 {body['data']!r}"


# ==================== 缺参数 ====================

@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #20：/article/search 缺 keyword 时返回 Spring 默认错误体"
           "（与缺陷 #2 /recipe/search 同源）",
)
def test_bug_search_without_keyword_not_unified_envelope(api, auth_headers):
    """漏传 keyword → 期望统一信封，实际 Spring 默认体。

    这是同一类问题的第三个接口（recipe / ingredient / article 都有）。
    三个都钉住，是为了"修的时候能确认全修了"，而不是修一个漏两个。
    """
    resp = api.article.search_without_keyword(headers=auth_headers)

    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}"
    body = resp.json()
    assert "code" in body, f"响应体不是统一信封：{str(body)[:300]}"


def test_path_param_type_error_not_unified_envelope(api, auth_headers):
    """/article/detail/abc → 400 Spring 默认体（缺陷 #12 同源，记录事实）。

    ⚠️ 不断言为缺陷：根因已在缺陷 #12 记过（进入 Controller 前被框架拦下）。
       这条只是把 /article 这条路径也记进来。
    """
    resp = api.article.detail("abc", headers=auth_headers)

    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}"
    assert "code" not in resp.json(), (
        "现在走的是 Spring 默认错误体（无 code）。这条红了说明框架层异常"
        "也被包成统一信封了 —— 好事，请把缺陷 #12 标为已修复并删掉这条用例。"
    )
