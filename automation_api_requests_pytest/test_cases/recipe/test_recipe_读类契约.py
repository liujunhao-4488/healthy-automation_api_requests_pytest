# test_cases/recipe/test_recipe_读类契约.py
# 【B 档 · 薄测】食谱的 5 个读接口：只断"结构对不对、空参数崩不崩、没登录进不进得来"
#
# ============ 为什么这批只做薄壳，不深测 ============
# 覆盖矩阵 §三 B 档的口径：「只断信封结构 + 空参数 + 权限，不要为每个接口写 10 条」。
# 理由是这些接口**没有自己的业务逻辑**：list 就是 select，detail 就是 select by id，
# 输出的内容由库里的数据决定。深测它们等于在测 MySQL 会不会 select ——
# 用例数涨了，能挡住的风险没涨。
#
# 它们真正的回归风险只有三种，本文件就测这三种：
#   ① **鉴权和文档不一致**：API.md 写"无需认证"，实测 401（缺陷 #1）。
#      这条一旦"修好"（真的放开白名单），就是**安全回归**，必须有人拦。
#   ② **空参数 / 缺参数**：query param 漏传时返回什么。实测是 Spring 默认错误体，
#      不走统一信封（缺陷 #2）—— 前端按 body.message 解析会拿到 undefined。
#   ③ **返回结构**：字段名和嵌套层级（detail 的 data 是 {recipe, ingredients}，
#      不是扁平食谱对象）。前端联调时最容易在这里对不上。
#
# ============ 明确不测什么 ============
#   · 不断言"返回几条食谱" —— 取决于库里有什么，换个环境就红；
#   · 不断言搜索结果的排序/相关性 —— 由 SQL 和算法决定，写死就是假红；
#   · 不用例逐个测"每个字段的类型" —— 已由 ①③ 的字段存在性覆盖，再多是重复。

import pytest

pytestmark = pytest.mark.requires_db


# ==================== 鉴权（缺陷 #1 的回归保护）====================

@pytest.mark.parametrize("name,path,call", [
    ("list", "/recipe/list", lambda api: api.recipe.list_all(headers=None)),
    ("detail", "/recipe/detail/1", lambda api: api.recipe.detail(1, headers=None)),
    ("search", "/recipe/search", lambda api: api.recipe.search("鸡", headers=None)),
    ("nutrition", "/recipe/nutrition/1", lambda api: api.recipe.nutrition(1, headers=None)),
    ("custom", "/recipe/custom", lambda api: api.recipe.custom(headers=None)),
], ids=["list", "detail", "search", "nutrition", "custom"])
def test_read_endpoints_require_token(api, name, path, call):
    """5 个读接口不带 token 全部 401 —— 与 API.md 的"无需认证"声明**相反**。

    ══ 为什么把这条当"必须守"而不是"文档错了改文档就行" ══
    两种可能，都不能靠猜：
      a) 文档对、实现错 → 现在是**功能缺陷**（匿名用户看不了食谱）；
      b) 实现对、文档错 → 现在没问题，但文档得改，否则迟早有人"照着文档"
         把这几个接口加进白名单，那时就是**真的**把食谱库匿名公开了。
    无论哪种，都需要有人盯着它变。所以用一条参数化用例一次覆盖 5 个，
    红色的时候一眼看得见是哪个接口变了。

    ⚠️ 401 的响应体是有内容的（{"code":401,"message":"登录已过期，请重新登录"}），
       不是覆盖矩阵旧记录里的"空响应体"。
    """
    resp = call(api)
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)


# ==================== 返回结构 ====================

def test_list_returns_flat_array_of_recipes(api, recipe_pair):
    """/recipe/list 的 data 是**扁平数组**，每个元素是完整食谱对象。

    ⚠️ 和 /article/list 对比着看：那边 data 是 {total, pageSize, page, list} 分页对象。
       同一个项目两种风格，前端每接一个接口都要重新确认一次 —— 这个事实
       值得被用例记录下来，而不是靠人记。
    """
    owner = recipe_pair["owner"]
    rid = recipe_pair["add"]("契约用例的食谱")

    body = api.assert_ok(api.recipe.list_all(headers=owner["headers"]), "读取食谱列表应成功")
    data = body["data"]
    assert isinstance(data, list), (
        f"/recipe/list 的 data 应该是数组，实际 {type(data).__name__}：{str(data)[:200]}\n"
        f"→ 如果变成了分页对象，前端所有直接 .map() 的地方都会崩。"
    )

    item = next((r for r in data if r["id"] == rid), None)
    assert item is not None, f"刚造的食谱 id={rid} 不在列表里（夹具自检应该已经拦住了）"

    # 只断"关键字段存在"，不断类型细节 —— 薄测的边界就在这里
    for field in ("id", "name", "category", "totalCalories", "caloriesPerServing",
                  "protein", "carbs", "fat", "instructions", "creatorId", "isCustom"):
        assert field in item, f"食谱对象缺少字段 {field}：当前字段 {sorted(item)}"


