# pages/assistant_page.py
# 作用：front2 AI 助手页（AssistantView）的 Page Object。
#
# 页面核心是流式对话，用例面对的不确定性：
#   · 回复耗时波动大（后端调大模型 8~25s，护栏拦截几乎秒回）——
#     两者都给 AI_TIMEOUT 上限，用 expect 等结果，绝不 sleep 固定秒数；
#   · 进页面会拉历史会话并自动打开最近一条 —— 消息区可能不为空，
#     断言"收到了新回复"要数着消息发，不能只看"有没有消息"；
#   · 流式期间有个占位气泡（.typing / .stream-text），结束后被真消息替换。
#
# 产品点也是断言点：每条 AI 回答带「意图：xx」「来源：xx」两个 chip ——
# 这是这个模块的可追溯性需求，UI 用例专门盯它。

import re

from playwright.sync_api import expect

from config.config import AI_TIMEOUT, EXPECT_TIMEOUT

from pages.base_page import BasePage


class AssistantPage(BasePage):
    path = "/assistant"

    def open(self, path=None, wait_until="domcontentloaded"):
        super().open(path, wait_until)
        return self.expect_loaded()

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        # exact=True：get_by_role 的 name 默认子串匹配，标题类断言一律加严
        expect(
            self.page.get_by_role("heading", name="AI 饮食助手", exact=True)
        ).to_be_visible(timeout=timeout)
        # 会话列表是异步拉的，等它有个结论（有列表或空态文案）再继续，
        # 避免开场瞬间"既没有会话也没有空态"的中间态
        expect(
            self.page.locator(".conv-empty").or_(self.page.locator(".conv-row").first)
        ).to_be_visible(timeout=timeout)
        return self

    # ---------------- 输入与发送 ----------------

    def input_box(self):
        return self.page.locator(".chat-input textarea")

    def send_button(self):
        return self.page.locator(".chat-input").get_by_role("button", name="发送")

    def send(self, text):
        """输入并发送。发送后输入框会被清空 —— 这本身就是"发出去了"的证据。"""
        count_before = self.ai_message_count()
        self.input_box().fill(text)
        self.send_button().click()
        expect(self.input_box()).to_have_value("", timeout=EXPECT_TIMEOUT)
        # 等用户气泡真的出现在消息区（本地先落一条，应该瞬间可见）
        expect(self.page.locator(".msg.user .msg-bubble").filter(has_text=text).last).to_be_visible(
            timeout=EXPECT_TIMEOUT
        )
        return count_before

    def click_suggest(self, text):
        """点引导页的快捷提问（等价于直接 send 这句话）。"""
        self.page.locator(".suggest").filter(has_text=text).first.click()
        return self

    def guardrail_button(self):
        """输入区下方的「试试医疗越界问题」—— 走护栏链路的捷径。"""
        return self.page.locator(".chat-hint .link-btn")

    # ---------------- 回复断言 ----------------

    def wait_ai_settled(self, before_count=0, timeout=AI_TIMEOUT):
        """等一条**新的 AI 回复落定**，返回最后一条 AI 消息。

        两个必须绕开的坑：
        1) 流式期间页面会插一个占位气泡（.msg 不带 user 类），它**也匹配
           .msg:not(.user)** —— 只数消息数的话，占位一出现就"到数"了，
           读到的是还没内容的气泡。占位气泡的标志是页面存在 .stream-text，
           它消失 = 流式结束、占位被真消息替换。
        2) 落定后还要确认最后一条有正文或有拦截说明（流式中断会留下空气泡）。
        """
        import time

        deadline = time.monotonic() + timeout / 1000
        msgs = self.page.locator(".msg:not(.user)")
        while time.monotonic() < deadline:
            settled = (
                msgs.count() == before_count + 1
                and self.page.locator(".stream-text").count() == 0
            )
            if settled:
                last = msgs.last
                if last.locator(".blocked-note").count() or last.locator(".msg-bubble").count():
                    return last
            self.page.wait_for_timeout(300)
        raise AssertionError(
            f"等了 {timeout}ms 没等到 AI 回复落定"
            f"（发送前 {before_count} 条，当前 {msgs.count()} 条，"
            f"streaming={'进行中' if self.page.locator('.stream-text').count() else '已结束'}）"
        )

    def ai_message_count(self):
        """当前 AI 消息数（含流式占位 —— 只用于"发送前"的基线计数）。"""
        return self.page.locator(".msg:not(.user)").count()

    def expect_reply_annotated(self, msg, timeout=EXPECT_TIMEOUT):
        """断言回答带意图与来源标注（本模块的可追溯性需求）。"""
        meta = msg.locator(".msg-meta")
        expect(meta).to_contain_text("意图：", timeout=timeout)
        expect(meta).to_contain_text("来源：", timeout=timeout)
        return self

    def expect_reply_nonempty(self, msg):
        """回答正文非空（流式断了会留下空气泡，这里兜住）。"""
        text = msg.locator(".msg-bubble").inner_text().strip()
        assert text, "AI 回复的气泡是空的 —— 流式链路可能中断"

    def expect_blocked(self, timeout=AI_TIMEOUT):
        """护栏拦截：出现 .blocked-note（含「安全护栏已拦截」）。"""
        note = self.page.locator(".blocked-note").last
        expect(note).to_be_visible(timeout=timeout)
        expect(note).to_contain_text("安全护栏已拦截")
        return self
