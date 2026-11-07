# test_cases/health/test_health_profile_ui.py
# 健康档案：展示页读取 + 编辑保存 + 路由守卫。
#
# ── 这组用例的两条设计原则 ─────────────────────────────────────
#   1) **只验 UI 该验的**：回显对不对、保存后页面有没有更新、派生值（BMI/BMR）有没有重算。
#      不验营养学公式本身 —— 那是后端/算法的单元测试，UI 只要"显示的是后端返回的值"。
#   2) **改了什么就还原什么**。档案全局只有一份，被写成 75kg 之后：
#        · 下一轮"基线断言"全红
#        · AI 建议、食谱推荐的结果也跟着变
#      所以下面的 restore_weight 夹具是必须的，不是可选的清洁工作。
#      真出过问题的项目，通常是"某条用例改完没还原，三天后整个档案模块开始飘"。

import re

import pytest
from playwright.sync_api import expect

from config.config import PROFILE
from pages.base_page import BasePage
from pages.health_profile_page import HealthProfilePage


def _expected_bmi(weight, height_cm=PROFILE["height"]):
    return round(weight / ((height_cm / 100) ** 2), 1)


@pytest.fixture
def restore_weight(user_page):
    """记下改之前的体重，用例结束后写回去。

    刻意做成 fixture 而不是写在用例的 try/finally 里：
      用例中途失败时，pytest 仍会执行 fixture 的收尾；
      而用例自己写 finally，一旦断言在 finally 之前抛错、又赶上编辑器里手动中断，
      还原就被跳过了 —— 那种残留会静默影响后面所有轮次。
    """
    page = HealthProfilePage(user_page).open()
    page.expect_loaded()
    original = page.read_weight()

    yield original

    # 还原也走 UI（不走接口）：这个用例验的就是"UI 保存能不能落库"，
    # 如果还原走接口，就分不清"没落库"是保存坏了还是还原坏了。
    try:
        edit = HealthProfilePage(user_page).open().goto_edit()
        edit.set_weight(original).save_and_expect_success()
    except Exception as exc:  # noqa: BLE001
        # 还原失败不能盖住用例本身的失败，但必须让人看见 —— 否则下一轮全红却没人知道为什么
        print(f"\n  ⚠ 档案体重还原失败，基线可能已漂移：{exc}")


class TestHealthProfileDisplay:

    def test_档案页回显与基线一致(self, user_page):
        """页面显示的体重 / BMI 与 config.PROFILE 一致。

        ⚠️ 这条用例是**基线探测器**，不是功能测试。
           它红了有两种可能：
             a) 真的显示错了（缺陷）
             b) 上一轮某条用例改了档案没还原（测试自身的卫生问题）
           两种都要处理，但处理方式完全不同 ——
           所以失败信息里把"期望值来自哪里"写清楚，别让人猜。
        """
        page = HealthProfilePage(user_page).open()
        page.expect_loaded()

        weight = page.read_weight()
        assert weight == pytest.approx(PROFILE["weight"], abs=0.2), (
            f"页面体重 {weight} 与基线 {PROFILE['weight']} 不符。\n"
            f"基线来自 config.PROFILE（可用 AUTOTEST_UI_PROFILE_WEIGHT 覆盖）。\n"
            f"如果这个账号的档案被改过，先确认是缺陷还是上一轮没还原。"
        )
        assert page.read_bmi() == pytest.approx(_expected_bmi(PROFILE["weight"]), abs=0.2)

    def test_基础信息项都有值(self, user_page):
        """年龄 / 性别 / 身高 不能显示成 '--'。

        为什么单列一条：这三个字段是"新用户引导"和"AI 建议"的输入前提，
        缺任何一个，页面不报错、接口也不报错，只是后续推荐变差 ——
        属于"静默降级"，不主动断言就永远发现不了。
        """
        page = HealthProfilePage(user_page).open()
        page.expect_loaded()

        for label in ("年龄", "性别", "身高"):
            value = page.info_value(label).inner_text().strip()
            assert value and value != "--", f"档案里的「{label}」没有值"


