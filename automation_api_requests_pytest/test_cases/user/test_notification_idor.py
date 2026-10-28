# test_cases/user/test_notification_idor.py
# 【越权 / IDOR】通知接口：别人能不能操作我的通知。
#
# ============ 这个文件为什么存在 ============
# /notification/read/{id} 和 /notification/delete/{id} 的入参**只有 id**，
# 没有 token 之外的任何"这东西属于谁"的信息。如果后端忘了校验归属，
# 任何一个登录用户都能遍历 id 把全站用户的通知改已读或删掉 —— 数据泄漏级。
#
# 读后端代码看，NotificationController 第 81 / 109 行是有校验的：
#     if (notification == null || !userId.equals(notification.getUserId()) || ...)
# 所以这里的定位是**回归保护**，不是"找 bug"。
# 这两者断言强度不一样：找 bug 时"能复现问题"就够；
# 回归保护必须能挡住"哪天有人把这行删了"，所以它得有副作用回查 + 正角色对照。
#
# ============ 断言强度：这类测试最容易写成垃圾的三个地方 ============
#   垃圾写法 1：只断状态码 400，不管数据动没动。
#       → 第 1、3 节：越权之后回查，证明 is_read / is_deleted **真的没变**。
#         后端完全可能"返回 400 但其实已经改了"（先改再校验），只断码永远看不出来。
#   垃圾写法 2：没有正角色对照。
#       → 第 5 节：owner 操作自己的通知必须 200。
#         否则"接口整个坏掉、永远返回 400"也能让全部用例绿。
#   垃圾写法 3：拿不存在的 id 当越权样本。
#       → 夹具造的是**真实存在**的通知，只有它能触发归属校验那一行。
#         id=999999999 这种样本，后端在查库前就拒了，测了等于没测。
#
# ============ 与后端代码的一处重要约定：越权返回 400，不是 403 ============
# 实测："别人的通知"和"不存在的通知"返回**完全相同**的
#     HTTP 400 {"code":400,"message":"消息不存在"}
# 这是刻意的（防枚举：不能让攻击者通过状态码区分"存在但不是你的"和"不存在"）。
# 第 4 节专门把这条约定钉死 —— 哪天有人"顺手"把越权改成 403，
# 就等于给攻击者送了一个用户数据探针。

import pytest

# 夹具要连库造靶子数据（通知），db 不可用时整片跳过。
pytestmark = pytest.mark.requires_db

# 「消息不存在」——越权和"真的不存在"共用这个文案，是防枚举的一部分。
NOT_FOUND = "消息不存在"


def _list(api, who):
    """读某人的收件箱，返回列表。"""
    body = api.assert_ok(
        api.notification.list_mine(headers=who["headers"]),
        f"用户 {who['userId']} 读取通知列表应成功",
    )
    return body.get("data") or []


def _find(items, notification_id):
    """从列表里挑出某条，找不到返回 None。"""
    return next((n for n in items if n["id"] == notification_id), None)


# ==================== 一、越权改已读 ====================

def test_intruder_cannot_mark_others_notification_read(api, notification_pair):
    """B 用自己的 token 去标记 A 的通知 → 必须失败。"""
    nid = notification_pair["add"]("A 的私有通知")

    resp = api.notification.mark_read(nid, headers=notification_pair["intruder"]["headers"])

    api.assert_error(resp, 400, NOT_FOUND)


def test_intruder_mark_read_does_not_actually_change_data(api, notification_pair):
    """越权被拒之后，A 那条通知**必须还是未读**。

    ══ 为什么这条要单独写，不能靠上一条覆盖 ══
    上一条只证明了"响应是 400"。但后端完全可能是**先把 is_read 改掉、
    再判断权限**，或者事务里改完又回滚失败 —— 响应照样 400，数据已经脏了。
    这种 bug 只看状态码一辈子发现不了。

    ══ 为什么用 A 的列表回查，而不是查数据库 ══
    查库只能证明"库里那行没变"，而 A 实际看到什么，取决于后端读的是哪个库。
    走 A 的接口回查，物理上保证和越权请求是同一个后端、同一个库。
    """
    nid = notification_pair["add"]("A 的私有通知")
    owner = notification_pair["owner"]
    intruder = notification_pair["intruder"]

    api.notification.mark_read(nid, headers=intruder["headers"])

    item = _find(_list(api, owner), nid)
    assert item is not None, (
        f"越权请求之后，A 自己的列表里找不到通知 id={nid} 了 —— 数据被动了。"
    )
    assert item["isRead"] == 0, (
        f"越权被 400 拒绝了，但 A 的通知**真的变成已读了**（isRead={item['isRead']}）。\n"
        f"→ 这是「拦住了响应、没拦住副作用」：攻击者看到 400 会以为失败了，\n"
        f"  实际上已经改掉了用户的数据。\n"
        f"→ 后端要检查：归属校验是否在读改之前。"
    )
    assert item["readTime"] is None, (
        f"is_read 还是 0，但 read_time 被写入了（{item['readTime']}）—— 数据不一致。"
    )


