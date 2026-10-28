# common/cleanup.py
# 【数据生命周期】进程级清理登记表：创建时登记，会话收尾兜底回收。
#
# 为什么需要它：
#   现在的清理靠每个夹具自己写 yield teardown —— 正常/失败都会执行，
#   但夹具写漏了、或清理到一半抛异常，就会留下数据，而且没人知道。
#   这里加一层登记表：夹具创建资源时登记，正常清完就注销；
#   会话结束时把仍然登记的再删一次。
#
# ⚠️ 只回收**本进程登记过**的资源，不按 username 前缀扫全库：
#   xdist 多 worker 同时在跑，扫全库会把别的 worker 正在用的临时账号删掉；
#   前缀也不是安全边界，真实用户完全可能叫 hx_xxx。

import logging
import threading

from common import db

log = logging.getLogger("cleanup")

_lock = threading.Lock()
_users = {}            # userId -> email（email 只用于日志）
_conversations = set()


# ==================== 登记 / 注销 ====================

def register_user(user_id, email=None):
    with _lock:
        _users[user_id] = email


def unregister_user(user_id):
    with _lock:
        _users.pop(user_id, None)


def register_conversation(conversation_id):
    with _lock:
        _conversations.add(conversation_id)


def unregister_conversations(ids):
    with _lock:
        _conversations.difference_update(ids)


# ==================== 硬删除 ====================

def hard_delete_conversations(ids):
    """按会话 id 硬删消息 + 会话（软删除只是 is_deleted=1，行还在）。"""
    ids = list(dict.fromkeys(ids))       # 去重，顺便保持顺序
    if not ids:
        return
    marks = ",".join(["%s"] * len(ids))
    db.execute(
        f"DELETE FROM `assistant_message` WHERE `conversation_id` IN ({marks})",
        tuple(ids),
    )
    db.execute(
        f"DELETE FROM `assistant_conversation` WHERE `id` IN ({marks})",
        tuple(ids),
    )


# 引用 `user` 的子表，以及挂在子表下面的**孙表** —— 顺序即删除顺序：孙 → 子 → 父。
#
# ⚠️ 这份清单必须写全，原因：这些外键**全是 ON DELETE RESTRICT**（不是 CASCADE）。
#    少删任何一张，最后那句 DELETE FROM user 就会抛 IntegrityError(1451)，
#    于是账号和它的子数据一起留在库里。实测踩过：原来只删 3 张表，
#    带 diet_record / notification 的临时账号一个都删不掉；
#    而且 diet_record 自己还有孙表 diet_record_detail，漏了它一样删不动。
#
# 每条 WHERE 里的 %s 都填 userId。
# 怎么核对这份清单（库里加新表时必须重跑）：
#   SELECT k.TABLE_NAME, k.COLUMN_NAME, k.REFERENCED_TABLE_NAME, rc.DELETE_RULE
#   FROM information_schema.KEY_COLUMN_USAGE k
#   JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
#     ON rc.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
#    AND rc.CONSTRAINT_NAME  = k.CONSTRAINT_NAME
#   WHERE k.TABLE_SCHEMA = DATABASE() AND k.REFERENCED_TABLE_NAME IS NOT NULL;
_USER_CHILD_DELETES = [
    # ---- 孙表：它们的父表本身要被删，所以得抢在前面 ----
    ("diet_record_detail",
     "`record_id` IN (SELECT `id` FROM `diet_record` WHERE `user_id` = %s)"),
    ("recipe_ingredient",
     "`recipe_id` IN (SELECT `id` FROM `recipe` WHERE `creator_id` = %s)"),
    # ---- 子表 ----
    ("assistant_conversation", "`user_id` = %s"),
    ("health_info_history", "`user_id` = %s"),
    ("health_info", "`user_id` = %s"),
    ("diet_record", "`user_id` = %s"),
    ("diet_goal", "`user_id` = %s"),
    ("user_diet_preference", "`user_id` = %s"),
    ("user_article_collect", "`user_id` = %s"),
    ("user_article_like", "`user_id` = %s"),
    ("user_read_record", "`user_id` = %s"),
    ("user_recipe_collect", "`user_id` = %s"),      # 必须排在 recipe 前面
    ("article_comment", "`user_id` = %s"),
    ("notification", "`user_id` = %s"),
    ("recipe", "`creator_id` = %s"),
]


def _delete_user_messages(user_id):
    """删临时账号的消息。

    assistant_message 有两根外键（user_id、conversation_id），所以它不放进
    上面那张普通清单，单独处理：
      · 按 conversation_id 删 —— 越权用例可能把**别人的**消息写进了它的会话，
        那条消息的 user_id 不是它，只按 user_id 删会漏，接着删会话时会被
        fk_assistant_message_conversation 挡住；
      · 按 user_id 删 —— 它自己写在**别人**会话里的消息（越权真的失守时会有）。
    两条都要，缺一条就删不干净。
    """
    db.execute(
        "DELETE FROM `assistant_message` WHERE `user_id` = %s OR `conversation_id` IN "
        "(SELECT `id` FROM `assistant_conversation` WHERE `user_id` = %s)",
        (user_id, user_id),
    )


def _hard_delete_user(user_id):
    """删临时账号及其孩子的数据 —— 顺序必须孩子 → 家长（外键 RESTRICT）。

    只负责"删"，**不负责验证**。要"删了而且确认没了"请用 purge_user()。
    """
    _delete_user_messages(user_id)
    for table, where in _USER_CHILD_DELETES:
        db.execute(f"DELETE FROM `{table}` WHERE {where}", (user_id,))
    db.execute("DELETE FROM `user` WHERE `id` = %s", (user_id,))


