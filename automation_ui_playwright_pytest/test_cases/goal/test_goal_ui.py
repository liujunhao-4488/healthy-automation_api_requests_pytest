# test_cases/goal/test_goal_ui.py
# 饮食目标 —— 前端计算 + 后端持久化
#
# 这组用例存在的理由（和接口层的分工）：
#   接口层只能验"存进去的四个数字对不对"；
#   这一页真正容易坏的是**算给你看的那部分**：
#     · 目标类型 → 推荐热量区间（Mifflin-St Jeor × 类型系数）
#     · 拖动一项营养素 → 另外两项按原比例修正、总和恒 100%
#     · 体重进度、饮水估算
#   这些在接口层完全不可见（接口只收到最终结果），只能在这里验。
#
# 数据卫生：
#   目标是**账号级状态**（不是列表数据），改完会影响后续用例和人工演示，
#   所以主流程那条先快照原值、跑完用接口恢复（cleanup.task）。

import re

from playwright.sync_api import expect

from common.cleanup import api
from common.seed import goal_restore_payload
from pages.goal_page import GoalPage


class TestGoal:
    def test_修改目标类型与热量_保存后刷新仍生效(self, user_page, account, cleanup):
        """主流程：改类型 + 改热量 → 保存 → 刷新仍生效。

        为什么保存后要再刷新断言一次：
          只断言 toast，测的是"前端弹没弹提示"，不是"数据落没落库"。
          接口 200 但后端字段名对不上被静默忽略时，toast 依然是绿的。
          刷新会重新 GET，能抓到这类"半成功"。
        """
        resp = api("GET", "/health/goal", account["token"])
        snapshot = resp.json().get("data") if resp.status_code < 400 else None
        if snapshot:
            # ① 只回灌用户可写的字段（GET 包里含 id/createTime 等服务端字段）
            # ② 用 restore 而不是 task：写回失败必须喊出来，否则账号目标是永久脏的
            cleanup.restore("POST", "/health/goal", goal_restore_payload(snapshot))

        goal = GoalPage(user_page).open()
        goal.expect_loaded()

        goal.pick_type("增肌")
        goal.set_kcal(2200)
        goal.save()
        goal.expect_saved()

        goal.reload()
        goal.expect_loaded()
        assert goal.kcal_value() == 2200, "刷新后热量目标不是刚保存的值，说明没真正落库"
        assert goal.current_type() == "增肌", "刷新后目标类型回退了"

    def test_拖动蛋白质滑块_三大营养素合计恒为100(self, user_page):
        """前端的"自动配平"：推任意一项，另外两项按原比例修正，总和永远 100%。

        这是这一页最有价值的 UI 级断言 —— 后端只收三个整数，
        真正保证"用户怎么拖都不会拖出 99% 或 101%"的是前端这段逻辑。
        用键盘推滑块而不是直接改 value：逻辑挂在 @input/@change 上，
        直接赋值不触发事件，等于绕过被测代码自问自答。
        """
        goal = GoalPage(user_page).open()
        goal.expect_loaded()

        before = goal.macro_percent("蛋白质占比")
        for i in range(3):
            goal.nudge_macro("蛋白质占比", steps=4)
            assert goal.macro_sum() == 100, f"第 {i + 1} 次拖动后合计不再是 100%"

        assert goal.macro_percent("蛋白质占比") > before, "推了 12 次右方向键，蛋白质占比没涨"

    def test_热量低于下限_保存被拦且请求未发出(self, user_page):
        """热量越界：前端拦下，且**请求根本没发出去**。

        只断言 toast 是不够的：先发请求再弹提示也算"拦下"，
        但那样后端会收到非法值（真出过这类问题：前端校验写成事后提示）。
        监听网络请求才能区分"拦住了"和"拦晚了"。
        """
        goal = GoalPage(user_page).open()
        goal.expect_loaded()

        posted = []
        user_page.on(
            "request",
            lambda r: posted.append(r.url) if r.method == "POST" and "/health/goal" in r.url else None,
        )

        goal.set_kcal(500)
        goal.save()
        goal.expect_rejected("每日热量目标需在 1000–4000 kcal 之间")

        assert not posted, "前端校验没生效：非法热量已经发到后端了"

    def test_采用建议值_热量被填成推荐值(self, user_page):
        """「采用建议值」是纯前端计算（基础代谢 × 类型系数 ± 幅度），必须能用。"""
        goal = GoalPage(user_page).open()
        goal.expect_loaded()

        goal.pick_type("减脂")
        goal.page.get_by_role("button", name=re.compile("采用建议值")).click()

        goal.toast("已采用建议热量值")
        value = goal.kcal_value()
        assert 1000 <= value <= 4000, f"建议值 {value} 落在了合法区间之外"

    def test_体重低于下限_保存被拦(self, user_page):
        """体重 30–200kg 的下限校验。上限由同一条规则覆盖，不重复写。"""
        goal = GoalPage(user_page).open()
        goal.expect_loaded()

        goal.set_current_weight(20)
        goal.save()
        goal.expect_rejected("体重需在 30–200kg 之间")
