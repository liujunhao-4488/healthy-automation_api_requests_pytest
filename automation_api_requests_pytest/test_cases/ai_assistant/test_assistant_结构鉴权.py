# test_cases/ai_assistant/test_assistant_结构鉴权.py
# 【任务：AI 助手 · /assistant/*】—— AI 测试的主战场，也是这个文件"长得不一样"的原因。
#
# 为什么它和别的用例文件不一样？
#   别的接口是"输入 → 固定输出"：assert resp.json()["data"] == 期望值 就完事。
#   这个接口的输出是**一段自然语言**，你没法断言它等于什么。
#
# 所以这里的断言分成三种：
#   ① **断结构** —— 字段齐不齐、类型对不对。这部分能精确断言，先测满。
#   ② **断行为** —— 该拒绝的有没有拒绝。用**负面断言**："不该出现 XX"。
#   ③ **断不了的钉住** —— 已知缺陷用 xfail 固化，等后端修（和 health / user 一个套路）。
#
# 期望值全部来自 2026-10-10 实测，不靠猜。
#
# ⚠️ 两个前提，换环境要重新确认：
#   1. 本机后端**没配 DeepSeek key**，走的是本地兜底分支
#      （RecipeServiceImpl.getIngredientSubstitutes → buildLocalAssistantCards），
#      输出是**确定性的模板文本**，跑得也快。配了 key 之后断言要对一下。
#   2. 每聊一句都会在库里建会话——所以统一用 conftest 的 ask / conversation 夹具，
#      跑完自动清场，不留垃圾数据。

import pytest

from common import cleanup

# 意图识别（"问什么该走哪条分支"）**不在本文件** —— 见 test_assistant_意图识别.py。
# 本文件只管结构 / 鉴权 / 参数校验。


# ==================== 鉴权 ====================

def test_chat_without_token(api):
    """/assistant/chat 必须带 token：不带 → 401，且响应体是空的。"""
    resp = api.assistant.chat({"rawPrompt": "你好"})
    assert resp.status_code == 401, f"无 token 应 401，实际 {resp.status_code}"
    assert resp.text == "", f"401 响应体应为空，实际 {resp.text!r}"


def test_conversations_without_token(api):
    """会话列表同样要 token → 401 + 空体。"""
    resp = api.assistant.list_conversations()
    assert resp.status_code == 401, f"无 token 应 401，实际 {resp.status_code}"
    assert resp.text == ""


# ==================== 参数校验 ====================

@pytest.mark.parametrize("payload", [{"rawPrompt": ""}, {"prompt": ""}, {}],
                         ids=["rawPrompt为空", "prompt为空", "空body"])
def test_chat_empty_content(api, auth_headers, payload):
    """rawPrompt 和 prompt 都给不出内容 → 400「请输入聊天内容」。

    后端逻辑：rawPrompt 空就退回读 prompt，两个都空才报错。
    """
    resp = api.assistant.chat(payload, headers=auth_headers)

    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}"
    body = resp.json()
    assert body["code"] == 400, f"期望 code=400，实际 {body.get('code')}"
    assert body["message"] == "请输入聊天内容", f"实际 message={body.get('message')!r}"


def test_chat_with_unknown_conversation(api, auth_headers):
    """传一个不存在的 conversationId → 400「会话不存在或无权访问」。

    ⚠️ 这条**不测越权**，别被报错文案骗了：
       999999 在库里根本不存在，后端走到 `selectById` 返回 null 就抛了，
       `!userId.equals(conversation.getUserId())` 那半个条件**从来没被执行过**。
       所以它证明不了"别人的会话进不来"。

    真正的越权（会话**存在**、但属于别人）在 test_assistant_越权.py，
    那边用另一个真实账号的 conversationId 测——只有这种样本才能证明归属校验生效。

    它留在本文件，是因为它的关注点其实是**资源参数校验**：
    给一个指向空资源的 id，应该规规矩矩 400，而不是 NPE 变 500。
    """
    resp = api.assistant.chat({"conversationId": 999999, "rawPrompt": "你好"},
                              headers=auth_headers)

    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}"
    assert resp.json()["message"] == "会话不存在或无权访问"


