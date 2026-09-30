# test_cases/test_recipe.py
# 第二组测试：食谱接口 /recipe/list。
# 这组重点教一件事：鉴权。对比"不带 token"和"带 token"两种结果。

from config import BASE_URL, TIMEOUT


def test_recipe_list_no_auth(api):
    """不带 token 访问受保护接口 → 应当被拦，返回 401。"""
    resp = api.get(BASE_URL + "/recipe/list", timeout=TIMEOUT)
    # 后端有 JWT 过滤器：没有合法 token，直接 401（未认证）。
    assert resp.status_code == 401


def test_recipe_list_with_auth(api, auth_headers):
    """带 token 访问 → 应当成功，返回统一信封 code=200。"""
    resp = api.get(
        BASE_URL + "/recipe/list",
        headers=auth_headers,   # 关键：把登录夹具给的鉴权头带上去
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200

    body = resp.json()
    # 统一信封：成功一定是 code=200（这是本项目判断成败的唯一标准）。
    assert body["code"] == 200
    # data 字段必须存在（返回的是食谱数据）。
    assert "data" in body


def test_recipe_detail_with_auth(api, auth_headers,id=101):
    resp=api.get(
        f"{BASE_URL}/recipe/detail/{id}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body["data"]["recipe"]
    print(body)
