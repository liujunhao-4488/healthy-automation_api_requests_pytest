# test_cases/record/test_diet_record_ui.py
# 饮食记录：新增 → 列表回显 → 删除（含必填校验、食材明细校验）。
#
# ── 这个模块最容易积累脏数据，所以清理是重点 ────────────────────
#   档案只有一个当前值，改完还原就行；饮食记录是**列表，会越跑越多**。
#   不清理的话：
#     · 一周 10 轮 × 3 条 = 30 条"自动化三文鱼沙拉"堆在用户列表里
#     · 表格翻页、ECharts 趋势图被假数据拉平
#     · AI 饮食建议基于这些假记录给结论 —— 后面看到的"建议很奇怪"其实怪测试
#   所以本模块的每条用例都通过 temp_record 夹具建数据，夹具负责删干净。
#
# ── 菜品名为什么要带时间戳 ────────────────────────────────────
#   用例并发 / 上次异常退出残留时，同名记录会有多条，
#   `filter(has_text=名字)` 会一次命中多行，删除时删错行、断言时永远绿。
#   带时间戳后名字全局唯一，定位和清理都是确定的。

import re
import time
from datetime import datetime

import pytest

from pages.diet_record_page import DietRecordPage


def unique_name(prefix="自动化-三文鱼沙拉"):
    return f"{prefix}-{int(time.time() * 1000) % 100000}"


def today():
    return datetime.now().strftime("%Y-%m-%d")


@pytest.fixture
def temp_record(user_page):
    """建一条记录 → 交给用例 → 删干净。"""
    name = unique_name()

    page = DietRecordPage(user_page).open()
    page.expect_loaded()
    page.add_record(name, today(), meal_value="lunch")

    yield name

    try:
        DietRecordPage(user_page).open().delete_record(name)
    except Exception as exc:  # noqa: BLE001
        # 清不掉必须让人看见 —— 否则下一轮会出现"为什么有一条同名老数据"的困惑
        print(f"\n  ⚠ 饮食记录 {name} 清理失败，请在界面上手动删除：{exc}")


class TestCreateRecord:

    def test_新增饮食记录_列表里能查到(self, temp_record, user_page):
        """这条用例的主体在夹具里（建完就能看到），这里补一条列表查询的验证。

        为什么要「再查询一次」：新增后前端是本地插入还是重新拉列表，
        对用户来说没区别，但对"刷新后还在不在"有区别 ——
        从没真正落库的记录，刷新就消失了。
        重新 open + 查询 = 走一遍真实读取链路。
        """
        page = DietRecordPage(user_page).open()
        page.expect_loaded()
        page.search()

        page.expect_row(temp_record)
        assert page.row_calories(temp_record) not in (None, "", "--"), "热量列没有值"

    def test_未填食材明细_保存被拦住(self, user_page):
        """只填日期和菜品名、不填任何食材 → 不允许保存。

        ⚠️ 这条的判据是"**弹窗没关**"，而不是"有提示"。
           提示文案会改（现在叫"请至少添加一项食材明细"），
           但"没食材不能存"是业务规则。
           只断提示会变成"文案一变就红"，断弹窗才是断规则。
        """
        page = DietRecordPage(user_page).open()
        page.expect_loaded()

        page.open_add_dialog()
        page.fill_date(today())
        page.pick_meal("dinner")
        page.fill_food_name(unique_name("自动化-无食材"))
        page.save()

        # 弹窗还在 = 请求根本没发出去
        page.expect_visible(page.dialog())
        page.toast("请至少添加一项食材明细")

    def test_必填项为空_表单校验拦截(self, user_page):
        """什么都不填直接保存 → 校验红字出现，弹窗不关。"""
        page = DietRecordPage(user_page).open()
        page.expect_loaded()

        page.open_add_dialog()
        page.save()

        page.expect_visible(page.dialog())
        # 三个必填项（日期/餐次/菜品名）都该报错；这里只验"至少报了"
        page.expect_visible(page.dialog().locator(".el-form-item__error").first)


class TestDeleteRecord:

    def test_删除记录后列表不再出现(self, temp_record, user_page):
        """删除链路：点删除 → 二次确认 → 记录消失。

        刻意**不用**夹具的收尾删除，而是在用例里删：
          夹具的删除是"清理"，用例的删除是"被测行为"。
          两者代码相同但目的不同 —— 混在一起，
          清理一失败就会让人以为删除功能坏了（或者反过来，坏了也看不出来）。
          所以这里删完之后，夹具收尾时发现记录已不在，直接返回（幂等）。
        """
        page = DietRecordPage(user_page).open()
        page.expect_loaded()
        page.expect_row(temp_record)

        page.delete_record(temp_record)

        page.expect_no_row(temp_record)

    def test_删除时点取消_记录还在(self, temp_record, user_page):
        """二次确认点「取消」不能删掉记录。

        这是删除的**对照组**。只测"点删除能删"的话，
        一个"对话框没等用户确认就删了"的缺陷会被漏掉 ——
        那可是误删用户数据的级别。
        """
        page = DietRecordPage(user_page).open()
        page.expect_loaded()

        row = page.row_by_food(temp_record)
        row.get_by_role("button", name="删除").click()

        box = user_page.locator(".el-message-box:visible").last
        box.get_by_role("button", name="取消").click()

        page.expect_row(temp_record)
