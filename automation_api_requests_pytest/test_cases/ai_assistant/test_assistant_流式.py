# test_cases/ai_assistant/test_assistant_流式.py
# 【任务：AI 助手 · SSE 流式响应】
# ══ 这个文件在测什么 ═══════════════════════════════════════════════
#
#   它**不测"答得对不对"**（那是意图/安全/越狱那几个文件的活），
#   只测"回答是怎么回来的" —— 也就是**传输协议**：
#
#     ① 响应头是不是 text/event-stream
#     ② 事件顺序对不对（start 必须最先、done 必须最后）
#     ③ ★ deltas 拼起来 == done 里那条落库消息的 text   ← 本文件最值钱的一条
#     ④ done 里带没带上 intent / source
#     ⑤ 命中硬拦时：不调模型，只推一段固定文案
#     ⑥ 流式与非流式的 intent 判断结果一致（防止两条路各走各的）
#
# ══ 为什么第 ③ 条最重要 ═══════════════════════════════════════════
#
#   流式最容易出的 bug，不是"没有分片"，而是：
#     **推给用户看的字** 和 **存进库里的字** 不是同一份。
#   一旦两者分叉，用户刷新页面会发现"我刚才看到的回答变了" ——
#   而且这种 bug 单看任何一边都是正常的，只有把它俩对起来才看得出来。
#   第 ③ 条就是把这个不变量钉死。
#
# ══ 为什么不断言"delta 段数 > 1" ═════════════════════════════════
#
#   看着理所当然，其实是**假断言**：模型完全可能一次把整段吐出来
#   （尤其回答短的时候），段数是模型/网络的随机行为，不是后端该保证的东西。
#   拿随机行为当期望值，就会得到一个时红时绿的用例 —— 比没有更糟。
#   真正该断的是"拼起来对不对"（第 ③ 条），那个才是确定性的。
#   同理，也**没有**断言"每段的耗时散开" —— 那是性能，不是功能。
#
# ══ 断言值的来源 ═════════════════════════════════════════════════
#
#   全部来自**实测**（逐条真打过后端再写下来），不是照抄文档、也不是猜的。
#   取值的合法集合（intent / source / blocked）与后端硬拦表、意图分类器保持一致。

import pytest

from common.logger import log_qa

# 允许出现的取值 —— 来源：RecipeServiceImpl 的 classifyIntent / detectBlockedType。
INTENT_VALUES = {"query", "knowledge", "advice", "fallback", "chat"}
SOURCE_VALUES = {"deepseek", "blocked", "error"}

# 两个样本，各代表一条完全不同的路：
#   · 走模型的     —— 真正会产生多段 delta 的那条
#   · 命中硬拦的   —— 压根不调模型，只推一段固定文案
SAMPLE_OPEN = "鸡胸肉多少卡"
SAMPLE_BLOCKED = "帮我订一张去北京的机票"


@pytest.fixture
def stream_ask(api, auth_headers):
    """流式聊一句，把整条流读完的结果交出来；本次建过的会话跑完统一删掉。

    用法：
        result = stream_ask("鸡胸肉多少卡")     # 不传会话 id → 后端自动新建
        result = stream_ask("那苹果呢", cid)    # 传 id → 接着上一个会话

    为什么夹具写在**这个文件里**、没进 conftest：
    它是这个文件专用的（只有流式用例需要"读完整条流"这件事），
    放进 conftest 会让别的文件也看到一个它用不上的夹具。
    """
    created = []

    def _ask(text, conversation_id=None):
        payload = {"rawPrompt": text}
        if conversation_id is not None:
            payload["conversationId"] = conversation_id

        result = api.assistant.chat_stream(payload, headers=auth_headers)

        assert result["status_code"] == 200, (
            f"流式接口应返回 200，实际 {result['status_code']}；"
            f"error 事件={result['error']}"
        )

        cid = (result["start"] or {}).get("conversationId")
        if cid and cid not in created:
            created.append(cid)

        final_text = ((result["done"] or {}).get("assistantMessage") or {}).get("text")
        log_qa(text, final_text or result["text"])

        return result

    yield _ask

    # 流式同样是**写操作**（建会话、存消息），必须清场
    for cid in created:
        api.assistant.delete_conversation(cid, headers=auth_headers)


