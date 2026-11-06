# test_cases/recipe/test_recipe_收藏闭环.py
# 【A 档 · 状态机 + 数据归属】食谱收藏四件套
#
# ============ 为什么这批是"必须覆盖"的第一优先级 ============
# 覆盖矩阵 §三 的判断标准里，它同时满足前两条：
#   ① 有写副作用 + 状态流转：收藏 → 查状态 → 查列表 → 取消 → 再查状态。
#      手工点的时候，人只会点一次收藏、看一眼红心亮没亮就完了；
#      "取消之后列表里是不是真的没了""重复点会不会变成 2 条"没人会验。
#   ② 数据归属边界：入参只有 recipeId，归属全靠 token。拦不住就是
#      "任何人能取消任何人的收藏"。
# 而且这两个风险都是**静默的**：前端只看红心颜色，后端错了也看不出来。
#
# ============ 这个文件怎么组织的 ============
#   一、正向闭环   —— 五步顺序走一遍，钉住"收藏了就该看得到"
#   二、幂等       —— 重复收藏/取消，别产生脏数据
#   三、归属隔离   —— 别人的收藏我看不到、也改不了（IDOR）
#   四、字段语义   —— collectCount（全站）vs collected（我自己），最容易写错
#   五、鉴权       —— 没 token 进不来
#   六、已知缺陷   —— 用 xfail 钉住，修好那天会变 XPASS 提醒
#
# ⚠️ 每条用例都用**新造的账号**，不碰主测试账号 ——
#    收藏表是 (user_id, recipe_id) 唯一键，主账号的收藏状态不可控，
#    断言"列表里有 1 条"就会时灵时不灵。

import pytest

from common import db

pytestmark = pytest.mark.requires_db


# ==================== 小工具 ====================

def _status(api, rid, who):
    """读某人视角下的收藏状态，返回 (collected, collectCount)。"""
    body = api.assert_ok(
        api.recipe.collect_status(rid, headers=who["headers"]),
        f"用户 {who['userId']} 查询收藏状态应成功",
    )
    data = body["data"]
    return data["collected"], data["collectCount"]


def _collect_ids(api, who):
    """某人收藏列表里的食谱 id 集合。"""
    body = api.assert_ok(
        api.recipe.collect_list(headers=who["headers"]),
        f"用户 {who['userId']} 读取收藏列表应成功",
    )
    return {r["id"] for r in (body.get("data") or [])}


def _db_collect_rows(user_id, recipe_id):
    """直接查库：这一对 (user, recipe) 有几行收藏记录。

    用它来验"取消收藏是不是真删了"，和走接口查 status 互为补充：
    接口回答"用户看到什么"，库回答"数据实际长什么样"。
    只看接口，会漏掉"收藏行还在但 status 算错了"这种反向错误。
    """
    row = db.query(
        "SELECT COUNT(*) AS n FROM user_recipe_collect WHERE user_id = %s AND recipe_id = %s",
        (user_id, recipe_id), one=True,
    )
    return row["n"]


# ==================== 一、正向闭环 ====================

def test_collect_then_status_and_list_agree(api, recipe_pair):
    """收藏之后，**查状态**和**查列表**必须同时认账。

    ══ 为什么把两件事写在一条用例里 ══
    它们是同一个事实的两个出口。真实翻过的 bug 长这样：
    status 查的是 user_recipe_collect 表，list 查的是关联查询带 status=1 过滤，
    两边的 SQL 各写各的 —— 收藏成功了，红心亮了，但收藏夹是空的。
    分成两条用例时它们会**分别**通过，因为单独的每一条都只在验自己那个出口。
    """
    owner = recipe_pair["owner"]
    rid = recipe_pair["add"]()

    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "收藏应成功")

    collected, count = _status(api, rid, owner)
    assert collected is True, f"刚收藏成功，status 却返回 collected={collected}"
    assert count == 1, f"只有 owner 一个人收藏，collectCount 应该是 1，实际 {count}"

    assert rid in _collect_ids(api, owner), (
        f"收藏接口返回成功、status 也认了，但收藏列表里没有 recipeId={rid}。\n"
        f"→ 两个接口查的可能不是同一份数据（一个查关联表、一个查带过滤的联表）。"
    )

    # 数据库也确认一下：接口说收藏了，库里就该有那一行
    assert _db_collect_rows(owner["userId"], rid) == 1, (
        "收藏接口返回成功，但 user_recipe_collect 表里查不到这一行 —— 接口在骗人。"
    )