# ==================== 二、越权删除 ====================

def test_intruder_cannot_delete_others_notification(api, notification_pair):
    """B 用自己的 token 去删除 A 的通知 → 必须失败。"""
    nid = notification_pair["add"]("A 的私有通知")

    resp = api.notification.delete(nid, headers=notification_pair["intruder"]["headers"])

    api.assert_error(resp, 400, NOT_FOUND)


def test_intruder_delete_does_not_actually_remove_it(api, notification_pair):
    """越权删除被拒之后，A 那条通知**必须还在**。"""
    nid = notification_pair["add"]("A 的私有通知")
    owner = notification_pair["owner"]

    api.notification.delete(nid, headers=notification_pair["intruder"]["headers"])

    assert _find(_list(api, owner), nid) is not None, (
        f"越权删除被 400 拒绝了，但 A 的通知 id={nid} **从收件箱里消失了**。\n"
        f"→ 「删掉了但返回失败」比「删掉了且返回成功」更阴险：用户毫无察觉地丢数据。"
    )


# ==================== 三、已删除的通知不能再操作 ====================

def _mark_read(api, nid, headers):
    return api.notification.mark_read(nid, headers=headers)


def _delete(api, nid, headers):
    return api.notification.delete(nid, headers=headers)


@pytest.mark.parametrize("op", [_mark_read, _delete], ids=["标记已读", "删除"])
def test_deleted_notification_rejects_further_operations(api, notification_pair, op):
    """已经删掉（is_deleted=1）的通知，本人再操作也必须报「消息不存在」。

    后端那行校验是 `notification == null || !属于我 || is_deleted == 1` 三合一，
    这一节盯的是第三个条件。漏掉它的话，删掉的通知还能被改已读，
    等于"删除"没真正生效（只是列表里看不见了）。
    """
    nid = notification_pair["add"]("已删除的通知", is_deleted=1)

    resp = op(api, nid, notification_pair["owner"]["headers"])

    api.assert_error(resp, 400, NOT_FOUND)


# ==================== 四、防枚举：越权和不存在的响应必须一模一样 ====================
# 这一节是"安全"而不是"功能"：如果两种情况的响应有任何差别
# （状态码不同、文案不同、甚至 body 里多了个字段），攻击者就能拿它当探针，
# 遍历 id 判断"这个通知存在吗、属于谁"。这属于信息泄露，即使数据本身没被改。

@pytest.mark.parametrize("op", [_mark_read, _delete], ids=["标记已读", "删除"])
def test_others_id_and_missing_id_are_indistinguishable(api, notification_pair, op):
    """「别人的通知」和「根本不存在的通知」，响应必须完全相同。"""
    exist_but_not_mine = notification_pair["add"]("A 的私有通知")
    intruder = notification_pair["intruder"]["headers"]

    r_real = op(api, exist_but_not_mine, intruder)
    r_fake = op(api, 999999999, intruder)

    assert r_real.status_code == r_fake.status_code, (
        f"「别人的通知」返回 HTTP {r_real.status_code}，"
        f"「不存在的通知」返回 HTTP {r_fake.status_code} —— 两者不一致，"
        f"攻击者可以据此判断某个 id 是否存在（用户数据枚举）。"
    )
    assert r_real.json() == r_fake.json(), (
        f"两种情况的响应体不一致：\n"
        f"  别人的通知：{r_real.json()}\n"
        f"  不存在的  ：{r_fake.json()}\n"
        f"→ 任何差异都会被用来探测数据是否存在。"
    )


# ==================== 五、正角色对照（没有它，接口全坏也是全绿）====================
# 第 1~4 节全都是"必须失败"。如果接口彻底坏掉、对任何 id 都返回 400
# 「消息不存在」，上面所有用例都会通过 —— 这是最容易被忽略的假绿。
# 所以必须有这组：本人操作自己的通知，必须成功，而且状态真的变了。

def test_owner_can_mark_own_notification_read(api, notification_pair):
    """A 标记自己的通知 → 200，且列表里 isRead 变 1、readTime 有值。"""
    nid = notification_pair["add"]("A 的私有通知")
    owner = notification_pair["owner"]

    api.assert_ok(api.notification.mark_read(nid, headers=owner["headers"]),
                  "本人标记已读应成功")

    item = _find(_list(api, owner), nid)
    assert item is not None, "标记已读成功了，但列表里找不到这条通知"
    assert item["isRead"] == 1, f"标记已读返回 200，但 isRead 还是 {item['isRead']}"
    assert item["readTime"] is not None, "标记已读返回 200，但 readTime 没写入"


def test_owner_can_delete_own_notification(api, notification_pair):
    """A 删除自己的通知 → 200，且之后列表里不再出现。"""
    nid = notification_pair["add"]("A 的私有通知")
    owner = notification_pair["owner"]

    api.assert_ok(api.notification.delete(nid, headers=owner["headers"]),
                  "本人删除通知应成功")

    assert _find(_list(api, owner), nid) is None, (
        "删除返回 200，但这条通知还在收件箱里 —— 删除没生效。"
    )


