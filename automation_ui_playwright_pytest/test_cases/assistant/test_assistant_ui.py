# test_cases/assistant/test_assistant_ui.py
# AI 饮食助手（/dashboard/ingredient-substitute）。
#
# ── 这组用例的量刻意压到最少（3 条），理由要说清 ──────────────────
#   1) 慢：每条要真等模型，首字 2~5s、整段 8~25s。
#      堆 10 条 AI 用例 = 每轮回归多 3 分钟，而它们验的东西高度重复。
#   2) 不稳：模型输出有抖动，断言写得越细越容易假红。
#      假红多了，人就开始整组 skip，覆盖等于零 —— 这比不写更糟。
#
#   所以分工是：
#     UI 层（本文件）  → 链路通不通、渲染对不对、状态机有没有卡住
#     接口层（已有）   → 意图识别、RAG 召回、安全拦截、越狱、RAG 生成质量
#   同一个问题在这两层各测一遍，收益是零，成本是两倍维护。
#
# ── 稳定性的两个具体手段 ───────────────────────────────────────
#   ① 用**快捷问题 chip** 而不是自由输入：问题固定 → 后端路径固定 → 波动更小。
#   ② 判定完成靠**发送按钮的 loading 消失**，不靠 sleep、不靠"文字不再变化"。
#      （原因见 pages/assistant_page.py 头部注释）

import pytest

from pages.assistant_page import AssistantPage


@pytest.mark.slow_ai
class TestAssistantChat:

    def test_快捷问题_能拿到非空回复(self, user_page):
        """发一个问题，必须拿回一段非空回复。

        断言只做到"非空"，不断言内容 —— 内容属于模型效果，归接口层评测集。
        这里要证明的是：**从点下去到气泡里出现字，这条链路没断**。
        链路断了的典型表现：气泡一直空着、一直转圈、或者报"网络错误"。
        """
        page = AssistantPage(user_page).open()
        page.expect_loaded()

        page.ask_by_quick_chip("控糖早餐")
        reply = page.wait_reply_done()

        assert reply.strip(), "助手回复是空的：链路通了但没内容（检查流式渲染）"
        # 用户那条气泡也必须出现 —— 只有助手气泡说明"发出去了但没回显问题"
        page.expect_visible(page.user_bubbles.first)

    def test_发送后按钮恢复可点_不会卡在loading(self, user_page):
        """一轮结束后发送按钮必须能再点。

        这是"状态机没复位"的探测器：
          loading 没关 → 用户看着有回复，但再也发不出第二条，只能刷新页面。
          这类缺陷在手工测试时很容易被"等一下再试就好了"糊过去。
        """
        page = AssistantPage(user_page).open()
        page.expect_loaded()

        page.ask_by_quick_chip("食材替换")
        page.wait_reply_done()

        assert page.is_streaming() is False, "回复已结束，但发送按钮仍处于 loading"

        # 真的再发一条：能发出去才说明状态真的复位了
        page.ask_by_quick_chip("低钠晚餐")
        second = page.wait_reply_done()
        assert second.strip(), "第二条消息没拿到回复"

    def test_空输入_发不出去(self, user_page):
        """不填内容直接点发送 → 不发请求、不产生气泡。

        ⚠️ 判据用"气泡数量没变"而不是"有校验红字"：
           el-form 的 prompt 规则是 required + trigger: blur，
           点发送时走 validate()，红字可能出现也可能因为 blur 时机不出现。
           但"没多发出一条消息"是**确定的行为**，不依赖 UI 细节。
        """
        page = AssistantPage(user_page).open()
        page.expect_loaded()

        before = page.user_bubbles.count() + page.assistant_bubbles.count()

        page.composer.fill("")
        page.send_button.click()

        # 给一点点时间让"如果发出去"的气泡有机会出现
        page.page.wait_for_timeout(1500)

        after = page.user_bubbles.count() + page.assistant_bubbles.count()
        assert after == before, "空输入居然发出了消息"