def _user_exists(user_id):
    row = db.query(
        "SELECT COUNT(*) AS n FROM `user` WHERE `id` = %s", (user_id,), one=True
    )
    return row["n"] > 0


# ==================== 临时账号：删 + 验证 + 注销（夹具统一走这个）====================
#
# ══ 为什么不能只用 db.execute("DELETE ...") ══
# 原来各夹具自己写一句 DELETE，然后无条件 unregister_user()。这个组合有两个坑：
#
#   坑 1：只看 affected，或者干脆不看。
#         affected=0 有两种含义 —— "本来就没有" 和 "我删的不是它所在的库"。
#         两种都被当成"删完了"，一声不响。
#
#   坑 2：不管删没删掉都注销登记表。
#         注销 = 告诉会话收尾"这个我处理好了，别再管"。
#         于是兜底也捞不到它，垃圾永久留下。
#         实测后果：开发库里堆了 65 个 hx_ 账号，跑了几十轮没人发现。
#
# 这个函数把三件事绑成一件：**删 → 回查 → 真删掉了才注销**。
# 于是登记表有了一条能复述的不变量：**还留在表里的 = 还没确认清干净的**。

def purge_user(user_id, strict=True):
    """硬删临时账号（含全部子数据），回查确认，并从登记表注销。

    返回：
        True  = 删之前存在，现在已确认删干净
        False = 删之前库里就没有（只有 strict=False 才会返回，见下）

    strict=True（夹具默认）时，"库里本来就没有"也当异常：
        后端注册成功返回了 userId，我这边却查不到 —— 说明**后端写进去的库
        和这里删的库不是同一个**。账号正在后端那个库里越积越多，
        这时候最该做的是报出来，而不是假装清完了。

    抛出异常的场景（两种都**不注销**登记，留给会话收尾再试一次）：
        · DELETE 本身失败（多半是 1451，有子表没删干净）；
        · DELETE 成功但回查还在。
    """
    if not _user_exists(user_id):
        unregister_user(user_id)          # 没人可回收，别让兜底反复空跑
        if strict:
            raise RuntimeError(
                f"临时账号 userId={user_id} 在测试库里查不到 —— 但它是接口注册成功的。\n"
                f"→ 说明**后端连的库和测试连的库不是同一个**："
                f"后端写进 A 库，我去 B 库删。\n"
                f"→ 这个账号会留在后端那个库里，得人工清；"
                f"先确认两边库名一致（启动后端时 DB_NAME 要对）。"
            )
        return False

    try:
        _hard_delete_user(user_id)
    except Exception as exc:
        raise RuntimeError(
            f"删除临时账号 userId={user_id} 失败：{exc}\n"
            f"→ 1451 = 还有子表引用它（外键是 RESTRICT，不会级联删）。\n"
            f"→ 去补 common/cleanup.py 里的 _USER_CHILD_DELETES 清单，"
            f"上面那条失败的 DELETE 就是漏掉的那张表。"
        ) from exc

    # 回查：这才是"删掉了"的证据。不查等于相信刚才那条 DELETE 的手气。
    if _user_exists(user_id):
        raise RuntimeError(
            f"临时账号 userId={user_id} 的 DELETE 执行完了，但回查**它还在**。\n"
            f"→ 检查是不是连了只读账号，或者有触发器把删除挡了。"
        )

    unregister_user(user_id)
    return True


# ==================== 夹具用的统一收尾 ====================

def delete_conversations(api, headers, ids):
    """夹具收尾：先走接口软删（和产品行为一致），再硬删库里的行。

    ⚠️ 即使接口软删失败，也要把库里的行硬删掉 —— 否则数据会越跑越多；
    接口错误会在最后重新抛出来，不会把"删除接口坏了"悄悄吞掉。
    """
    ids = list(dict.fromkeys(ids))
    if not ids:
        return

    api_errors = []
    for cid in ids:
        try:
            api.assistant.delete_conversation(cid, headers=headers)
        except Exception as exc:        # 连接失败 / 超时；4xx 不会抛，只返回响应
            api_errors.append((cid, exc))

    # 硬删失败就不注销，留给会话收尾再试一次
    hard_delete_conversations(ids)
    unregister_conversations(ids)

    if api_errors:
        cid, exc = api_errors[0]
        raise AssertionError(f"接口软删会话 {cid} 失败：{exc}") from exc


# ==================== 会话收尾兜底 ====================

def cleanup_all():
    """把仍然登记的资源再删一次；返回失败清单（空 = 全部回收）。

    只处理本进程登记过的：
      · 正常路径：夹具已经删掉并注销 → 这里什么都不做；
      · 兜底路径：夹具漏清 / 清理中途抛异常 → 这里补一刀。
    """
    with _lock:
        users = list(_users)
        conversations = list(_conversations)

    failures = []

    if conversations:
        try:
            hard_delete_conversations(conversations)
            unregister_conversations(conversations)
        except Exception as exc:
            failures.append(("conversation", conversations, exc))

    for user_id in users:
        try:
            # strict=False：兜底这一步，"库里已经没有了"属正常（可能夹具刚删完、
            # 也可能人工清过），不该记成失败。但删不干净照样会被记进 failures。
            purge_user(user_id, strict=False)
        except Exception as exc:
            failures.append(("user", user_id, exc))

    return failures
