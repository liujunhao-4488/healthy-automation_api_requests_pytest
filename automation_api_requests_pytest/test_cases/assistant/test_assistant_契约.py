# test_cases/assistant/test_assistant_契约.py
# 【任务：AI 助手四个接口的**结构契约**】
#
# ══ 和老文件的分工 ═══════════════════════════════════════════════════
#   老文件（意图识别 / 意图标签 / 安全拦截 / 越狱 …）
#       验「模型说了什么」：意图判对没、该拒的拒了没、有没有幻觉
#   本文件
#       验「壳子长什么样」：字段齐不齐、类型对不对、列表和详情的形状是否一致
#
#   分开的意义：模型那条线本来就飘（同一句话两次回复措辞不同），
#   混进"字段类型"这种硬约束一起跑，红了会分不清是模型的锅还是序列化的锅。
#
# ══ 成本提示 ═════════════════════════════════════════════════════════
#   test_chat_shape 会**真调一次模型**（约几秒）。这是唯一一条花钱的用例，
#   其余几条都是纯读接口或参数校验，不碰模型。
#   用 `-k "not chat_shape"` 可以跳过它。

import pytest

from common import cleanup
from common.schemas import (
    CHAT_SCHEMA,
    CONVERSATION_LIST_SCHEMA,
    MESSAGE_LIST_SCHEMA,
    check,
)

# chat 用例会建会话，收尾要直接删库；数据库不可用时由根 conftest 跳过。
pytestmark = pytest.mark.requires_db


@pytest.fixture
def chat_conversations(api, auth_headers):
    """登记本用例创建的会话，跑完先走接口软删、再硬删库里的行。"""
    ids = []
    yield ids
    cleanup.delete_conversations(api, auth_headers, ids)


# ==================== 聊天 ====================

def test_chat_shape(api, auth_headers, chat_conversations):
    """POST /assistant/chat → data 里 5 个部分，每个部分各自的字段都要齐。

    这个接口的响应是全场最复杂的，值得逐块看：
      · userMessage      用户消息：没有 source / intent / ragUsed
      · assistantMessage 助手回复：**多** source / intent / ragUsed / retrievalStatus / sources
      · conversationId   会话 id
      · conversation     会话摘要（标题、条数、最后消息时间）
      · contextMessage   正常对话时是 null

    ⚠️ 两者形状不同是**故意的**，不是漏写。若拿同一份 schema 套两边，必有一边红。
    """
    resp = api.assistant.chat({"rawPrompt": "每天喝多少水合适"}, headers=auth_headers)

    # 先把 conversationId 摘出来登记：哪怕下面的断言行挂了，收尾也能把会话删掉
    try:
        cid = (resp.json().get("data") or {}).get("conversationId")
    except ValueError:
        cid = None
    if cid:
        chat_conversations.append(cid)
        cleanup.register_conversation(cid)

    body = api.assert_ok(resp, "发送消息应成功", schema=CHAT_SCHEMA)

    # 语义补充：schema 只保证 intent 是字符串，不保证是空串
    assistant = body["data"]["assistantMessage"]
    assert assistant["text"].strip(), "助手回复不该是空文本"
    assert assistant["intent"].strip(), "intent 不该是空串（前端拿它选展示样式）"


def test_chat_empty_content_is_rejected(api, auth_headers):
    """空内容 → 400「请输入聊天内容」。

    精简版 assert_error 的样板：这以前要写三行。
    """
    resp = api.assistant.chat({"rawPrompt": "", "prompt": ""}, headers=auth_headers)

    api.assert_error(resp, 400, "请输入聊天内容")


def test_chat_with_unknown_conversation_is_rejected(api, auth_headers):
    """带一个不存在的 conversationId → 400「会话不存在或无权访问」。

    ⚠️ 注意文案里有"或无权访问"—— 后端**故意**不区分"不存在"和"是别人的"，
       免得泄露"这个 id 存在"这一信息。这句话本身就是安全设计，钉住它。
    """
    resp = api.assistant.chat(
        {"rawPrompt": "你好", "conversationId": 99999999},
        headers=auth_headers,
    )

    api.assert_error(resp, 400, "会话不存在或无权访问")


# ==================== 会话列表 / 消息列表 ====================

def test_conversation_list_shape(api, auth_headers):
    """GET /assistant/conversations → 数组，每个会话 7 个字段。"""
    resp = api.assistant.list_conversations(headers=auth_headers)

    api.assert_ok(resp, "获取会话列表应成功", schema=CONVERSATION_LIST_SCHEMA)


def test_message_list_shape(api, auth_headers):
    """GET /conversations/{id}/messages → 数组，每个元素 6 个基础字段。

    ⚠️ 这里的元素**比 chat 响应里的少 5 个字段**（没有 intent / ragUsed / sources…）。
       同一个"消息"在两个接口里长两个样 —— 实测确认，不是 bug。
       所以"想看模型判了什么意图"只能查 chat 的响应，列表接口查不到。
    """
    conversations = api.assert_ok(
        api.assistant.list_conversations(headers=auth_headers), "获取会话列表应成功"
    )["data"]

    if not conversations:
        # 没有会话就没什么可验的。用 pytest.skip 而不是"假装通过"——
        # 假绿会让人以为这条一直在守着，其实一次都没跑过。
        import pytest
        pytest.skip("该账号还没有任何会话，消息列表无可验；先跑一次 chat 用例再来")

    resp = api.assistant.list_messages(conversations[0]["id"], headers=auth_headers)

    body = api.assert_ok(resp, "获取消息列表应成功", schema=MESSAGE_LIST_SCHEMA)
    assert body["data"], "刚取到的会话不该一条消息都没有"


def test_message_list_keeps_six_fields_only(api, auth_headers):
    """把"列表元素少 5 个字段"这件事**主动钉住**，而不是等 schema 红了才发现。

    做法：用 chat 的 ASSISTANT_MESSAGE 去套列表元素，**应该失败**。
    这条如果哪天通过了，说明后端给列表接口补上了 intent / ragUsed ——
    那是好事，但也意味着上面那条 MESSAGE_LIST_SCHEMA 该跟着放宽，
    不能默默变强而没人知道。
    """
    conversations = api.assert_ok(
        api.assistant.list_conversations(headers=auth_headers), "获取会话列表应成功"
    )["data"]
    if not conversations:
        import pytest
        pytest.skip("该账号还没有任何会话")

    messages = api.assert_ok(
        api.assistant.list_messages(conversations[0]["id"], headers=auth_headers),
        "获取消息列表应成功",
    )["data"]

    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    if not assistant_msgs:
        import pytest
        pytest.skip("这个会话里没有助手消息")

    from common.schemas import ASSISTANT_MESSAGE

    try:
        check(assistant_msgs[0], ASSISTANT_MESSAGE, label="列表里的助手消息")
    except AssertionError:
        return      # 预期路径：列表元素确实没有那 5 个字段

    raise AssertionError(
        "列表接口突然开始返回 intent / ragUsed / sources 了 —— "
        "这本身是好事，但要同步改 MESSAGE_LIST_SCHEMA，否则两条 schema 打架。"
    )


# ==================== 鉴权 ====================

def test_assistant_endpoints_reject_without_token(api):
    """不带 token → 401（和 health / user 一个口径）。"""
    api.assert_error(api.assistant.list_conversations(), 401, http=401)
