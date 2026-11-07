# pages/health_profile_page.py
# 作用：front2 健康档案页（HealthView）的 Page Object。
#
# 页面行为要点（写用例前必须知道的三件事）：
#   1) 表单数据挂载时异步从后端 GET /health/info 拉取回填 ——
#      进页面瞬间表单是空的，直接断言/操作会拿到"还没回填"的状态。
#      页面有个防冲掉用户输入的机制（untouched 判断）：**表单一旦被动过，
#      后端数据就不再回填**。所以用例要么先等回填完成再动手，
#      要么接受"填的就是我填的值" —— 不能既抢在回填前填了值又指望它被覆盖。
#   2) KPI 卡（BMI/BMR/血压/血糖）只在 healthFilled（后端确实有档案）时渲染，
#      v-if 控制 —— 没档案的账号连元素都不存在，不能拿来当必现断言。
#   3) 保存成功后 KPI 立即刷新（保存响应里带回重算的 bmi/bmr 写进 store）。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT

from pages.base_page import BasePage


class HealthProfilePage(BasePage):
    path = "/health"

    def open(self, path=None, wait_until="domcontentloaded"):
        super().open(path, wait_until)
        return self.expect_loaded()

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        # ⚠️ 必须 exact=True：get_by_role 的 name 默认是**子串匹配**，
        # "健康档案"会同时命中空态标题"还没有健康档案"，strict mode 直接炸。
        # 而且空态标题出现本身说明"后端没档案"，把它排除在外才是在测对的东西。
        expect(
            self.page.get_by_role("heading", name="健康档案", exact=True)
        ).to_be_visible(timeout=timeout)
        return self

    # ---------------- 表单控件 ----------------

    def input_by_label(self, label):
        """按 label 拿输入框：年龄（岁）/ 身高（cm）/ 体重（kg）/ 腰围（cm）/
        每日运动时长（分钟）—— exact 匹配，'体重（kg）' 不会命中'体重趋势'。"""
        return self.field_input(label)

    def gender_option(self, name):
        """性别 .seg（女 / 男）。性别字段只有一个，scope 圈 .field 即可。"""
        field = self.page.locator(".field").filter(
            has=self.page.get_by_text("性别", exact=True)
        ).first
        return self.seg_option(field, name)

    def save_button(self):
        return self.page.get_by_role("button", name=re.compile("保存身体数据"))

    # ---------------- 等待后端回填 ----------------

    def wait_form_loaded(self, timeout=EXPECT_TIMEOUT):
        """等后端档案回填进表单（loadRemote 是异步的）。

        判据：体重框里有数字。没档案的账号这里永远等不到 ——
        那不是用例的 bug，是环境里没有档案数据，needs_profile 标记负责挡住这种情况。
        """
        weight = self.input_by_label("体重（kg）")
        expect(weight).to_have_value(re.compile(r"\d"), timeout=timeout)
        return self

    # ---------------- KPI ----------------

    def kpi_section(self):
        return self.page.locator("section.grid.g4")

    def kpi_value(self, label):
        """某张 KPI 卡的数值（如 BMI 卡的 22.1）。"""
        card = self.page.locator("article.card.kpi").filter(
            has=self.page.get_by_text(label, exact=False)
        ).first
        return card.locator(".kpi-value")

    def expect_kpi_visible(self, timeout=EXPECT_TIMEOUT):
        expect(self.kpi_section()).to_be_visible(timeout=timeout)
        return self

    # ---------------- 断言辅助 ----------------

    def expect_saved(self, timeout=EXPECT_TIMEOUT):
        """保存成功的轻提示。

        文案用后端返回的 res.message 兜底「健康档案已保存」——
        后端可能改措辞，所以按正则匹配"保存"相关文案，别写死整句。
        """
        self.toast(re.compile(r"已保存|保存成功"), timeout=timeout)
        return self

    def expect_validation_error(self, field_label, timeout=EXPECT_TIMEOUT):
        """保存被前端校验拦下：toast 提示 + 对应字段标红。"""
        self.toast("填写有误", timeout=timeout)
        field = self.field(field_label)
        expect(field).to_have_class(re.compile(r"has-error"), timeout=timeout)
        return self