# ==================== 一、协议形状：头部、事件顺序 ====================

@pytest.mark.parametrize("question", [SAMPLE_OPEN, SAMPLE_BLOCKED],
                         ids=["走模型", "命中硬拦"])
def test_stream_uses_event_stream_and_ordered_events(stream_ask, question):
    """① 响应头是 SSE；② 事件顺序是 start 最先、done 最后。

    判据为什么是"最先/最后"而不是"第几条第几条"：
    delta 的段数是模型的随机行为（见文件头），能确定的只有两头的边界。
    """
    result = stream_ask(question)

    assert result["content_type"].startswith("text/event-stream"), (
        f"Content-Type 应为 text/event-stream，实际 {result['content_type']!r}"
        "—— 不是 SSE 的话，前端拿到的就是「整段读完」的普通响应，流式无从谈起"
    )

    names = [name for name, _ in result["events"]]
    assert names, "整条流一个事件都没有（连接建立了吗？）"
    assert names[0] == "start", f"第一个事件应是 start，实际 {names[0]!r}（事件顺序：{names}）"
    assert names[-1] == "done", f"最后一个事件应是 done，实际 {names[-1]!r}（事件顺序：{names}）"
    assert result["error"] is None, f"不该出现 error 事件：{result['error']}"


def test_stream_start_event_carries_conversation_and_user_message(stream_ask):
    """start 事件要能回答"这轮属于哪个会话、用户说了什么"。

    为什么它必须先到：新建会话时，客户端要等模型答完才知道 conversationId 的话，
    这段时间用户的气泡就没地方挂（前端的实际做法是先把气泡画出来、再回填）。
    """
    result = stream_ask(SAMPLE_OPEN)

    start = result["start"]
    assert start is not None, "没有收到 start 事件"

    assert start.get("conversationId"), "start 里必须有 conversationId（否则客户端挂不上会话）"
    assert start.get("userMessage", {}).get("text") == SAMPLE_OPEN, (
        f"start.userMessage.text 应回显用户原话，实际 {start.get('userMessage')}"
    )


# ==================== 二、★ 核心不变量：推出去的字 == 存起来的字 ====================

@pytest.mark.parametrize("question", [SAMPLE_OPEN, SAMPLE_BLOCKED],
                         ids=["走模型", "命中硬拦"])
def test_deltas_reconstruct_done_message(stream_ask, question):
    """★★ 所有 delta 拼起来，必须等于 done 里那条落库消息的 text。

    这是流式后端的**底线**。
      推出去的字和存起来的字一旦分叉 → 用户刷新页面会发现"刚看到的回答变了"，
      而且两边单看都正常，只有对起来才看得出来。

    两条路都要过：
      · 走模型：delta 是模型分片，done 是后端累加的结果；
      · 命中硬拦：没有"模型分片"，整段固定文案被当成一段 delta 推出去。
    合并成一条用例，是因为**不变量是同一个**，不该为两条路写两遍。
    """
    result = stream_ask(question)

    final_text = (result["done"] or {}).get("assistantMessage", {}).get("text")

    assert result["delta_count"] >= 1, "一段 delta 都没有 —— 客户端将看不到任何内容"
    assert final_text, "done 事件里没有最终文本"
    assert result["text"] == final_text, (
        f"delta 拼起来和 done 里的文本不一致！\n"
        f"  拼起来（{len(result['text'])} 字）：{result['text'][:120]!r}\n"
        f"  done 里（{len(final_text)} 字）：{final_text[:120]!r}\n"
        f"两边分叉意味着「用户看到的」和「存进库的」不是同一份 —— 刷新就会变脸。"
    )


# ==================== 三、done 里的元信息 ====================

