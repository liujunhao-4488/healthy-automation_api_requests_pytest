# pages/assistant_page.py
# AI 饮食助手（frontend/src/views/IngredientSubstitute.vue）
# 路由：/dashboard/ingredient-substitute
#
# ── UI 层测 AI 对话，该断言什么（这个决定比选择器重要得多）───────────
#   ✗ 不断言回复内容。"控糖早餐怎么搭配" 每次答得都不一样，把某句话写进断言，
#     这条用例就会长期红着并最终被人 skip 掉 —— 那是负资产。
#   ✗ 不断言回复是否"科学/正确"。那是模型效果，归接口层的评测集管
#     （automation_api_requests_pytest 里已经有一套）。
#   ✓ 断言**链路和渲染**：用户气泡出现了吗？助手气泡有内容吗？
#     流结束后按钮恢复可点吗？会话切换后消息没串到别的会话吧？
#   ✓ 断言**前端该拦的**：空输入能不能发出去、超长输入提示、删除会话后消息清空。
#
#   一句话：**UI 层管"用户看得见的流程有没有断"，接口层管"答得对不对"。**
#   两层都去管模型效果，等于同一个东西测两遍，且 UI 那遍必然不稳定。
#
# ── 流式回复的"完成"怎么判（最容易写错的地方）────────────────────
#   ✗ sleep(10)。慢的时候没答完，快的时候白等；CI 上机器更慢。
#   ✗ 等文本不再变化。流式传输中间有停顿，会在半句话处判"完成"。
#   ✓ 等**发送按钮的 loading 态消失**。它是 <el-button :loading="loading">，
#     loading 就是"这一轮请求还没结束"的唯一真相来源，
#     前端自己在 finally 里关掉它，比任何文本特征都可靠。

import re

from playwright.sync_api import expect

from config.config import AI_TIMEOUT, EXPECT_TIMEOUT
from pages.base_page import BasePage

SEND_BUTTON = ".send-btn"


class AssistantPage(BasePage):
    path = "/dashboard/ingredient-substitute"

    # ---------------- 首页 ----------------

    def expect_loaded(self):
        # 只等输入框：它是这个页面的功能核心，且渲染最晚（在会话列表和聊天区之后）。
        # 不去断言标题文字 —— 标题是最容易被改的东西，
        # 而它一变，所有用例的失败信息都变成"标题不对"，掩盖真正的业务失败。
        self.expect_visible(self.composer)
        self.expect_visible(self.send_button)
        return self

    @property
    def composer(self):
        return self.page.get_by_placeholder("输入你的问题，例如：减脂期间晚餐怎么吃？")

    @property
    def send_button(self):
        # ⚠️ 这个按钮是 circle + 图标，没有文字：
        #   <el-button type="success" circle class="send-btn"><el-icon><Promotion/></el-icon></el-button>
        # 可访问名是空的，get_by_role("button", name=...) 抓不到。
        # 这就是"没有 data-testid 时的代价"—— 只能靠 class。
        # 该 class 一旦被样式重构改名，这条链路就断，所以它是加 data-testid 的头号候选。
        return self.page.locator(SEND_BUTTON).first

    def is_streaming(self):
        """这一轮还在流式输出吗（按钮处于 loading）。"""
        return self.send_button.evaluate("el => el.classList.contains('is-loading')")

    # ---------------- 消息 ----------------

    @property
    def assistant_bubbles(self):
        return self.page.locator(".message-row.assistant .bubble-assistant")

    @property
    def user_bubbles(self):
        return self.page.locator(".message-row.user .bubble-user")

    def last_assistant_text(self):
        return self.assistant_bubbles.last.inner_text().strip()

    def think_indicator(self):
        return self.page.locator(".chat-loading")

    # ---------------- 发送 ----------------

    def new_conversation(self):
        self.by_role_button("新建会话").click()
        return self

    def ask(self, prompt):
        """输入并发送（填输入框 + 点发送按钮）。"""
        self.composer.fill(prompt)
        self.send_button.click()
        return self

    def ask_by_quick_chip(self, label):
        """点快捷问题发送。

        比填输入框更稳：快捷 chip 是普通 <button>，有可见文字，
        定位不依赖任何 class；而 textarea 需要处理 Enter/失焦等细节。
        代价是问题固定 —— 正好，UI 层要的就是可重复。
        """
        self.page.locator(".quick-chip").filter(has_text=label).first.click()
        return self

    def wait_reply_done(self, timeout=AI_TIMEOUT):
        """等这一轮流式结束，并返回助手回复文本。

        判定顺序：
          ① 助手气泡出现（至少一条）
          ② 发送按钮 loading 消失
          ③ 助手气泡**非空**
        第 ③ 步单独判：流式是先建一个空气泡再往里填，
        如果后端一上来就报错，气泡会一直是空的、按钮也已恢复 ——
        只看 ① ② 会把"打开就是空白"当成通过。
        """
        expect(self.assistant_bubbles.first).to_be_visible(timeout=timeout)
        expect(self.page.locator(f"{SEND_BUTTON}.is-loading")).to_have_count(0, timeout=timeout)

        bubble = self.assistant_bubbles.last
        expect(bubble).not_to_have_text(re.compile(r"^\s*$"), timeout=EXPECT_TIMEOUT)
        return bubble.inner_text().strip()

    def ask_and_wait(self, prompt, timeout=AI_TIMEOUT):
        self.ask(prompt)
        return self.wait_reply_done(timeout=timeout)

    # ---------------- 会话管理 ----------------

    def conversation_items(self):
        return self.page.locator(".assistant-body .conversation-item, .conversation-list li")

    def delete_conversation(self):
        self.by_role_button("删除会话").click()
        return self

    def expect_empty_chat(self):
        expect(self.assistant_bubbles).to_have_count(0, timeout=EXPECT_TIMEOUT)
        expect(self.user_bubbles).to_have_count(0, timeout=EXPECT_TIMEOUT)
        return self