def test_uncollect_removes_from_status_and_list(api, recipe_pair):
    """取消收藏之后，状态和列表必须**同时**回到"没有"。"""
    owner = recipe_pair["owner"]
    rid = recipe_pair["add"]()

    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "收藏应成功")
    api.assert_ok(api.recipe.uncollect(rid, headers=owner["headers"]), "取消收藏应成功")

    collected, count = _status(api, rid, owner)
    assert collected is False, f"已取消收藏，status 仍返回 collected={collected}"
    assert count == 0, f"取消后 collectCount 应归零，实际 {count}"

    assert rid not in _collect_ids(api, owner), "已取消收藏，但列表里还有它"

    # 软删还是硬删？表里没有 is_deleted 列，所以必须是真删 —— 留残行会顶掉唯一键，
    # 导致"取消后重新收藏"报 Duplicate entry。这条断言就是防那个。
    assert _db_collect_rows(owner["userId"], rid) == 0, (
        "取消收藏后 user_recipe_collect 里还留着那一行。\n"
        "→ 表上有 uk_user_recipe 唯一键：残留会让「再收藏一次」直接撞唯一键报错。"
    )


def test_collect_again_after_uncollect_works(api, recipe_pair):
    """取消之后再收藏一次 —— 这是"残留行"缺陷唯一能暴露出来的路径。

    ══ 为什么这条不能省 ══
    取消收藏如果只是置了个"已取消"标记而没删行，
    上一条用例（取消后查不到）照样绿 —— 因为查询会过滤掉标记行。
    但唯一键还占着，用户第二次点收藏就会 500。
    真实产品里这对应"我今天不想吃了先取消，明天又想吃了再收藏"，
    是必走的路径，不是边角。
    """
    owner = recipe_pair["owner"]
    rid = recipe_pair["add"]()

    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "第一次收藏应成功")
    api.assert_ok(api.recipe.uncollect(rid, headers=owner["headers"]), "取消应成功")
    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "取消后重新收藏应成功")

    collected, count = _status(api, rid, owner)
    assert collected is True and count == 1, (
        f"重新收藏后状态不对：collected={collected}, collectCount={count}"
    )
    assert _db_collect_rows(owner["userId"], rid) == 1, "重新收藏后表里应该有且只有 1 行"


# ==================== 二、幂等 ====================

def test_collect_twice_does_not_duplicate(api, recipe_pair):
    """重复收藏不能变成 2 条，也不能报错。

    ══ 依据（判定为"应当幂等"而不是"应当报重复"）══
    前端收藏是**一个可连点的按钮**，双击是常规操作，不是攻击。
    所以接口要么幂等返回 200，要么至少返回业务码而不是 500。
    实测是幂等 200 —— 这正是期望值，用例把它钉住。
    """
    owner = recipe_pair["owner"]
    rid = recipe_pair["add"]()

    first = api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "第一次收藏应成功")
    second = api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "重复收藏应成功")

    assert first["data"]["collectCount"] == second["data"]["collectCount"] == 1, (
        f"重复收藏把计数加成了 {second['data']['collectCount']} —— "
        f"说明后端不是「判断已收藏就返回」，而是又插了一次。"
    )
    assert _db_collect_rows(owner["userId"], rid) == 1, (
        "重复收藏在 user_recipe_collect 里留下了多行。\n"
        "→ 如果唯一键还在，这里应该插不进去；能插进去说明唯一键被去掉了，"
        "收藏夹会出现重复卡片。"
    )


def test_uncollect_twice_does_not_error(api, recipe_pair):
    """重复取消收藏：第二次不能 500。

    实测验过是 200 + collected=false（幂等）。这条的价值是把"幂等"变成契约：
    哪天有人把它改成"没收藏就抛异常"，前端双击取消会弹一个吓人的报错。
    """
    owner = recipe_pair["owner"]
    rid = recipe_pair["add"]()

    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "收藏应成功")
    api.assert_ok(api.recipe.uncollect(rid, headers=owner["headers"]), "第一次取消应成功")
    api.assert_ok(api.recipe.uncollect(rid, headers=owner["headers"]), "重复取消应成功")

    collected, count = _status(api, rid, owner)
    assert collected is False and count == 0, (
        f"重复取消后状态不对：collected={collected}, collectCount={count}"
    )