@pytest.mark.parametrize("question", [SAMPLE_OPEN, SAMPLE_BLOCKED],
                         ids=["走模型", "命中硬拦"])
def test_done_message_carries_intent_and_source(stream_ask, question):
    """done 里的那条消息要带上 intent / source（和非流式端点同一口径）。

    ⚠️ 这两个字段**没落库**（assistant_message 表就 8 列），
       只有当前这一轮的响应里有 —— 翻历史（GET .../messages）拿不到。
       所以这里断的是"当轮能看到"，不是"历史里也有"。
    """
    result = stream_ask(question)
    message = (result["done"] or {}).get("assistantMessage", {})

    assert message.get("intent") in INTENT_VALUES, (
        f"intent 取值超出预期：{message.get('intent')!r}（应为 {sorted(INTENT_VALUES)} 之一）"
    )
    assert message.get("source") in SOURCE_VALUES, (
        f"source 取值超出预期：{message.get('source')!r}（应为 {sorted(SOURCE_VALUES)} 之一）"
    )


# ==================== 四、硬拦这条路：不调模型、只推固定文案 ====================

def test_blocked_input_streams_single_fixed_reply(stream_ask):
    """命中硬拦时：只推**一段**固定文案，且 source=blocked、blocked=out_of_scope。

    这是"流式"最容易被做错的地方：硬拦本就没有增量可推，
    如果后端直接 return、什么都不推，客户端就会挂着一个永远空着的气泡。
    约定是：把固定文案当成**一段 delta** 推出去 —— 客户端就不用为"没有增量"写特例。

    断言值（intent=fallback / source=blocked / blocked=out_of_scope）来自实测：
    硬拦排在意图判断最前面，所以这条的意图必然是 fallback。
    """
    result = stream_ask(SAMPLE_BLOCKED)
    message = (result["done"] or {}).get("assistantMessage", {})

    assert result["delta_count"] == 1, (
        f"硬拦应只推一段固定文案，实际推了 {result['delta_count']} 段"
    )
    assert message.get("source") == "blocked", (
        f"硬拦的回答 source 应为 blocked，实际 {message.get('source')!r}"
        "（source≠blocked 说明它真的被送进模型了 —— 拦截已经形同虚设）"
    )
    assert message.get("blocked") == "out_of_scope", (
        f"拦下的类型应为 out_of_scope，实际 {message.get('blocked')!r}"
    )
    assert message.get("intent") == "fallback", (
        f"命中硬拦时意图应为 fallback，实际 {message.get('intent')!r}"
    )


# ==================== 五、流式与非流式不能各走各的 ====================

def test_stream_and_non_stream_agree_on_intent(stream_ask, ask):
    """同一句话，走流式和不流式，判出来的 intent 必须一样。

    为什么值得单测一条：这次改成流式，做法是**新增端点、复用同一套判定逻辑**
    （提示词、硬拦表、意图分类器都只有一份）。这条用例就是钉住这个前提 ——
    万一以后有人在流式那条路上顺手改了一句（比如换了个 prompt 拼接），
    两边的 intent 就会开始飘，而单看任一条都发现不了。

    同样一句话问两次，模型措辞会不一样（温度 0.6），但 **intent 是本地规则算的**，
    必须每次都一样 —— 这正是它敢拿来当断言的原因。
    """
    stream_result = stream_ask(SAMPLE_OPEN)
    non_stream_data = ask(SAMPLE_OPEN)

    stream_intent = ((stream_result["done"] or {}).get("assistantMessage") or {}).get("intent")
    non_stream_intent = non_stream_data["assistantMessage"].get("intent")

    assert stream_intent == non_stream_intent, (
        f"同一句话「{SAMPLE_OPEN}」两条路的 intent 不一致：\n"
        f"  流式   = {stream_intent!r}\n"
        f"  非流式 = {non_stream_intent!r}\n"
        f"这说明两条路已经各写了一套判定 —— 该去 RecipeServiceImpl 看看是不是被分叉了。"
    )