def test_detail_wraps_recipe_and_ingredients(api, recipe_pair):
    """/recipe/detail 的 data 是**嵌套结构** {recipe, ingredients}。

    ══ 这是最容易写错的地方 ══
    方法名叫 detail，直觉上 data 就是食谱本身。实测是两层：
        {"recipe": {...食谱字段...}, "ingredients": [...关联食材...]}
    写成 data["name"] 会 KeyError，然后被误判成"接口挂了"。
    """
    owner = recipe_pair["owner"]
    rid = recipe_pair["add"]("详情结构用例")

    body = api.assert_ok(api.recipe.detail(rid, headers=owner["headers"]), "读取食谱详情应成功")
    data = body["data"]

    assert isinstance(data, dict), f"detail 的 data 应该是对象，实际 {type(data).__name__}"
    assert set(data) >= {"recipe", "ingredients"}, (
        f"detail 的 data 应该含 recipe / ingredients 两个键，实际 {sorted(data)}\n"
        f"→ 如果改成了扁平结构（data 直接就是食谱），请同步改 api/recipe_api.py 的说明。"
    )
    assert data["recipe"] is not None, f"食谱 id={rid} 明明存在，recipe 却是 null"
    assert data["recipe"]["id"] == rid
    assert isinstance(data["ingredients"], list), "ingredients 应该是数组（可以为空）"


def test_detail_of_missing_id_returns_empty_shell_not_error(api, recipe_pair):
    """不存在的食谱 id → 200 + {recipe: null, ingredients: []}，**不报错**。

    ⚠️ **观察点，不断言为缺陷**（判定纪要我查过了）：
       同一个项目里两种风格并存 ——
         · /article/detail 不存在 → 400「文章不存在」
         · /recipe/detail 不存在 → 200 + 空壳
       谁对谁错没有依据（API.md 没写详情接口的失败语义）。
       所以这里只记录"实际是哪种"，不下对错。要改，先改 API.md 统一定义。
    """
    body = api.assert_ok(
        api.recipe.detail(999999999, headers=recipe_pair["owner"]["headers"]),
        "当前实现：不存在的食谱也返回 200",
    )
    assert body["data"]["recipe"] is None, (
        f"期望 recipe 为 null（空壳），实际 {str(body['data'])[:200]}"
    )
    assert body["data"]["ingredients"] == [], "空壳里的 ingredients 应该是空数组，不是 null"


def test_nutrition_returns_object_even_for_missing_recipe(api, recipe_pair):
    """营养分析：即使食谱不存在也返回 200 + 空对象 {}。

    ⚠️ 观察点：`data: {}` 而不是 `data: null`。前端要按"对象里有没有 key"
       判断有没有数据，不能用 `if not data` —— 空对象是真值，判断会反。
    """
    owner = recipe_pair["owner"]
    rid = recipe_pair["add"]("营养分析用例")

    body = api.assert_ok(api.recipe.nutrition(rid, headers=owner["headers"]),
                         "分析食谱营养应成功")
    assert isinstance(body["data"], dict), (
        f"nutrition 的 data 应该是对象，实际 {type(body['data']).__name__}"
    )


# ==================== 空参数 / 缺参数 ====================

@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #2：/recipe/search 缺 keyword 时返回 Spring 默认错误体"
           "{timestamp,status,error,path}，不走统一信封 {code,message}",
)
def test_bug_search_without_keyword_not_unified_envelope(api, recipe_pair):
    """漏传 keyword → 期望统一信封，实际是 Spring 默认体。

    ══ 依据 ══
    API.md 开头承诺所有接口统一返回 `{code, message, data}`；
    缺陷 #2 已就这个接口记录过一次，缺陷 #12 也因同类问题（路径参数类型转换失败）
    用 xfail 钉过。这是团队已确立的标准，不是我的口味。

    ══ 影响 ══
    前端全局拦截器读的是 `body.message`，这里拿到 undefined，
    用户看到的是一个**空白错误提示**（或者 "undefined"）。
    这类问题在页面上表现为"点了搜索没反应"，排查时完全看不出是参数问题。
    """
    resp = api.recipe.search_without_keyword(headers=recipe_pair["owner"]["headers"])

    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}"
    body = resp.json()
    assert "code" in body, (
        f"响应体里没有业务 code 字段，不是统一信封：{str(body)[:300]}"
    )


def test_search_with_keyword_returns_array(api, recipe_pair):
    """带合法 keyword 时正常返回数组（空结果也是数组，不是 null）。

    ══ 为什么空结果也要断 ══
    "搜不到"返回 `null` 还是 `[]`，是前端 `result.map()` 崩不崩的分水岭。
    实测是 `[]`，钉住它。
    """
    owner = recipe_pair["owner"]
    recipe_pair["add"]("独一无二的食谱名XYZ")

    body = api.assert_ok(api.recipe.search("独一无二的食谱名XYZ", headers=owner["headers"]),
                         "搜索食谱应成功")
    assert isinstance(body["data"], list), "搜索结果的 data 应该是数组"

    empty = api.assert_ok(api.recipe.search("绝不可能存在的食谱名QQQ", headers=owner["headers"]),
                          "搜不到也应成功返回")
    assert empty["data"] == [], f"搜不到时应该返回空数组，实际 {empty['data']!r}"


def test_path_param_type_error_not_unified_envelope(api, recipe_pair):
    """/recipe/detail/abc（id 不是数字）→ 400 Spring 默认体（缺陷 #12 同源）。

    ⚠️ **这条不断言为缺陷，用"记录事实"的写法**：
       它和缺陷 #12 是同一个根因（进入 Controller 之前就被框架拦下），
       已在缺陷单里。这里只把 /recipe 这条路径也记下来，
       避免有人以为"只有 notification 有这个问题"。
    """
    resp = api.recipe.detail("abc", headers=recipe_pair["owner"]["headers"])

    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}"
    body = resp.json()
    assert "code" not in body, (
        "现在的实现走 Spring 默认错误体（无 code）。如果这条断言红了，"
        "说明有人把框架层异常也包成统一信封了 —— 那是好事，"
        "请把缺陷 #12 标为已修复并删掉这条用例。"
    )
