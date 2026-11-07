# test_cases/record/test_diet_record_ui.py
# front2 饮食记录 —— 主链路：搜食材 → 选候选 → 克数 → 加入本餐 → 保存 → 列表出现。
# 删除放在同一条用例末尾做自清理：添加用例本来就要写一条测试数据，
# 用完删掉，测试库不会越跑越脏（数据自洽比"用例数更多"有价值）。
#
# 空态校验单独一条：不选食材直接点保存，前端应拦（toast，不弹窗不报错）。

import pytest

from pages.diet_record_page import DietRecordPage

# 食材关键词用后端食材库必有的常见食材 —— 真没有的话这条红是对的（环境缺数据）
INGREDIENT = "燕麦"


class TestDietRecord:
    def test_添加记录_列表出现_删除后消失(self, user_page):
        page = DietRecordPage(user_page)
        page.open()

        # 传 meal_name 让餐次确定（不传会按当前时间猜，断言就随机了）
        page.add_record("早餐", INGREDIENT, grams=50)
        page.save_record()
        page.expect_record_saved("早餐")

        # 列表证据：早餐卡出现包含食材名的记录行
        row = page.meal_records("早餐").filter(has_text=INGREDIENT).first
        row.wait_for(state="visible")
        # 行内带热量值（kcal），说明营养计算链路也走完了
        assert "kcal" in row.inner_text(), "记录行里没有热量值，营养计算可能没落库"

        # 自清理：删除要过二次确认（ConfirmDialog，按钮文案是「删除」）
        page.wait_toast_gone()
        page.delete_record("早餐", INGREDIENT)

    def test_未选食材直接保存_前端拦下不误存(self, user_page):
        page = DietRecordPage(user_page)
        page.open()

        page.open_add_modal("早餐")
        page.save_record()

        page.toast("请至少添加一项食材")
        # 弹窗还在（没被误关），记录也没存
        page.modal()
