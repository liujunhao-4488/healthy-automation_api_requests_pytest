# test_cases/ingredient/test_ingredient_读类契约.py
# 【B 档 · 薄测】食材库 4 个读接口
#
# ============ 这批用例为什么值得写（但只能薄写）============
# 食材库是全站**最稳的一块数据**：测试库有 125 条种子，前端所有"选食材记账"
# "算一道菜的营养"都从这里取。它几乎没有自己的业务逻辑（就是按条件 select），
# 所以深测没有收益 —— 但它的**契约**必须钉住，因为下游依赖它的字段名：
#   caloriesPer100g / proteinPer100g / carbsPer100g / fatPer100g
# 这四个字段一旦改名，热量计算、食谱营养分析、AI 的"这道菜多少卡"全跟着错，
# 而接口本身照样返回 200。
#
# ============ 本文件只断三件事 ============
#   ① 鉴权：4 个接口无 token 都该 401（API.md 写"无需认证"，实测相反 → 缺陷 #1）
#   ② 契约：返回的食材对象有没有那批 per100g 字段
#   ③ 边界：不存在的 id / 不存在的分类 / 空关键字，别崩、别返回 null
#
# 不断言"有 125 条""第一条是米饭"这类 —— 那是数据快照，换个库就红。

import pytest


# ==================== 鉴权 ====================

@pytest.mark.parametrize("call", [
    lambda api: api.ingredient.list_all(headers=None),
    lambda api: api.ingredient.detail(1, headers=None),
    lambda api: api.ingredient.by_category("蔬菜", headers=None),
    lambda api: api.ingredient.search("鸡", headers=None),
], ids=["list", "detail", "category", "search"])
def test_read_endpoints_require_token(api, call):
    """4 个读接口不带 token 全部 401 —— 与 API.md 的"无需认证"声明相反。

    同 recipe 读类的论证：文档与实现不一致，需要一个"有人盯着它变"的用例。
    """
    resp = call(api)
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)


# ==================== 契约 ====================

def test_list_returns_ingredients_with_per100g_fields(api, auth_headers):
    """食材对象必须带那四个 per100g 营养字段（下游全指望它）。

    ══ 为什么只断"字段存在"，不断值 ══
    值是数据库里的业务数据，会随运营调整（比如把米饭的热量从 116 改成 130）。
    断值等于把数据快照写进用例，改一次数据红一片。
    而**字段名**是契约，改名就是破坏性变更，必须红。
    """
    body = api.assert_ok(api.ingredient.list_all(headers=auth_headers), "读取食材列表应成功")
    data = body["data"]

    assert isinstance(data, list), f"食材列表的 data 应该是数组，实际 {type(data).__name__}"
    assert data, (
        "食材列表是空的。测试库应该有 125 条种子食材 —— "
        "空的说明 seed_test.sql 没跑，或者后端连的不是测试库。"
    )

    sample = data[0]
    for field in ("id", "name", "category", "caloriesPer100g", "proteinPer100g",
                  "carbsPer100g", "fatPer100g"):
        assert field in sample, (
            f"食材对象缺少字段 {field}，当前字段：{sorted(sample)}\n"
            f"→ per100g 系列是热量计算的基础，改名会让所有营养计算静默出错。"
        )


def test_detail_returns_single_object(api, auth_headers):
    """按 id 取单个食材，返回的是**对象**（不是只含一个元素的数组）。"""
    first_id = api.assert_ok(
        api.ingredient.list_all(headers=auth_headers), "读取食材列表"
    )["data"][0]["id"]

    body = api.assert_ok(api.ingredient.detail(first_id, headers=auth_headers),
                         "读取食材详情应成功")
    data = body["data"]
    assert isinstance(data, dict), f"detail 的 data 应该是对象，实际 {type(data).__name__}"
    assert data["id"] == first_id, f"要的是 id={first_id}，返回的是 {data['id']}"


def test_by_category_filters_to_that_category(api, auth_headers):
    """按分类取出来的每一条，category 都必须等于请求的分类。

    ══ 这条不是薄测，是确定性规则 ══
    "按蔬菜查，返回里不能有肉类" —— 这是接口语义，不是数据内容。
    后端如果把 category 当成模糊匹配（LIKE %蔬菜%）或者压根没加 where，
    结果里会混进别的分类，而前端会把它显示在"蔬菜"标签页下面。
    """
    body = api.assert_ok(api.ingredient.by_category("蔬菜", headers=auth_headers),
                         "按分类读取应成功")
    data = body["data"]
    assert isinstance(data, list), "按分类返回的 data 应该是数组"

    wrong = [i["name"] for i in data if i["category"] != "蔬菜"]
    assert not wrong, f"按「蔬菜」筛选，结果里混进了别的分类：{wrong[:5]}"


def test_search_returns_array_and_respects_keyword(api, auth_headers):
    """搜索：结果里每条的 name 都要包含关键字（大小写/中文都要能匹配）。"""
    body = api.assert_ok(api.ingredient.search("鸡", headers=auth_headers), "搜索应成功")
    data = body["data"]
    assert isinstance(data, list), "搜索结果的 data 应该是数组"

    no_match = [i["name"] for i in data if "鸡" not in i["name"]]
    assert not no_match, (
        f"搜「鸡」，结果里出现了不含该字的食材：{no_match[:5]}\n"
        f"→ 后端可能把 keyword 当成了模糊匹配但拼错了 LIKE，或者忽略了它。"
    )


# ==================== 边界 ====================

def test_missing_id_returns_null_data_not_error(api, auth_headers):
    """不存在的食材 id → 200 + data:null。

    ⚠️ **观察点**：同样是"查不到"，/recipe/detail 返回 {recipe:null}、
       /ingredient/detail 返回 data:null、/article/detail 返回 400。
       三个接口三种风格，没有统一依据，所以只记录不判定。
       断言落在"别 500、别返回一个假对象"这两点上。
    """
    resp = api.ingredient.detail(999999999, headers=auth_headers)

    assert resp.status_code == 200, f"当前实现是 200 + data:null，实际 {resp.status_code}"
    assert resp.json()["data"] is None, (
        f"不存在的食材应返回 data:null，实际 {str(resp.json()['data'])[:200]}\n"
        f"→ 返回假对象（比如全 0 的营养值）比 null 更危险：前端会当真数据展示。"
    )


def test_unknown_category_returns_empty_array(api, auth_headers):
    """不存在的分类 → 200 + 空数组（不是 null，也不是 400）。"""
    body = api.assert_ok(api.ingredient.by_category("绝不存在的分类QQQ", headers=auth_headers),
                         "查不存在的分类应成功返回空")
    assert body["data"] == [], f"应该返回空数组，实际 {body['data']!r}"


@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #20：/ingredient/search 缺 keyword 时返回 Spring 默认错误体"
           "（与缺陷 #2 /recipe/search、#12 同源）",
)
def test_bug_search_without_keyword_not_unified_envelope(api, auth_headers):
    """漏传 keyword → 期望统一信封，实际 Spring 默认体。

    ══ 为什么这条要单独记，而不是"README 说过了" ══
    缺陷 #2 只记了 /recipe/search 一个接口。实测 /ingredient/search、
    /article/search 是**同一个毛病** —— 说明不是某个接口写错了，
    而是"缺必填 query param"这个场景整体没被统一异常处理器覆盖。
    逐个接口钉住，修的时候才知道要修几处、修完是不是全修了。
    """
    resp = api.ingredient.search_without_keyword(headers=auth_headers)

    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}"
    body = resp.json()
    assert "code" in body, f"响应体不是统一信封：{str(body)[:300]}"
