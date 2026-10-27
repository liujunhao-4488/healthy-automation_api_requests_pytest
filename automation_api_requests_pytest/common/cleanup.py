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


def _hard_delete_user(user_id):
    """删临时账号及其孩子的数据 —— 顺序必须孩子 → 家长（外键 RESTRICT）。"""
    db.execute(
        "DELETE FROM `assistant_message` WHERE `conversation_id` IN "
        "(SELECT `id` FROM `assistant_conversation` WHERE `user_id` = %s)",
        (user_id,),
    )
    db.execute("DELETE FROM `assistant_conversation` WHERE `user_id` = %s", (user_id,))
    db.execute("DELETE FROM `health_info_history` WHERE `user_id` = %s", (user_id,))
    db.execute("DELETE FROM `health_info` WHERE `user_id` = %s", (user_id,))
    db.execute("DELETE FROM `diet_goal` WHERE `user_id` = %s", (user_id,))
    db.execute("DELETE FROM `user` WHERE `id` = %s", (user_id,))


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
            _hard_delete_user(user_id)
            unregister_user(user_id)
        except Exception as exc:
            failures.append(("user", user_id, exc))

    return failures
