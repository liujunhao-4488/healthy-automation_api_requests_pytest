# test_cases/test_recipe_v2.py
# 【新风格版】—— 和 test_recipe.py（你手写的旧风格）放在一起对照看。
# 三条用例一模一样，只把"重复动作"交给了 ApiClient：
#   1) 路径只写相对部分 "/recipe/list"，BASE_URL 由 ApiClient 自动拼 → 不用再手写 BASE_URL
#   2) api.assert_ok(resp) 一行完成 "HTTP 200 + 业务 code==200" 双重校验 → 不用再手写
# compared with: test_recipe.py


def test_recipe_list_no_auth(api):
    """不带 token 访问受保护接口 → 401（同旧版第 1 条）。"""
    # 旧版： resp = api.get(BASE_URL + "/recipe/list", timeout=TIMEOUT)
    resp = api.get("/recipe/list")
    assert resp.status_code == 401


def test_recipe_list_with_auth(api, auth_headers):
    """带 token 访问 → 成功，统一信封 code==200（同旧版第 2 条）。"""
    resp = api.get("/recipe/list", headers=auth_headers)
    # 旧版要写 4 行： status_code==200 / json() / code==200 / "data" in body
    # 新版一行搞定：
    body = api.assert_ok(resp)
    assert "data" in body


def test_recipe_detail_with_auth(api, auth_headers):
    """食谱详情 → 成功（同旧版第 3 条，但 id 动态取，不写死）。"""
    # 先从列表里拿一个真实存在的 id：数据被删/新增都不怕，比写死 id=101 更稳
    list_body = api.assert_ok(api.get("/recipe/list", headers=auth_headers))
    recipe_id = list_body["data"][0]["id"]

    resp = api.get(f"/recipe/detail/{recipe_id}", headers=auth_headers)
    body = api.assert_ok(resp)
    # 断言"取到的详情 id == 刚才那个 id"，比只判 "id" in ... 更严格
    assert body["data"]["recipe"]["id"] == recipe_id
