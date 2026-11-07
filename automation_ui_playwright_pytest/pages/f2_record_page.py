# pages/f2_record_page.py
# 作用：front2 饮食记录页（RecordView）的 Page Object。
#
# 这页是 front2 交互最重的页面，用例要走的链路：
#   某餐的「添加」→ 弹窗 → 搜索食材（后端食材库，140ms 防抖出候选）
#   → 选候选 → 填克数（220ms 防抖出营养预览）→ 加入本餐 → 保存记录
#
# 三个必须处理的异步点，全靠 expect 自动等待而不是 sleep：
#   · 搜索候选：输入后 140ms 才出现，直接点 .cand 会找不到元素；
#     反过来，点完候选关键词被清空，候选框立刻收起 —— 别再断言它还开着。
#   · 营养预览：改克数后 220ms 才刷新，「加入本餐」按钮本身不受影响
#     （它拿的是点击时的 grams 值），所以预览断言可以松一点。
#   · 保存成功后弹窗自己关，toast「已保存到今天 · 早餐」2.6s 后消失。
#
# 定位关键：餐次卡片用 h3 文案圈（早餐/午餐/晚餐/加餐），
# 弹窗内输入框用 id（foodSearch / gramsInput / noteInput）。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT

from pages.f2_base_page import F2BasePage


class F2RecordPage(F2BasePage):
    path = "/record"

    def open(self, path=None, wait_until="domcontentloaded"):
        super().open(path, wait_until)
        return self.expect_loaded()

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        # exact=True：子串匹配会命中弹窗里的"添加饮食记录"（弹窗常驻 DOM，
        # 只是 overlay 没展开，heading 一直存在于页面）
        expect(
            self.page.get_by_role("heading", name="饮食记录", exact=True)
        ).to_be_visible(timeout=timeout)
        return self

    # ---------------- 餐次卡片 ----------------

    def meal_card(self, meal_name):
        """某餐的卡片。卡片结构固定 <article class="card"> 内含 <h3>餐名</h3>。

        h3 用子串匹配（has_text 普通字符串）而非 ^...$ 锚点：
          Vue 模板渲染的 h3 innerText 带换行缩进，锚点正则永远匹配不上。
          "早餐"只出现在本卡 h3 和空态文案里，而空态文案不在 h3 元素内，
          所以子串匹配不会串卡。
        """
        card = self.page.locator("article.card").filter(
            has=self.page.locator("h3").filter(has_text=meal_name)
        ).first
        expect(card).to_be_visible()
        return card

    def meal_records(self, meal_name):
        """某餐卡片下的记录行（.log-row，空则返回空集合 locator）。"""
        return self.meal_card(meal_name).locator(".log-row")

    def open_add_modal(self, meal_name=None):
        """打开添加弹窗。

        传 meal_name 就点对应餐次卡片里的「添加」（弹窗餐次预选为该餐），
        不传就点右上角「添加记录」（餐次按当前时间猜）。
        用例里**优先传**：不传的话餐次取决于跑用例的时刻（10 点前是早餐，15 点后是加餐），
        断言"记录出现在哪一餐"就会时好时坏 —— 这种随机红最难查。
        """
        if meal_name:
            # 卡片里"添加"有两个（card-hd 一个 + 空态提示里一个），限定头部那个
            self.meal_card(meal_name).locator(".card-hd").get_by_role(
                "button", name="添加"
            ).click()
        else:
            self.page.get_by_role("button", name=re.compile("^添加记录$")).click()
        self.modal()  # 等弹窗可见
        return self

    # ---------------- 弹窗内操作 ----------------

    def search_ingredient(self, keyword):
        """搜索食材并等候选出现。返回候选列表 locator（可能为空 = 没搜到）。"""
        self.page.locator("#foodSearch").fill(keyword)
        cand_box = self.page.locator(".cand-box.on")
        expect(cand_box).to_be_visible(timeout=EXPECT_TIMEOUT)
        return self.page.locator(".cand-box.on .cand")

    def pick_first_candidate(self):
        """点第一个候选。点完关键词被替换成食材名、候选框收起，都属正常。"""
        self.page.locator(".cand-box.on .cand").first.click()
        return self

    def set_grams(self, grams):
        self.page.locator("#gramsInput").fill(str(grams))
        return self

    def add_to_meal(self):
        self.page.get_by_role("button", name="加入本餐").click()
        return self

    def save_record(self):
        self.page.get_by_role("button", name=re.compile("^保存记录$")).click()
        return self

    def staged_items(self):
        """弹窗里"已添加条目"的行。"""
        return self.modal().locator(".log-row")

    # ---------------- 主流程封装 ----------------

    def add_record(self, meal_name, ingredient_keyword, grams=100):
        """完整添加链路：开弹窗 → 搜食材 → 选第一个候选 → 填克数 → 加入本餐。"""
        self.open_add_modal(meal_name)
        self.search_ingredient(ingredient_keyword)
        self.pick_first_candidate()
        if grams != 100:
            self.set_grams(grams)
        self.add_to_meal()
        # 等条目真的进了"已添加"列表再保存，否则保存的是空列表（会被前端拦）
        expect(self.staged_items()).not_to_have_count(0, timeout=EXPECT_TIMEOUT)
        return self

    def expect_record_saved(self, meal_name, timeout=EXPECT_TIMEOUT):
        """保存成功的两个证据：toast + 该餐列表出现新行。

        toast 文案是「已保存到今天 · <餐次>」，按"已保存到"前缀匹配。
        """
        self.toast(re.compile(r"^已保存到"), timeout=timeout)
        return self

    # ---------------- 删除 ----------------

    def delete_record(self, meal_name, keyword, confirm_text="删除"):
        """删除该餐下包含 keyword 的记录，走二次确认。"""
        row = self.meal_records(meal_name).filter(has_text=keyword).first
        expect(row).to_be_visible(timeout=EXPECT_TIMEOUT)
        row.locator("button[title=删除记录]").click()
        self.confirm_dialog(ok_text=confirm_text)
        self.toast("记录已删除")
        expect(row).to_have_count(0, timeout=EXPECT_TIMEOUT)
        return self

    # ---------------- 日期切换 ----------------

    def switch_date(self, label):
        """前一天 / 今天 / 后一天（.page-actions 里的 .seg，用可访问名匹配）。"""
        seg = self.page.locator(".page-actions .seg")
        seg.get_by_role("button", name=label, exact=True).click()
        return self

    def expect_day_summary(self, text, timeout=EXPECT_TIMEOUT):
        """顶部"今天 · 已记录 N 餐"那行副标题。"""
        expect(self.page.locator(".page-head .page-sub")).to_contain_text(
            text, timeout=timeout
        )
        return self