# ==================== 三、归属隔离（IDOR）====================

def test_intruder_status_does_not_see_others_collect(api, recipe_pair):
    """B 查**A 收藏过的**食谱状态 → collected 必须是 false。"""
    owner, intruder = recipe_pair["owner"], recipe_pair["intruder"]
    rid = recipe_pair["add"]()

    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "A 收藏应成功")

    collected, count = _status(api, rid, intruder)
    assert collected is False, (
        f"B 从没收藏过 recipeId={rid}，status 却返回 collected={collected}。\n"
        f"→ 查询没有按 user_id 过滤，把别人的收藏当成了自己的。"
    )
    assert count == 1, (
        f"collectCount 是全站收藏数，应该是 1（A 一个人收藏），实际 {count}。\n"
        f"→ 如果这里也变成 0，说明接口把「全站数」错算成了「我的数」，"
        f"前端会显示「0 人收藏」但红心是亮的，两个数字自相矛盾。"
    )


def test_intruder_list_excludes_others_collect(api, recipe_pair):
    """B 的收藏夹里不能出现 A 收藏的食谱。"""
    owner, intruder = recipe_pair["owner"], recipe_pair["intruder"]
    rid = recipe_pair["add"]()

    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "A 收藏应成功")

    ids = _collect_ids(api, intruder)
    assert rid not in ids, (
        f"B 的收藏列表里出现了 A 收藏的 recipeId={rid} —— 收藏夹串号，属数据泄漏。"
    )


def test_intruder_uncollect_does_not_affect_owner(api, recipe_pair):
    """B 调"取消收藏"打 A 收藏的食谱 → A 的收藏必须还在。

    ══ 这条最容易误判，先说清楚期望值怎么来的 ══
    实测 B 调用后拿到的是 **200「已取消收藏」**，不是 403/400。
    看起来像越权成功，但数据没动 —— 因为后端删的是 (B 的 userId, recipeId) 这一对，
    B 本来就没有，删 0 行，幂等返回成功。

    这是**合理设计**（取消收藏天然幂等，不该因为"你没有"而报错），
    所以不断言 403。真正的风险是"删成了 A 的那一行"，所以断言落在数据上：
    A 的 status 仍是 true、库里 A 的行还在。
    """
    owner, intruder = recipe_pair["owner"], recipe_pair["intruder"]
    rid = recipe_pair["add"]()

    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "A 收藏应成功")
    api.recipe.uncollect(rid, headers=intruder["headers"])       # 不关心返回值，只看副作用

    collected, _ = _status(api, rid, owner)
    assert collected is True, (
        f"B 调了取消收藏之后，A 的收藏没了。\n"
        f"→ DELETE 的 WHERE 条件里漏了 user_id，B 把 A 的那一行删掉了。"
    )
    assert _db_collect_rows(owner["userId"], rid) == 1, "A 的收藏行被 B 删掉了（查库确认）"


def test_intruder_collect_does_not_steal_owner_collect(api, recipe_pair):
    """A、B 各收藏同一条食谱 → 两条独立的收藏记录，计数变 2。"""
    owner, intruder = recipe_pair["owner"], recipe_pair["intruder"]
    rid = recipe_pair["add"]()

    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "A 收藏应成功")
    api.assert_ok(api.recipe.collect(rid, headers=intruder["headers"]), "B 收藏应成功")

    _, count = _status(api, rid, owner)
    assert count == 2, f"两个人都收藏了，collectCount 应该是 2，实际 {count}"
    assert _db_collect_rows(owner["userId"], rid) == 1, "A 的收藏行数不对"
    assert _db_collect_rows(intruder["userId"], rid) == 1, "B 的收藏行数不对"

    # 唯一键应该按 (user_id, recipe_id) 生效，而不是只按 recipe_id ——
    # 后者会导致"第二个人收藏时报重复"，也就是全站只能有一个人收藏。
    ids = _collect_ids(api, intruder)
    assert rid in ids, "B 收藏成功了，但 B 自己的收藏列表里看不到"


# ==================== 四、字段语义 ====================

