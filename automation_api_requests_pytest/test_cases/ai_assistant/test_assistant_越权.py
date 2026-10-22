# test_cases/ai_assistant/test_assistant_越权.py
# 【任务：AI 助手 · 水平越权（IDOR / BOLA）】—— OWASP API Security Top 10 · API1
# ═══════════════════════════════════════════════════════════════════════════
# 这个工位之前只有"半个"用例。
#
#   已有的 `test_chat_with_unknown_conversation` 传的是 `conversationId: 999999`，
#   它测的是「**会话不存在**」。
#
#   本文件测的是「会话**存在**，但是别人的」——这两件事差很远：
#     · 不存在的 id：后端完全可以在查库之前就拒掉，甚至不需要 user_id 这个概念；
#     · 别人的会话：必须真的比对 `conversation.user_id == 当前登录用户` 才拦得住。
#   后者失守 = **一个普通用户能读、能删、能往别人的会话里发消息**。
#   在简历和面试里，这是"安全事故"，不是"接口报错"。
#
# ══ 判据为什么能精确断言（不需要 judge）═══════════════════════════════════
#   越权的判据全是确定性的：
#     · 状态码是不是 200（有没有让你得逞）
#     · 数据归属对不对（列表里有没有别人的 id）
#     · **副作用有没有发生**（删失败之后，那个会话还在不在）
#   没有一句需要看模型说了什么，所以不会随措辞波动，可以天天跑。
#
# ══ 三道"不只断状态码"的设计 ═════════════════════════════════════════════
#   ① 删除越权要验**副作用**。
#      只看 `status_code != 200` 是不够的：如果后端写成"先删、再校验归属"，
#      状态码照样是 400，但会话已经被删了——用户看着像被拒绝，数据却没了。
#      所以删除失败后必须回头确认：**B 自己还能读到这个会话**。
#
#   ② 读消息越权不能用一个空会话测。
#      空会话对谁都是 `[]`，归属校验整段漏了也照样"通过"。
#      所以 other_user 夹具里先让 B 真聊一句，会话里有别人的数据才测得出泄漏。
#
#   ③ 列表接口也要测。
#      单条资源的归属校验做对了，列表接口忘了加 `where user_id = ?` 的情况非常常见。
#      列表泄漏的是**标题**（用户第一句话），比正文更容易被忽略。
#
# ⚠️ 跑这份用例的前提：后端 8080 已启动（要能注册临时账号）。
#    不依赖模型质量——就算 DeepSeek 挂了走本地兜底，越权判据照样成立。


# 后端所有"无权访问"都抛同一个 RuntimeException，由全局异常处理转成 400 + 这句 message。
# 刻意不去区分"不存在"和"不是你的"——这是**正确**的安全设计（不泄漏资源是否存在）。
EXPECTED_MSG = "会话不存在或无权访问"


def _assert_denied(resp, action, resource):
    """统一的"应该被拒绝"断言。

    为什么不锁死 400：安全测试的核心是"没让你得逞"，不是状态码的具体数字。
    403 / 400 / 404 在语义上都可以接受（甚至 404 更好，不暴露资源存在）。
    但 **200 一定不行**，2xx 里任何一个都说明攻击成功了。
    """
    assert not (200 <= resp.status_code < 300), (
        f"{action} 越权成功了：用 A 的 token 操作 B 的{resource}，"
        f"返回 {resp.status_code}。\n"
        f"响应体：{resp.text[:300]!r}\n"
        f"→ 这是**数据泄漏 / 数据破坏**缺陷：后端没有校验资源归属。"
    )

    # 第二道：400 的文案必须是统一口径。
    # 如果这里回的是"这不是你的会话"、而 999999 回的是"会话不存在"，
    # 攻击者就能靠报错文案**枚举出哪些 id 真实存在**（资源枚举）。
    # 后端刻意不区分这两种情况，这条断言就是在守住这个设计。
    if resp.status_code == 400:
        try:
            msg = resp.json().get("message", "")
        except ValueError:
            return
        assert msg == EXPECTED_MSG, (
            f"{action} 被拒了，但报错文案不统一：{msg!r}（期望 {EXPECTED_MSG!r}）。\n"
            f"→ 如果「别人的会话」和「不存在的会话」返回不同文案，"
            f"攻击者可以用它枚举出哪些会话 id 真实存在（资源枚举）。"
        )


# ==================== 一、读：往别人的会话里发消息 ====================


def test_cross_user_chat_denied(api, auth_headers, other_user):
    """A 用自己的 token + B 的 conversationId 发消息 → 必须被拒。

    这是最直接的一条：如果它过了，A 就能在 B 的对话里插话，
    而且这些消息会以 B 的身份出现在历史里（B 打开 App 会看到自己"说过"的话）。
    """
    cid_b = other_user["conversationId"]

    # 用一个**独一无二的标记**，而不是"你好"——
    # other_user 夹具里 B 自己也发过"你好"，用它做判据会把正常数据当成越权证据。
    marker = "A越权插入-7XQ"

    resp = api.assistant.chat(
        {"conversationId": cid_b, "rawPrompt": marker},
        headers=auth_headers,
    )

    _assert_denied(resp, "往别人的会话发消息", "会话")

    # 状态码对了还不够——确认这句话**没有被写进 B 的会话**。
    messages = api.assert_ok(
        api.assistant.list_messages(cid_b, headers=other_user["headers"]),
        "B 读取自己的会话应成功",
    )["data"]

    assert all(m["text"] != marker for m in messages), (
        f"接口返回了 {resp.status_code}（看起来拒绝了），"
        f"但 {marker!r} **已经被写进 B 的会话**。\n"
        f"B 的会话消息：{[m['text'][:30] for m in messages]}\n"
        f"→ 典型的「先写后校验」：副作用发生在权限检查之前。"
    )