# ==================== 正常流程：断结构 ====================

def test_chat_response_structure(ask):
    """一条正常聊天 → data 就是这 5 个字段，assistantMessage 结构完整。

    这是"断不了内容就断结构"的样板：答什么管不了，**答的格式必须守约**。
    """
    data = ask("我能吃海虾吗")

    assert set(data) == {"conversationId", "conversation", "userMessage",
                         "contextMessage", "assistantMessage"}, \
        f"data 字段与预期不符：{sorted(data)}"

    am = data["assistantMessage"]
    for key in ("id", "role", "text", "messageType", "cards", "createTime"):
        assert key in am, f"assistantMessage 缺字段 {key}"

    assert am["role"] == "assistant", f"role 应是 assistant，实际 {am['role']!r}"
    assert am["messageType"] in ("text", "cards"), \
        f"messageType 只该是 text / cards，实际 {am['messageType']!r}"
    assert isinstance(am["cards"], list), "cards 应是数组"
    assert isinstance(am["text"], str) and am["text"].strip(), \
        f"回答内容不该为空，实际 {am['text']!r}"


def test_chat_persists_both_messages(api, auth_headers, ask):
    """聊一句 → 库里要留下"先问后答"两条，且问题原文没走样。"""
    cid = ask("我能吃海虾吗")["conversationId"]

    messages = api.assert_ok(api.assistant.list_messages(cid, headers=auth_headers))["data"]

    assert [m["role"] for m in messages] == ["user", "assistant"], \
        f"消息角色顺序不对：{[m['role'] for m in messages]}"
    assert messages[0]["text"] == "我能吃海虾吗", "存下来的应该是问题原话"


def test_chat_appends_to_same_conversation(api, auth_headers, ask):
    """带上 conversationId 再聊 → 追加到同一个会话，消息数累加。"""
    cid = ask("我能吃海虾吗")["conversationId"]

    second = ask("那鸡胸肉呢", cid)

    assert second["conversationId"] == cid, "应复用同一个会话，不该新建"
    assert second["conversation"]["messageCount"] == 4, \
        f"两轮问答应有 4 条消息，实际 {second['conversation']['messageCount']}"

    messages = api.assert_ok(api.assistant.list_messages(cid, headers=auth_headers))["data"]
    assert len(messages) == 4


def test_create_conversation_default_title(conversation):
    """不传标题建会话 → 标题回落成「AI 助手会话」，且初始消息数为 0。"""
    assert conversation["title"] == "AI 助手会话", f"实际标题 {conversation['title']!r}"
    assert conversation["messageCount"] == 0, f"实际 {conversation['messageCount']}"


def test_deleted_conversation_disappears(api, auth_headers):
    """删掉的会话不再出现在列表里（软删除：库里还在，但接口不再返回）。

    用例自己建、自己删；最后的硬删是为了不把 is_deleted=1 的行留在库里。
    """
    created = api.assert_ok(api.assistant.create_conversation({}, headers=auth_headers))["data"]
    cid = created["id"]
    cleanup.register_conversation(cid)      # 断言中途挂了也能兜底硬删

    listed = api.assert_ok(api.assistant.list_conversations(headers=auth_headers))["data"]
    assert any(c["id"] == cid for c in listed), "刚建的会话应该在列表里"

    api.assert_ok(api.assistant.delete_conversation(cid, headers=auth_headers))

    listed = api.assert_ok(api.assistant.list_conversations(headers=auth_headers))["data"]
    assert not any(c["id"] == cid for c in listed), "删掉的会话不该还留在列表里"

    # 接口软删只是 is_deleted=1；用例自己的产物自己硬删干净
    cleanup.hard_delete_conversations([cid])
    cleanup.unregister_conversations([cid])
