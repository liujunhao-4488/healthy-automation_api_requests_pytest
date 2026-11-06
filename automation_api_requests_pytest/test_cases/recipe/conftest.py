# test_cases/recipe/conftest.py
# 食谱模块（收藏四件套 + 读类契约）的专用夹具。
#
# ============ 为什么要自己造食谱，不直接用库里的 ============
# 测试库 health_diet_test 的 recipe 表**是空的**（seed_test.sql 只放了账号和食材）。
# 而开发库有 253 条 —— 这正是"别直接连开发库"的另一个理由：
# 一旦用例依赖"库里刚好有食谱"，换台机器就全红，还得反过来查是环境问题还是代码问题。
#
# 所以靶子食谱由夹具现造、用完随账号一起删（cleanup.purge_user 会连带删
# recipe 和 user_recipe_collect，见 common/cleanup.py 的子表清单）。
#
# ============ 为什么是"两个账号" ============
# 收藏接口的入参只有 recipeId，归属校验全靠 token。要证明"别人收藏的东西
# 我看不到、也改不了"，必须有一个**真实的另一个登录身份**。
# 拿不存在的 id 去测是无效的：后端可能根本没走到归属判断那一行。
# （同 user/test_notification_idor.py 开头的论证，那儿踩过的坑不再踩一遍。）

import uuid
from pathlib import Path

import pytest

from common import cleanup, db

_HERE = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items):
    """本目录用例都会连库造靶子（账号 + 食谱），统一标 requires_db。

    ⚠️ conftest 的 hook 收到的是**全量** items，必须按路径过滤 ——
       不过滤会把其它模块也标上，AUTOTEST_REQUIRE_DB=0 时一起被跳过（实测踩过）。
    """
    for item in items:
        if Path(str(item.fspath)).resolve().parent == _HERE:
            item.add_marker(pytest.mark.requires_db)


def _register(api, prefix):
    """注册一次性账号，返回 userId / email / 带 token 的请求头。"""
    uniq = prefix + uuid.uuid4().hex[:10]
    email = uniq + "@example.com"
    reg = api.assert_ok(
        api.auth.register({"username": uniq, "password": "123456", "email": email}),
        f"注册 {prefix} 账号应成功",
    )
    return {
        "userId": reg["data"]["userId"],
        "email": email,
        "headers": {"Authorization": "Bearer " + reg["data"]["token"]},
    }


def _insert_recipe(creator_id, name="夹具食谱", status=1, is_custom=1):
    """直接往库里插一条食谱，返回它的 id。

    为什么不走 POST /recipe/save：那是"用户自定义食谱"接口，字段和这里要造的
    （总热量、每份热量、分类）不完全一回事，而且它自己也是待测对象 ——
    用一个待测接口去准备另一个待测接口的数据，失败时分不清是谁坏了。
    造数据就直连库，这是最干净的分工。

    ⚠️ instructions 是 NOT NULL 且库里存的是 JSON 字符串（不是 JSON 列），
       所以这里要写成 '["1. 洗净","2. 下锅"]' 这种**带引号的字符串**。
       写成普通句子也能插进去，但前端解析会炸。
    """
    with db.transaction() as cur:
        cur.execute(
            "INSERT INTO recipe "
            "(name, description, category, cooking_time, difficulty, servings, "
            " total_calories, calories_per_serving, protein, carbs, fat, "
            " instructions, creator_id, is_custom, status) "
            "VALUES (%s, '夹具造的靶子食谱', '早餐', 10, '简单', 1, "
            "        300, 300, 10, 40, 8, '[\"1. 洗净\",\"2. 下锅\"]', %s, %s, %s)",
            (name, creator_id, is_custom, status),
        )
        return cur.lastrowid


@pytest.fixture
def recipe_pair(api):
    """一对真账号 + 一个造食谱的小工具。

    用法：

        rid = recipe_pair["add"]()                      # owner 名下的食谱
        api.recipe.collect(rid, headers=recipe_pair["owner"]["headers"])
        api.recipe.collect_status(rid, headers=recipe_pair["intruder"]["headers"])

    收尾：两个账号连同各自的食谱、收藏记录一起删。
    """
    owner = _register(api, "rcp_owner_")
    intruder = _register(api, "rcp_intr_")

    # ⚠️ 登记紧跟注册：下面自检一旦 assert 失败，生成器走不到 yield，
    #    teardown 整段不执行，两个账号就成了没人认领的孤儿
    #    （会话兜底只回收登记过的）。这个坑在 notification 夹具里踩过一次。
    for u in (owner, intruder):
        cleanup.register_user(u["userId"], u["email"])

    def add(name="夹具食谱", status=1, is_custom=1, who="owner"):
        target = owner if who == "owner" else intruder
        return _insert_recipe(target["userId"], name=name, status=status, is_custom=is_custom)

    # ---- 夹具自检：造出来的食谱必须真的能被后端读到 ----
    # 挡的是最阴的一种假绿：食谱插进库了，但后端的 /recipe/list 读不到
    # （后端连了别的库 / 加了 status 过滤 / 读写分离读到从库）。
    # 那样所有收藏用例都会得到"收藏失败"，看起来像鉴权生效，实际一条都没测到。
    probe_id = add("__fixture_probe__")
    body = api.assert_ok(
        api.recipe.list_all(headers=owner["headers"]),
        "owner 读取食谱列表应成功",
    )
    visible = {r["id"] for r in (body.get("data") or [])}
    assert probe_id in visible, (
        f"夹具自检失败：刚插的食谱 id={probe_id} 在 /recipe/list 里查不到。\n"
        f"→ 常见原因：后端连的不是测试库 health_diet_test、list 加了 status/creator 过滤、\n"
        f"  或者读写分离读到了还没同步的从库。\n"
        f"→ 先手工调一次 GET /recipe/list，确认刚造的食谱为什么不出现。"
    )
    db.execute("DELETE FROM recipe WHERE id = %s", (probe_id,))

    yield {"owner": owner, "intruder": intruder, "add": add}

    for u in (owner, intruder):
        cleanup.purge_user(u["userId"])