class TestHealthProfileEdit:

    def test_修改体重_保存后回显更新且BMI重算(self, user_page, restore_weight):
        """改体重 → 保存 → 回到展示页 → 体重和 BMI 都变了。

        断言两组值，是因为它们**分别会单独坏**：
          · 体重没变 → 保存请求没发出去 / 后端没落库
          · 体重变了但 BMI 没变 → 前端保存后没把重算的 bmi 一起写回 store，
            或者后端算了但没返回 —— 用户看到的是"BMI 一直是老值"，
            比体重错更难发现，因为它看起来"挺正常"。
        """
        new_weight = round(restore_weight + 3, 1)

        edit = HealthProfilePage(user_page).open().goto_edit()
        edit.set_weight(new_weight).save_and_expect_success()

        page = HealthProfilePage(user_page)
        page.expect_loaded()

        assert page.read_weight() == pytest.approx(new_weight, abs=0.2)
        assert page.read_bmi() == pytest.approx(_expected_bmi(new_weight), abs=0.2), (
            "体重改了但 BMI 没跟着变：检查保存后是否把重算的 bmi 一并写回 store"
        )

    def test_编辑页预填的是当前值(self, user_page, restore_weight):
        """进编辑页时表单里应该是库里的值，不是空表单。

        空表单会让用户在"不知道自己原来是什么"的情况下覆盖掉数据，
        属于体验缺陷，但后果是数据丢失 —— 值得一条用例。
        """
        edit = HealthProfilePage(user_page).open().goto_edit()

        assert edit.get_number("体重") == pytest.approx(restore_weight, abs=0.2)
        assert edit.get_number("年龄") not in ("", "--")

    def test_取消编辑不落库(self, user_page, restore_weight):
        """改成另一个值后点「取消」，展示页应该还是老值。

        这是"取消"和"保存"的对照：
          只测保存生效，测不出"取消其实也保存了"这类坑。
        """
        page = HealthProfilePage(user_page).open()
        page.expect_loaded()
        before = page.read_weight()

        edit = page.goto_edit()
        edit.set_weight(round(before + 7, 1))
        edit.by_role_button("取消").click()

        after = HealthProfilePage(user_page)
        after.expect_loaded()
        assert after.read_weight() == pytest.approx(before, abs=0.2), "点了取消，档案却被改了"


class TestRouteGuard:
    """路由守卫 —— 只有靠"控制登录态"才测得出来的东西。

    这是 token 直注的**第二个价值**（第一个是快）：
      它能把浏览器摆到"已登录 / 未登录 / 有档案 / 没档案"四种指定状态，
      而用真实登录去摆状态，至少要两个账号、几十秒。
    """

    def test_未登录访问业务页_被踢回登录页(self, page):
        """干净上下文（没注入 token）直接访问 /dashboard/health-info。"""
        BasePage(page).open("/dashboard/health-info")

        expect(page).to_have_url(re.compile(r"/login/?$"), timeout=10000)

    def test_档案已完成后_再访问引导页会被送回档案页(self, user_page):
        """档案完整的用户手动输 /health-info-basic 不该停在那儿。

        这条规则很容易在改路由时被删掉，而删掉后**没有任何页面会报错**，
        只是用户可以反复进到一个"让你重新填档案"的页面，
        填完再覆盖掉现有数据 —— 属于数据丢失类缺陷。
        """
        BasePage(user_page).open("/health-info-basic")

        expect(user_page).to_have_url(
            re.compile(r"/dashboard/health-info/?$"), timeout=10000
        )

    def test_档案未完成时_引导页放行(self, guest_profile_page):
        """反过来：没有档案的用户必须能进到引导页，否则新用户就被卡死了。

        和上一条合起来才构成完整判据：
          只测"有档案的进不去"，测不出"没档案的也进不去" ——
          后者会让所有新注册用户看到一片空白。
        """
        BasePage(guest_profile_page).open("/health-info-basic")

        expect(guest_profile_page).to_have_url(
            re.compile(r"/health-info-basic/?$"), timeout=10000
        )