# ==================== 六、列表隔离 ====================

def test_list_does_not_include_other_users_notifications(api, notification_pair):
    """A 的列表里不能出现 B 的通知，反之亦然。"""
    mine = notification_pair["add"]("A 的私有通知")
    theirs = notification_pair["add"]("B 的私有通知", who="intruder")

    owner_ids = {n["id"] for n in _list(api, notification_pair["owner"])}
    intruder_ids = {n["id"] for n in _list(api, notification_pair["intruder"])}

    assert mine in owner_ids, "A 看不到自己的通知"
    assert theirs not in owner_ids, (
        f"A 的列表里出现了 B 的通知 id={theirs} —— 收件箱串号，这是数据泄漏。"
    )
    assert theirs in intruder_ids, "B 看不到自己的通知"
    assert mine not in intruder_ids, (
        f"B 的列表里出现了 A 的通知 id={mine} —— 收件箱串号，这是数据泄漏。"
    )


def test_list_excludes_deleted_notifications(api, notification_pair):
    """已软删除的通知不应出现在列表里。"""
    nid = notification_pair["add"]("已删除的通知", is_deleted=1)

    assert _find(_list(api, notification_pair["owner"]), nid) is None, (
        "is_deleted=1 的通知仍然出现在列表里 —— 软删除形同虚设。"
    )


def test_list_is_ordered_by_create_time_desc(api, notification_pair):
    """列表按时间倒序（新的在前）—— 实测后端的 orderByDesc("create_time")。"""
    older = notification_pair["add"]("一小时前的", age_seconds=3600)
    newer = notification_pair["add"]("刚刚的", age_seconds=0)

    ids = [n["id"] for n in _list(api, notification_pair["owner"])]

    assert ids.index(newer) < ids.index(older), (
        f"列表没有按时间倒序：新的 id={newer} 排在旧的 id={older} 后面。\n"
        f"→ 实际顺序：{ids}"
    )


# ==================== 七、未登录 ====================
# 三个接口都不该在没身份的情况下工作。401 的响应体是空的（全站实测如此），
# 所以这里只验 HTTP 状态，不验文案 —— 见 api.assert_error 的注释。

@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.notification.list_mine(),
        lambda api: api.notification.mark_read(1),
        lambda api: api.notification.delete(1),
    ],
    ids=["列表", "标记已读", "删除"],
)
def test_notification_endpoints_require_token(api, call):
    """不带 token 调通知接口 → 401。"""
    api.assert_error(call(api), 401, http=401)


# ==================== 八、id 参数形态 ====================
# 这一节的定位是"别 500"。路径参数是 Long，非法值会在进业务代码之前
# 被 Spring 拦掉 —— 拦掉是好事，但不能让它变成 500（那会暴露堆栈、且监控告警）。

@pytest.mark.parametrize("bad_id", [-1, 0], ids=["负数", "零"])
def test_negative_or_zero_id_returns_400(api, notification_pair, bad_id):
    """负数 / 0 这种合法 Long、但不可能存在的 id → 400「消息不存在」。"""
    resp = api.notification.mark_read(bad_id, headers=notification_pair["owner"]["headers"])

    api.assert_error(resp, 400, NOT_FOUND)


@pytest.mark.xfail(
    strict=True,
    reason="缺陷#12：路径参数类型转换失败时走 Spring 默认错误体，不是统一信封 {code,message}",
)
@pytest.mark.parametrize("bad_id", ["abc", "1.5"], ids=["非数字", "小数"])
def test_malformed_id_uses_unified_error_envelope(api, notification_pair, bad_id):
    """HTTP 400 是对的，但响应体形状不对。

    ══ 实测的两种 400 ══
      id=-1 / id=0  → {"code":400,"message":"消息不存在"}          ← 统一信封
      id=abc / 1.5  → {"timestamp":...,"status":400,                ← Spring 默认体
                       "error":"Bad Request","path":"..."}

    前端是统一按 body.message 弹提示的，第二种情况下拿到的是 undefined，
    用户看到的是**空白报错**。这和管理端 403 那个缺陷（缺陷#10）同源：
    都是在进入 Controller 之前就被框架拦掉了，绕过了统一信封。

    为什么用 xfail(strict=True) 而不是直接断言"必须是 Spring 默认体"：
      后者等于把缺陷钉成正确答案，哪天修好了测试反而红。
      strict 的语义是"我知道它现在坏的，修好了请提醒我删掉这条"。
    """
    resp = api.notification.mark_read(bad_id, headers=notification_pair["owner"]["headers"])

    assert resp.status_code == 400
    body = resp.json()
    assert "code" in body and "message" in body, (
        f"非法 id「{bad_id}」返回的不是统一信封，实际 body：{body}\n"
        f"→ 前端按 body.message 解析会拿到 undefined，用户看到空白错误提示。"
    )
