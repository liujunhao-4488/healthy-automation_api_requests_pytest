# test_cases/user/conftest.py
# 通知越权（IDOR）用例的专用夹具。
#
# ============ 为什么需要"两个真账号" ============
# 越权测试最容易写成假的写法是：拿一个不存在的 id 去访问。
#   PUT /notification/read/999999999  → 400"消息不存在"
# 这条永远绿，但它证明不了任何事 —— 后端完全可以在查库之前就把 id 拒掉，
# 归属校验整段删掉它照样绿。
#
# 真正要验证的是「通知**确实存在**，但不是你的」这种情况，只有它能触发
# NotificationController 第 81 行那句：
#     !userId.equals(notification.getUserId())
# 所以必须造两个真账号：owner 有自己的通知，intruder 拿 owner 的通知 id 去操作。
#
# ============ 为什么两个账号都是新注册的，不用主测试账号 ============
# GET /notification/list 里调了 ensureDefaultNotifications()，会给
# 「有饮食目标 / 有饮食记录 / 有推荐文章」的账号**自动插入通知**。
# 主测试账号带着这些数据，list 里会凭空多出几条 —— 断言就没法写死了
# （"列表里有几条"这个数字每次都可能不一样）。
# 新注册账号什么都没有，list 的内容 100% 由本夹具决定。

import uuid

import pytest

from common import cleanup, db


def _register(api, prefix):
    """注册一个一次性账号，返回 userId / email / 带 token 的请求头。"""
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


def _add_notification(user_id, title, is_read=0, is_deleted=0, age_seconds=0):
    """直接往库里插一条通知，返回它的 id。

    为什么不走接口造：后端没有"给自己发通知"的接口（/admin/publish 要管理员），
    唯一能造通知的途径就是 list 触发的自动通知 —— 那个内容不可控。
    所以靶子数据直接插库，这是造数据，不是绕过接口做断言。
    """
    with db.transaction() as cur:
        cur.execute(
            "INSERT INTO notification "
            "(user_id, type, title, content, is_read, is_deleted, send_time, create_time) "
            "VALUES (%s, 'system', %s, '越权用例靶子', %s, %s, "
            "        DATE_SUB(NOW(), INTERVAL %s SECOND), DATE_SUB(NOW(), INTERVAL %s SECOND))",
            (user_id, title, is_read, is_deleted, age_seconds, age_seconds),
        )
        return cur.lastrowid


@pytest.fixture
def notification_pair(api):
    """造一对真账号 + 一个造通知的小工具。

    用法：
        nid = notification_pair["add"]("A 的通知")            # 给 owner 造
        nid = notification_pair["add"]("B 的", who="intruder") # 给 intruder 造
        api.notification.mark_read(nid, headers=notification_pair["intruder"]["headers"])

    用完自动清理两个账号（含通知）。清理走 cleanup.purge_user()：
    删 → 回查确认 → 真删掉了才注销登记，删不干净会抛异常而不是静默放过。
    """
    owner = _register(api, "ntf_owner_")
    intruder = _register(api, "ntf_intr_")

    # ⚠️ 登记必须紧跟注册，不能等到自检之后。
    #    自检是一句 assert，失败时夹具就地中断 —— 生成器走不到 yield，
    #    teardown 整段不执行，这两个账号就成了**没人认领的孤儿**：
    #    连会话收尾兜底都救不回来（它只回收登记过的）。
    #    实测踩过：变异验证时自检故意报错，当场漏下 2 个账号。
    for u in (owner, intruder):
        cleanup.register_user(u["userId"], u["email"])

    def add(title, is_read=0, is_deleted=0, age_seconds=0, who="owner"):
        target = owner if who == "owner" else intruder
        return _add_notification(target["userId"], title, is_read, is_deleted, age_seconds)

    # ---- 夹具自检：造的通知必须真的能被后端读到 ----
    # 防的是最阴的一种假绿：通知插进库了，但后端的 list 读不出来。
    # 这时所有越权用例都会得到 400「消息不存在」—— 看起来全部通过，
    # 实际上一条都没测到（因为"越权被拒"和"这通知根本不存在"长得一模一样）。
    #
    # ⚠️ 它能挡什么、不能挡什么（别把话说大）：
    #   挡得住：后端加了额外过滤条件（比如只返回 type != 'system'）、
    #           读写分离读到了从库、list 的 SQL 被人改坏。
    #   挡不住：后端连错库 —— 那种情况下面这句 INSERT 会先撞外键
    #           （notification.user_id → user.id，新账号只在测试库里），
    #           轮不到自检出手，报错位置在插入那行。
    probe_id = add("__fixture_probe__")
    body = api.assert_ok(
        api.notification.list_mine(headers=owner["headers"]),
        "owner 读取通知列表应成功",
    )
    visible = {n["id"] for n in (body.get("data") or [])}
    assert probe_id in visible, (
        f"夹具自检失败：刚插的通知 id={probe_id} 在 owner 的列表里查不到。\n"
        f"→ 这时所有越权断言都会得到 400「消息不存在」，和「通知真的不存在」长得一样，\n"
        f"  整套用例会**全部假绿**。\n"
        f"→ 常见原因：list 的 SQL 加了额外过滤（比如排除 system 类型）、\n"
        f"  读写分离读到了还没同步的从库、或者后端改了列表逻辑。\n"
        f"→ 先手工调一次 GET /notification/list，看刚造的数据为什么不出现。"
    )
    db.execute("DELETE FROM notification WHERE id = %s", (probe_id,))

    yield {"owner": owner, "intruder": intruder, "add": add}

    for u in (owner, intruder):
        cleanup.purge_user(u["userId"])