def test_collect_count_vs_collected_semantics(api, recipe_pair):
    """把 `collectCount` 和 `collected` 的语义差异钉死 —— 这是本轮最容易写错的断言。

    ══ 两个字段不是一个东西 ══
        collected    = **我**有没有收藏（随 token 变）
        collectCount = **全站**有多少人收藏（所有人看到的都一样）

    把 collected 写成 count > 0 是常见的误解，那样的断言在"别人收藏过"时
    会误判成"我收藏了"。这条用例用三个人把区别摆出来。
    """
    owner, intruder = recipe_pair["owner"], recipe_pair["intruder"]
    rid = recipe_pair["add"]()

    api.assert_ok(api.recipe.collect(rid, headers=owner["headers"]), "A 收藏应成功")

    a_collected, a_count = _status(api, rid, owner)
    b_collected, b_count = _status(api, rid, intruder)

    assert (a_collected, b_collected) == (True, False), (
        f"collected 应该因人而异，实际 A={a_collected}, B={b_collected}"
    )
    assert a_count == b_count == 1, (
        f"collectCount 应该对所有人一致（都是 1），实际 A={a_count}, B={b_count}"
    )


# ==================== 五、鉴权 ====================

def test_collect_list_requires_token(api):
    """收藏列表不带 token → 401。

    ⚠️ 401 的响应体**有内容**（2026-11-06 实测）：
           {"code":401,"message":"登录已过期，请重新登录","data":null}
       而覆盖矩阵长期记的是「401 全站空响应体」—— 那条记录已经过时了，
       所以这里可以正常走 assert_error，不用把 message 传 None。
    """
    resp = api.recipe.collect_list(headers=None)
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)


def test_collect_status_requires_token(api):
    """收藏状态不带 token → 401。"""
    resp = api.recipe.collect_status(1, headers=None)
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)


def test_collect_requires_token_post(api, recipe_pair):
    """收藏（POST）不带 token → 401，且**不能真的收藏成功**。"""
    owner = recipe_pair["owner"]
    rid = recipe_pair["add"]()

    resp = api.recipe.collect(rid, headers=None)
    api.assert_error(resp, 401, "登录已过期，请重新登录", http=401)

    # 关键：401 之后这一行不能存在。只看状态码会漏掉"先写后验权"的实现。
    assert _db_collect_rows(owner["userId"], rid) == 0, (
        "未登录的收藏请求被 401 拒绝了，但库里多了一行收藏记录 —— 先写库后验权。"
    )


# ==================== 六、已知缺陷 ====================

@pytest.mark.xfail(
    strict=True,
    reason="缺陷 #13：收藏不存在的食谱，400 响应体里吐出 MyBatis/SQL 外键异常原文"
           "（含库名、表名、约束名），属内部实现泄露",
)
def test_bug_collect_missing_recipe_leaks_sql(api, recipe_pair):
    """收藏一个不存在的 recipeId → 期望统一信封「食谱不存在」，实际吐 SQL 异常。

    ══ 为什么这是缺陷而不是"报 400 就够了" ══
    依据是项目自己的约定（覆盖矩阵 §六 判定纪律第 2 条：与既定标准不一致）：
      · API.md 承诺"统一响应结构 {code, message, data}"；
      · 缺陷 #3 已经因为同一件事修过一次（height=0 时吐 MySQL 异常栈），
        当时定性为"内部实现细节泄露（安全隐患）"。
    同一类问题再出现一次，就是回归，不是"新设计"。

    ══ 泄露了什么（这才是它比"格式不统一"严重的地方）══
    响应体里带着：库名 health_diet_test、表名 user_recipe_collect、
    约束名 user_recipe_collect_ibfk_2、甚至 INSERT 语句片段。
    攻击者不用扫端口，调一个收藏接口就知道你的库结构和表名。
    """
    owner = recipe_pair["owner"]

    resp = api.recipe.collect(999999999, headers=owner["headers"])

    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}"
    body = resp.json()
    message = body.get("message") or ""
    assert "SQL" not in message and "Exception" not in message, (
        f"响应体里含有 SQL/异常字样，泄露了实现细节：\n{message[:400]}"
    )
    assert "食谱不存在" in message, f"期望一句用户能看懂的提示，实际：{message[:300]}"
