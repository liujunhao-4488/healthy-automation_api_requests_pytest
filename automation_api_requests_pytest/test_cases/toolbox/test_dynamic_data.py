# test_cases/test_dynamic_data.py
# 【任务 #3.7：动态数据 L3】
#
# 前三层的数据都是"提前准备好"的（写在文件里或生成出来）；
# 这一层的数据是"运行时现场取"的，来源有两处：
#   ① 数据库 —— 取"当前真实存在"的一条记录当输入
#   ② 上一个接口的响应 —— 链式依赖（数据在下游"流动"）

from common.db import query


def test_real_user_from_db_rejects_wrong_password(api):
    """从库里抽一个真实启用用户，用**错误密码**登录。

    期望：报『密码错误』而不是『用户不存在』。
    这一条断言反过来证明：这个邮箱确实存在于库中 —— 数据来自数据库，不是写死的。
    """
    rows = query(
        "select email from `user` "
        "where status = 1 and password is not null and password <> '' "
        "order by id limit 1"
    )
    assert rows, "库里应至少有一个可登录的启用用户"
    real_email = rows[0]["email"]

    resp = api_post_login(api, real_email, "definitely_wrong_pwd")
    assert resp["code"] == 400
    assert "密码错误" in resp["message"], f"应为『密码错误』，实际『{resp['message']}』"


def test_recipe_detail_id_from_db(api, auth_headers):
    """食谱 id 从数据库取 —— 比写死 id=101 更抗数据变动。"""
    rows = query("select id from recipe where status = 1 order by id limit 1")
    assert rows, "库里应有启用状态的食谱"
    recipe_id = rows[0]["id"]

    body = api.assert_ok(api.get(f"/recipe/detail/{recipe_id}", headers=auth_headers))
    assert body["data"]["recipe"]["id"] == recipe_id


def test_chain_data_from_api(api, auth_headers):
    """链式依赖：上一步接口的响应，就是下一步接口的输入。"""
    list_body = api.assert_ok(api.get("/recipe/list", headers=auth_headers))
    first = list_body["data"][0]

    detail_body = api.assert_ok(api.get(f"/recipe/detail/{first['id']}", headers=auth_headers))
    detail = detail_body["data"]["recipe"]

    # 详情里的字段必须与列表里那条对得上 —— 这才叫"链式校验"
    assert detail["id"] == first["id"]
    assert detail["name"] == first["name"]


def api_post_login(api, email, password):
    """小工具：登录并把响应体转成 dict 返回（本文件内部用）。"""
    return api.post("/auth/login", json={"email": email, "password": password}).json()
