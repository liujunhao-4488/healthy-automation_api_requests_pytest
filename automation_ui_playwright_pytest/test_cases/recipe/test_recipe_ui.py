# test_cases/recipe/test_recipe_ui.py
# 食谱库 / 我的食谱 —— 用户自建内容的全生命周期（增 / 改 / 删 / 查）
#
# 为什么这组必须存在：
#   这是产品里唯一的 UGC 入口之一，"我的食谱"里建的东西是真实数据，
#   接口层能验字段，验不了这几件事：
#     · 建完是不是**立刻出现在列表里**（前端 loadCustom 有没有接上）
#     · 校验失败时弹层该不该关（关了就丢用户已填的内容）
#     · 删掉后列表有没有真刷新（删了但卡片还在，是最常见的半成功）
#
# 数据卫生（这组最关键的一条）：
#   所有建出来的食谱都会在用例结束时删掉（cleanup.recipe），
#   名称带唯一后缀，避免和上一次的残骸撞名导致假绿。

import re

from playwright.sync_api import expect

from common.seed import seed_recipe
from pages.recipes_page import RecipesPage


class TestCustomRecipe:
    def test_新建自定义食谱_出现在我的食谱列表(self, user_page, cleanup, unique):
        """主流程：填弹层 → 保存 → 弹层关闭 → 我的食谱里能看到。

        「弹层关闭」不是形式主义：saveCustom 里只有接口 code===200
        才关弹层，所以"关了"本身就是"后端认了"的旁证。
        反过来说，如果关了但列表里没有，问题在 loadCustom 没刷新 —— 两种缺陷分得清。
        """
        name = unique("自动化食谱")

        recipes = RecipesPage(user_page).open()
        recipes.expect_loaded()
        recipes.open_create()
        assert "新建" in recipes.modal_title(), f"弹层标题不对：{recipes.modal_title()!r}"

        recipes.fill(
            name=name,
            kcal=486,
            steps="意面下沸水煮 8 分钟\n鸡胸切条煎熟\n番茄炒出汁后翻匀",
            ingredients="全麦意面 70 g\n鸡胸肉 120 g\n番茄 2 个",
        )
        recipes.pick_fit("减脂")
        recipes.save()
        recipes.expect_saved()

        recipes.switch_view("我的食谱")
        recipes.expect_card(name)

        rid = recipes.card_id(name)
        assert rid, "卡片链接里没取到食谱 id，无法登记清理"
        cleanup.recipe(rid)

    def test_缺制作步骤_保存被拦且弹层不关(self, user_page):
        """校验矩阵里最容易被漏的一条：有名称、有热量、有适宜目标，但没有步骤。

        前端校验是**按顺序短路**的（名称 → 热量 → 步骤 → 适宜目标），
        所以要一次只违反一条。四条全违反只能测到第一条。
        """
        recipes = RecipesPage(user_page).open()
        recipes.expect_loaded()
        recipes.open_create()

        recipes.fill(name="缺步骤的食谱", kcal=300)
        recipes.pick_fit("减脂")
        recipes.save()

        recipes.expect_rejected("请至少填写一个制作步骤")

    def test_编辑自定义食谱_名称更新生效(self, user_page, account, cleanup, unique):
        """编辑：前置数据走接口造（只测编辑动作本身），改完列表要换成新名。

        断言"新名出现 + 旧名消失"两件事：
          只断言新名出现，遇到"另存为新记录"（而不是更新原记录）会漏 ——
          那正是 PUT 写成 POST 的典型症状。
        """
        old_name = unique("待编辑食谱")
        rid = seed_recipe(account, old_name)
        cleanup.recipe(rid)

        recipes = RecipesPage(user_page).open()
        recipes.expect_loaded()
        recipes.switch_view("我的食谱")
        recipes.expect_card(old_name)

        recipes.open_edit(old_name)
        assert "编辑" in recipes.modal_title(), f"打开的不是编辑弹层：{recipes.modal_title()!r}"

        new_name = old_name + "改写"
        recipes.fill(name=new_name)
        recipes.save()
        recipes.expect_saved()

        recipes.expect_card(new_name)
        assert old_name not in recipes.card_names(), "旧名称的卡还在，说明是新增了一条而不是更新原记录"

    def test_删除自定义食谱_列表移除(self, user_page, account, cleanup, unique):
        """删除：确认框点「删除」→ 卡片消失。

        删除是"软删"（后端 status 置位），所以断言要看**列表**，
        不能看接口返回值 —— 接口说成功但列表没刷新的情况真实存在。
        """
        name = unique("待删除食谱")
        rid = seed_recipe(account, name)
        cleanup.recipe(rid)  # 双保险：UI 删失败时接口兜底（重复删会 404，清理忽略）

        recipes = RecipesPage(user_page).open()
        recipes.expect_loaded()
        recipes.switch_view("我的食谱")
        recipes.expect_card(name)

        recipes.delete(name)
        recipes.expect_card_gone(name)


class TestRecipeSearch:
    def test_食谱库关键词搜索_命中与空态(self, user_page):
        """搜索是**前端内存过滤**（后端 /recipe/list 一次给全量，前端筛）。

        两向都测：命中（能搜到）+ 空态（搜不到时是空态而不是"还显示全部"）。
        只测命中会漏掉"清空关键词没生效""过滤条件没接上"这类问题 ——
        它们在"能搜到"的方向上全是绿的。
        """
        recipes = RecipesPage(user_page).open()
        recipes.expect_loaded()

        # ① 搜一个必然搜不到的词 → 空态
        recipes.search("zzz这个食材肯定不存在zzz")
        expect(recipes.page.get_by_text("没有符合条件的食谱", exact=True)).to_be_visible()

        # ② 换成能搜到的词 → 空态消失、有结果
        #    先断言空态消失再断言有卡：只断言"有卡"的话，
        #    上一次刷新的旧结果也能让断言通过（空态到结果的过渡没被验证）。
        recipes.search("鸡胸")
        expect(recipes.page.get_by_text("没有符合条件的食谱", exact=True)).to_be_hidden()
        expect(recipes.page.locator("article.recipe-card:visible h3").first).to_be_visible()
        assert recipes.library_card_names(), "搜「鸡胸」结果标题列表为空"
