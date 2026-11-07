# test_cases/health/test_health_profile_ui.py
# front2 健康档案 —— 核心用例是「BMI 显示值 = 页面身高体重算出来的值」这个 oracle：
#   前端 KPI 的 bmi 来自保存响应（后端重算），表单里的身高体重是用户输入 ——
#   两者能对上，说明"后端重算 → 前端回显"整条链路没断；
#   对不上就是真缺陷（历史缺陷：保存后 BMI 不变 —— 前端没把重算值写回 store）。
#
# 注意：这套前端没有"档案未完成引导流"（路由守卫不看档案），
# KPI 卡是 v-if（没档案就不渲染），所以依赖测试库里有档案 → needs_profile。

import re

import pytest
from playwright.sync_api import expect

from pages.health_profile_page import HealthProfilePage


def _to_float(raw):
    return float(str(raw).strip())


class TestHealthProfile:
    def test_档案回显_KPI的BMI与表单身高体重自洽(self, user_page, profile_ready):
        page = HealthProfilePage(user_page)
        page.open().wait_form_loaded()

        height = _to_float(page.input_by_label("身高（cm）").input_value())
        weight = _to_float(page.input_by_label("体重（kg）").input_value())
        assert height and weight, "表单回显的身高体重是空的（后端没有档案？）"

        # oracle：BMI = 体重 / 身高²，四舍五入 1 位（和前后端同一个公式）
        expected_bmi = round(weight / (height / 100) ** 2, 1)

        page.expect_kpi_visible()
        bmi_text = page.kpi_value("BMI").inner_text().strip()
        assert re.fullmatch(r"\d+\.\d", bmi_text), f"BMI 显示不是数值：{bmi_text!r}"
        assert abs(float(bmi_text) - expected_bmi) <= 0.15, (
            f"BMI 显示 {bmi_text}，但按表单身高体重算应为 {expected_bmi} —— "
            f"后端重算或前端回显链路断了"
        )

    def test_修改体重保存成功_刷新后仍是新值(self, user_page, profile_ready):
        page = HealthProfilePage(user_page)
        page.open().wait_form_loaded()

        weight_input = page.input_by_label("体重（kg）")
        old = _to_float(weight_input.input_value())
        new = round(old + 0.5, 1)

        weight_input.fill(str(new))
        page.save_button().click()
        page.expect_saved()

        user_page.reload(wait_until="domcontentloaded")
        page.wait_form_loaded()
        saved = _to_float(page.input_by_label("体重（kg）").input_value())
        assert abs(saved - new) < 0.01, f"刷新后体重回显 {saved}，保存的 {new} 没落库"

        # 收尾：把体重改回去，不污染其他用例的数据基线
        page.input_by_label("体重（kg）").fill(str(old))
        page.save_button().click()
        page.expect_saved()

    def test_体重超范围_保存被前端拦下且字段标红(self, user_page, profile_ready):
        page = HealthProfilePage(user_page)
        page.open().wait_form_loaded()

        page.input_by_label("体重（kg）").fill("500")
        page.save_button().click()

        page.expect_validation_error("体重（kg）")
        # 被拦住 = 留在本页，没有跳转也没有误存
        expect(user_page).to_have_url(re.compile(r"/health/?$"), timeout=5_000)