# ==================== 二、读：读别人的会话消息 ====================


def test_cross_user_read_messages_denied(api, auth_headers, other_user):
    """A 读 B 的会话消息列表 → 必须被拒。

    这条如果漏了，泄漏的是**完整对话内容**（可能包含身高体重、疾病、用药），
    比泄漏一个会话标题严重得多。
    """
    cid_b = other_user["conversationId"]

    resp = api.assistant.list_messages(cid_b, headers=auth_headers)

    _assert_denied(resp, "读取别人的会话消息", "消息列表")


# ==================== 三、写：删别人的会话（重点验副作用）====================


def test_cross_user_delete_denied(api, auth_headers, other_user):
    """A 删 B 的会话 → 必须被拒，**且 B 的会话必须还在**。

    这条的价值全在第二个断言上：
      如果后端是"先删再校验"，返回 400 会让你以为防住了，
      但 B 下次打开 App 会发现整个对话没了——**不可逆的数据丢失**。
    """
    cid_b = other_user["conversationId"]

    resp = api.assistant.delete_conversation(cid_b, headers=auth_headers)

    _assert_denied(resp, "删除别人的会话", "会话")

    # 副作用断言：B 自己还能读到它，说明软删除没有发生。
    after = api.assistant.list_messages(cid_b, headers=other_user["headers"])
    assert after.status_code == 200, (
        f"删除请求被拒了（{resp.status_code}），但 B 已经读不到自己的会话了"
        f"（{after.status_code}，body={after.text[:200]!r}）。\n"
        f"→ **先删后校验**：副作用发生在权限检查之前，数据已被破坏。"
    )


# ==================== 四、流式接口（同一资源的另一条写入路径）====================


def test_cross_user_stream_denied(api, auth_headers, other_user):
    """A 用 B 的 conversationId 走流式接口 → 必须被拒。

    为什么要单独测：流式接口是**另一个 Controller 方法**，
    很容易在实现时复制了 chat 的逻辑却漏了归属校验。
    "非流式做对了"不能推出"流式也做对了"。
    """
    cid_b = other_user["conversationId"]

    result = api.assistant.chat_stream(
        {"conversationId": cid_b, "rawPrompt": "你好"},
        headers=auth_headers,
        timeout=30,
    )

    # ⚠️ SSE 的拒绝不是 HTTP 4xx：Controller 先返回 SseEmitter，状态码必然是 200，
    #    真正的拒绝是流里的 error 事件。所以判据是"两者至少有一个"：
    #      · 非 2xx —— 如果将来改成在返回 emitter 之前就拒掉，也可以；
    #      · 2xx + error 事件 —— 当前实现的正常拒绝形态。
    denied_by_status = not (200 <= result["status_code"] < 300)
    denied_by_event = result["error"] is not None
    assert denied_by_status or denied_by_event, (
        f"流式聊天越权没有被拒绝：HTTP {result['status_code']}，"
        f"事件={[name for name, _ in result['events']]}，error={result['error']!r}。\n"
        f"→ 流式接口漏了归属校验（非流式做对不代表这条也对）。"
    )

    # 拒绝文案必须和非流式统一，避免靠报错差异枚举会话是否存在。
    if denied_by_event:
        message = (result["error"] or {}).get("message", "")
        assert message == EXPECTED_MSG, (
            f"流式接口拒绝了，但报错文案不统一：{message!r}（期望 {EXPECTED_MSG!r}）。\n"
            f"→ 如果「别人的会话」和「不存在的会话」返回不同文案，"
            f"攻击者可以用它枚举出哪些会话 id 真实存在（资源枚举）。"
        )

    # 最关键的一条：不管状态码是什么，都不能真的吐出回答内容。
    assert not result["text"].strip(), (
        f"流式接口返回 {result['status_code']}，但已经产出了回答内容："
        f"{result['text'][:200]!r}\n"
        f"→ 错误被包进了 SSE 事件里，模型其实已经被调用了。"
    )


# ==================== 五、列表：不泄漏别人的会话 ====================


def test_conversation_list_does_not_leak_others(api, auth_headers, other_user):
    """A 的会话列表里不该出现 B 的会话 id。

    单条资源的归属校验做对了、列表接口忘了加 `where user_id = ?`，
    是这类缺陷最常见的形态。泄漏的是会话标题（通常是用户第一句话），
    在心理健康 / 疾病相关场景里，光标题就足够敏感。
    """
    cid_b = other_user["conversationId"]

    listed = api.assert_ok(
        api.assistant.list_conversations(headers=auth_headers),
        "读取自己的会话列表应成功",
    )["data"]

    leaked = [c for c in listed if c["id"] == cid_b]
    assert not leaked, (
        f"A 的会话列表里出现了 B 的会话：{leaked}\n"
        f"→ 列表接口没有按 user_id 过滤（单条接口过滤了不代表列表也过滤了）。"
    )
