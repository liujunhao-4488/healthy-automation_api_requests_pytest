# pages/diet_record_page.py
# 饮食记录（frontend/src/views/DietRecord.vue，1117 行 —— 前端最大的一个页面）
#
# ── 这个页面为什么值得专门做 POM，而不是"点几下填几个框" ──────────────
#   它同时有：筛选区表单、主表格、可展开的子表格、ECharts 图表、
#   AI 饮食建议区、添加弹窗。**筛选区和弹窗里都有 el-form-item**，
#   一旦不限定作用域，`form_item("日期")` 会随机命中筛选区的"日期"。
#   这种错的表现不是"找不到元素"，而是"填进去了但保存时报错说没填日期" ——
#   排查成本极高。所以下面所有弹窗内的定位都强制走 self.dialog()。
#
# ── 副作用的处理 ──────────────────────────────────────────────
#   饮食记录是**会累积的真数据**，不像档案只有一个当前值。
#   用例自己建的那条记录必须自己删掉，否则每跑一轮，列表里就多一条
#   "自动化测试-三文鱼沙拉"，跑一个月后表格要翻三页，AI 建议也会被这些假数据带偏。
#   所以 add_record() 返回"能定位到这条记录"的键（菜品名），
#   由用例 teardown 用它删除。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT
from pages.base_page import BasePage

# 前端 value → 页面 label（frontend/src/views/DietRecord.vue 的 mealTypeMap）
MEAL_LABELS = {
    "breakfast": "早餐",
    "lunch": "午餐",
    "dinner": "晚餐",
    "snack": "加餐",
}


class DietRecordPage(BasePage):
    path = "/dashboard/diet-record"

    # ---------------- 列表 / 筛选 ----------------

    def expect_loaded(self):
        self.expect_visible(self.by_role_button("添加记录"))
        self.expect_visible(self.table_rows().first)
        return self

    def row_by_food(self, food_name):
        """按菜品名找表格行。

        用 has_text 而不是按列索引取第 N 列：
          列顺序会随需求调整（"明细数"这种列是新加的），
          按索引取会在改版后**静默取错列**，断言照样绿，但断言的是别的东西。
        """
        return self.table_rows().filter(has_text=food_name).first

    def expect_row(self, food_name, timeout=EXPECT_TIMEOUT):
        expect(self.row_by_food(food_name)).to_be_visible(timeout=timeout)
        return self

    def expect_no_row(self, food_name, timeout=EXPECT_TIMEOUT):
        expect(self.table_rows().filter(has_text=food_name)).to_have_count(0, timeout=timeout)
        return self

    def row_calories(self, food_name):
        """读该行"热量(kcal)"列。

        按表头文字定位列再取值，而不是写死 nth：
          列是"日期/餐次/本餐名称/明细数/热量…"，中间任何一列增删都会让索引失效。
        """
        row = self.row_by_food(food_name)
        headers = self.page.locator(".el-table__header-wrapper th")
        count = headers.count()
        for i in range(count):
            if "热量" in headers.nth(i).inner_text():
                return row.locator("td").nth(i).inner_text().strip()
        return None

    def search(self):
        self.by_role_button("查询").click()
        # 不 sleep：等表格的 loading 遮罩消失，是"数据到齐"的唯一可靠信号
        self.expect_hidden(self.page.locator(".el-loading-mask:visible"))
        return self

    # ---------------- 添加弹窗 ----------------

    def open_add_dialog(self):
        self.by_role_button("添加记录").click()
        dialog = self.dialog()
        expect(dialog).to_be_visible(timeout=EXPECT_TIMEOUT)
        expect(dialog.get_by_text("添加饮食记录")).to_be_visible(timeout=EXPECT_TIMEOUT)
        return self

    def _in_dialog(self, locator):
        return self.dialog().locator(locator)

    def fill_date(self, date_str):
        """填日期（YYYY-MM-DD）。

        ⚠️ el-date-picker 的坑：
          它的输入框是**可编辑的**，但填完不按 Escape 的话，
          日期面板会浮在上面盖住后面的"餐次"下拉 ——
          点"餐次"时点到的是日期面板，Playwright 报 "element is not visible"，
          而人肉操作完全正常（因为人会先点别处关掉面板）。
        """
        field = self.dialog().get_by_placeholder("选择日期")
        field.fill(date_str)
        field.press("Escape")
        return self

    def pick_meal(self, meal_value):
        label = MEAL_LABELS.get(meal_value, meal_value)
        self.dialog().get_by_placeholder("请选择餐次").click()
        self.pick_select_option(label)
        return self

    def fill_food_name(self, name):
        self.dialog().get_by_placeholder("请输入这餐菜品名称，例如：三文鱼藜麦沙拉").fill(name)
        return self

    def fill_ingredient(self, name, amount, unit="g", calories="300"):
        """填第一行食材明细。

        第一行是模板里默认就有的（v-for 渲染的那一行），不需要先点"添加食材"。
        营养值只填热量：其余的留空，后端会按 0 处理 ——
        用例要验的是"记录能落库并回显"，不是营养计算（那是算法层的职责）。
        """
        row = self.dialog().locator(".ingredient-row").first
        row.get_by_placeholder("食材名称").fill(name)
        amount_input = row.locator(".ingredient-amount input").first
        amount_input.fill(str(amount))
        amount_input.press("Tab")  # el-input-number 必须失焦才提交值
        row.locator(".ingredient-unit").click()
        self.pick_select_option(unit)
        row.get_by_placeholder("热量(kcal)").fill(str(calories))
        return self

    def save(self):
        self.dialog().get_by_role("button", name="保存记录").click()
        return self

    def save_and_expect_success(self):
        self.save()
        self.toast("保存成功")
        # 弹窗必须关掉：只断提示不断弹窗，会漏掉"提示成功但表单没关、用户会重复提交"
        expect(self.dialog()).to_be_hidden(timeout=EXPECT_TIMEOUT)
        return self

    def expect_validation_error(self, text):
        """表单校验错误 / 业务警告（比如"请至少添加一项食材明细"）。"""
        expect(
            self.dialog().locator(".el-form-item__error").filter(has_text=text).first
        ).to_be_visible(timeout=EXPECT_TIMEOUT)
        return self

    def add_record(self, food_name, date_str, meal_value="lunch", ingredient="三文鱼", amount=150):
        """一条完整的新增链路，返回菜品名（当作用例后续定位/清理的键）。"""
        self.open_add_dialog()
        self.fill_date(date_str)
        self.pick_meal(meal_value)
        self.fill_food_name(food_name)
        self.fill_ingredient(ingredient, amount)
        self.save_and_expect_success()
        self.expect_row(food_name)
        return food_name

    # ---------------- 删除（清理用）----------------

    def delete_record(self, food_name):
        """删掉指定菜品名的记录。

        ⚠️ 确认框的确认按钮文案是"删除"，不是"确定"
          （DietRecord.vue 里显式配了 confirmButtonText: '删除'），
          默认以为"确定"的写法会一直等不到按钮。
        """
        row = self.row_by_food(food_name)
        if row.count() == 0:
            return self  # 已经不在了 —— 清理要幂等，重复调用不算错
        row.get_by_role("button", name="删除").click()
        self.confirm_dialog("删除")
        self.toast("删除成功")
        self.expect_no_row(food_name)
        return self
