# conftest.py
# 公共夹具（fixture）集中放这里。pytest 会自动加载。
# fixture 类比：开火前"热锅备料"，每个测试跑之前先把需要的东西准备好。

import pytest

from common.api_client import ApiClient
from config import TEST_USER


@pytest.fixture
def api():
    """请求客户端夹具：返回一个封装好的 ApiClient。

    用例里直接用 api.get("/xxx")、api.post("/xxx")，不用再管 BASE_URL 和超时。
    """
    return ApiClient()


@pytest.fixture
def token(api):
    """登录夹具：用测试账号登录，取出 token 交给需要鉴权的用例。"""
    resp = api.post("/auth/login", json=TEST_USER)
    body = api.assert_ok(resp)  # 登录本身必须成功
    assert "token" in body["data"], "登录成功必须返回 token"
    return body["data"]["token"]


@pytest.fixture
def auth_headers(token):
    """鉴权头夹具：把 token 包成 'Authorization: Bearer <token>'。"""
    return {"Authorization": f"Bearer {token}"}


# 【对照教材，不参与自动测试】
# test_recipe.py 是你手写的"旧风格"版本，保留下来只为对照阅读。
# 它按旧约定自己手写了 BASE_URL，而新的 api 夹具也会自动拼 BASE_URL，两者冲突会 404，
# 所以这里让它不参与收集，避免每次跑都报红。内容一个字没改。
#
# ⚠️ 路径是相对本文件（conftest.py 在项目根）的。测试文件分目录后这里也要跟着改，
#    否则旧文件会被重新收集 → 3 条 404 假红。
collect_ignore = ["test_cases/recipe/test_recipe.py"]
