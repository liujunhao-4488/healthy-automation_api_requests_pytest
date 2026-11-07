# pages/goal_page.py
# 饮食目标页（front2/src/views/GoalView.vue）
#
# 这一页的业务价值在于：它是**纯前端算出来的一份配置**。
#   · 目标类型 + 档案 → 推荐热量区间（Mifflin-St Jeor + 类型系数）
#   · 拖动任一营养素滑块 → 另外两项按原比例自动修正，总和恒为 100%
#   · 体重进度条、饮水估算、餐次提示全是前端算的
# 这类"算出来给你看"的逻辑在接口层完全测不到（接口只收到最终 4 个数字），
# 只能在 UI 层验 —— 这是本页用例存在的唯一理由。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT
from pages.base_page import BasePage


class GoalPage(BasePage):
    path = "/goal"

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        expect(self.page.get_by_role("heading", name="饮食目标", exact=True)).to_be_visible(
            timeout=timeout
        )
        return self

    # ---------------- 目标类型 ----------------

    @property
    def _type_card(self):
        """目标类型卡片。

        必须圈卡片范围：下面还有「每日餐次」的 .seg（2/3/4/5 餐），
        全局找 .seg button 会点到餐次上去 —— 这类"同名元素多处出现"是这套
        DOM 结构里最容易写错的一处（前端没有 data-testid，只能靠结构圈定）。
        """
        return self.page.locator("article.card").filter(
            has=self.page.get_by_role("heading", name="目标类型", exact=True)
        ).first

    def pick_type(self, name):
        self._type_card.get_by_role("button", name=name, exact=True).click()
        return self

    def current_type(self):
        """当前选中的目标类型（卡片右上角那个 badge 就是它）。"""
        return self._type_card.locator(".badge").first.inner_text().strip()

    # ---------------- 数字字段 ----------------

    def num_input(self, label):
        """按字段名取数字输入框。

        不能写 input[type=number]：这一页有 5 个数字框
        （起始体重 / 当前体重 / 目标体重 / 热量 / 饮水），取第一个必然取错。
        也不能用 nth —— 字段顺序一改就错位，按 label 圈才稳定。

        exact=False：label 文案是「当前体重（kg）」这种带单位的，
        按全等匹配就得把单位也写进用例，单位一改选择器就断；
        而这里几个标签前缀互不包含（起始体重 / 当前体重 / 目标体重），子串匹配不会串。
        """
        return self.field(label, exact=False).locator("input").first

    def set_kcal(self, value):
        self.num_input("每日热量目标").fill(str(value))
        return self

    def kcal_value(self):
        return int(float(self.num_input("每日热量目标").input_value()))

    def set_current_weight(self, value):
        self.num_input("当前体重").fill(str(value))
        return self

    def set_target_weight(self, value):
        self.num_input("目标体重").fill(str(value))
        return self

    # ---------------- 三大营养素 ----------------

    def macro_slider(self, label):
        """营养素滑块，按 aria-label 精准定位。

        页面上三个 range 输入框长得一模一样（只有前后的文字不同），
        前端给它们留了 aria-label（蛋白质占比 / 碳水化合物占比 / 脂肪占比），
        这是这一页唯一"稳定锚点"。
        """
        return self.page.get_by_label(label, exact=True)

    def nudge_macro(self, label, steps=5):
        """用方向键推滑块，而不是直接改 value。

        为什么不用 fill/evaluate：业务逻辑挂在 @input 和 @change 上
        （拖一项要按原比例修正另外两项）。直接赋值不会触发这两个事件，
        等于绕过被测逻辑自问自答 —— 那样测出来的"合计 100%"毫无意义。
        键盘操作是真实交互，两个事件都会触发。
        """
        slider = self.macro_slider(label)
        slider.focus()
        for _ in range(steps):
            slider.press("ArrowRight")
        return self

    def macro_sum(self):
        """读「合计 xx%」那个数字。"""
        text = self.page.get_by_text(re.compile(r"^合计\s*\d+%$")).first.inner_text()
        return int(re.search(r"(\d+)", text).group(1))

    def macro_percent(self, label):
        """读某个滑块当前的百分比（同行右侧的「30% · 120g」）。"""
        row = self.page.locator(".slider-row").filter(has=self.page.get_by_label(label, exact=True))
        text = row.locator(".val").first.inner_text()
        return int(re.search(r"(\d+)%", text).group(1))

    # ---------------- 保存 ----------------

    def save(self):
        self.page.locator(".page-actions").get_by_role(
            "button", name=re.compile("保存目标|保存中")
        ).first.click()
        return self

    def expect_saved(self, timeout=EXPECT_TIMEOUT):
        return self.expect_success_toast(timeout=timeout)
