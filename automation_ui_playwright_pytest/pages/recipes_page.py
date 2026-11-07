# pages/recipes_page.py
# 食谱库 / 我的食谱（front2/src/views/RecipesView.vue）
#
# 一页两个视图（.recipe-tabs 切换）：
#   · 食谱库 —— 平台食谱，可筛选、搜索、收藏
#   · 我的食谱 —— 自定义食谱（可增删改）+ 已收藏
#
# 新建/编辑共用一个弹层，靠 h3 文案区分「新建自定义食谱」和「编辑自定义食谱」。
# 保存前的校验在 saveCustom() 里：名称 → 热量 >0 → 至少一步 → 至少一个适宜目标，
# **按顺序短路**，所以校验用例必须一次只违反一条，否则测到的是前一条规则。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT
from pages.base_page import BasePage


class RecipesPage(BasePage):
    path = "/recipes"

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        expect(self.page.get_by_role("heading", name="食谱库", exact=True)).to_be_visible(
            timeout=timeout
        )
        return self

    # ---------------- 视图切换 ----------------

    def switch_view(self, label):
        """切「食谱库 / 我的食谱」。"""
        self.page.locator(".recipe-tabs").get_by_role("button", name=label, exact=False).first.click()
        expect(self.page.get_by_role("heading", name=label, exact=True)).to_be_visible(
            timeout=EXPECT_TIMEOUT
        )
        return self

    # ---------------- 食谱库 ----------------

    def search(self, keyword):
        """库内搜索。

        注意这是**纯前端过滤**（后端 /recipe/list 一次返回全量，前端在内存里筛），
        所以没有网络请求可以等 —— 判断"结果出没出"只能看骨架屏（.sk）收没收。
        """
        box = self.page.get_by_placeholder("搜索食谱名称或食材")
        box.fill(keyword)
        box.press("Enter")
        return self

    def wait_results(self, timeout=EXPECT_TIMEOUT):
        """等列表落定：骨架屏消失。

        为什么必须有这一步：加载中渲染的骨架卡也是 `article.recipe-card`
        （只是没有 h3），所以"等第一张卡可见"会立刻通过、然后读到空标题列表 ——
        这类"等到假元素"是 UI 用例最常见的假失败来源。
        """
        expect(self.page.locator(".sk")).to_have_count(0, timeout=timeout)
        return self

    def library_card_names(self):
        """库里当前可见的卡片标题。

        必须加 :visible —— 两个视图用 v-show 切换，隐藏那半仍在 DOM 里。
        不加的话"我的食谱"里的卡也会被数进来，搜索结果断言就永远是绿的。
        """
        return [
            el.inner_text().strip()
            for el in self.page.locator("article.recipe-card:visible h3").all()
        ]

    # ---------------- 我的食谱 ----------------

    def card(self, name):
        """按名称定位一张食谱卡。

        用 h3 里的链接文案圈定，而不是 has_text 全文匹配：
        卡片里还有简介、营养、时长等文字，has_text 是子串匹配，
        名称刚好是另一张卡的简介开头时会串。
        """
        return self.page.locator("article.recipe-card:visible").filter(
            has=self.page.get_by_role("link", name=name, exact=True)
        ).first

    def card_names(self):
        return [
            el.inner_text().strip()
            for el in self.page.locator("article.recipe-card:visible h3").all()
        ]

    def expect_card(self, name, timeout=EXPECT_TIMEOUT):
        expect(self.card(name)).to_be_visible(timeout=timeout)
        return self

    def expect_card_gone(self, name, timeout=EXPECT_TIMEOUT):
        """等这张卡从可见列表里消失（删除生效的判据）。"""
        expect(self.page.locator("article.recipe-card:visible").filter(
            has=self.page.get_by_role("link", name=name, exact=True)
        )).to_have_count(0, timeout=timeout)
        return self

    def card_id(self, name):
        """从卡片链接里取食谱 id（/recipes/123 → 123）。

        为什么从 DOM 里抠 id：用例建了数据还要负责清理，
        删除接口只认 id。走 UI 建的数据，id 不会回传到 Python 侧，
        详情页链接是唯一能"读回来"的地方。
        """
        href = self.card(name).get_by_role("link").first.get_attribute("href") or ""
        m = re.search(r"/recipes/(\d+)", href)
        return int(m.group(1)) if m else None

    # ---------------- 新建 / 编辑弹层 ----------------

    def open_create(self):
        """打开新建弹层。

        注意「新建食谱」按钮**不在食谱库浏览模式的页头里**：
          页头 `.page-actions` 是 v-if（library && browse）→ 只有搜索 + 换一批；
          v-else 分支才放「新建食谱」，也就是"我的食谱"视图或智能配餐模式。
        所以库里找不到这个按钮是**正常**的，不是页面坏了 ——
        自动切到"我的食谱"再点，比在用例里散落这段判断强。
        """
        btn = self.page.locator(".page-actions").get_by_role(
            "button", name=re.compile("新建食谱")
        )
        if btn.count() == 0:
            self.switch_view("我的食谱")
            btn = self.page.locator(".page-actions").get_by_role(
                "button", name=re.compile("新建食谱")
            )
        btn.first.click()
        expect(self.modal()).to_be_visible(timeout=EXPECT_TIMEOUT)
        return self

    def open_edit(self, name):
        self.card(name).get_by_role("button", name="编辑", exact=True).click()
        expect(self.modal()).to_be_visible(timeout=EXPECT_TIMEOUT)
        return self

    def modal_title(self):
        return self.modal().locator(".modal-hd h3").first.inner_text().strip()

    def fill(self, name=None, kcal=None, steps=None, ingredients=None, meal_type=None):
        """填弹层。只填传了的字段，方便用例只改动一项。"""
        box = self.modal()
        if name is not None:
            box.get_by_placeholder("例如：番茄鸡胸意面").fill(name)
        if kcal is not None:
            box.locator(".field").filter(has=self.page.get_by_text("热量（kcal）", exact=True)).locator("input").fill(str(kcal))
        if steps is not None:
            box.locator(".field").filter(has=self.page.get_by_text("制作步骤", exact=False)).locator("textarea").fill(steps)
        if ingredients is not None:
            box.locator(".field").filter(has=self.page.get_by_text("食材清单", exact=False)).locator("textarea").fill(ingredients)
        if meal_type is not None:
            box.locator(".field").filter(has=self.page.get_by_text("餐次", exact=True)).locator("select").select_option(meal_type)
        return self

    def pick_fit(self, name):
        """确保某个「适宜目标」处于选中态。

        ⚠️ 是"确保选中"，不是"点一下就选中"：
          新建表单的 blankForm() 里 fit 默认是 ['减脂'] —— 直接点会把它**取消掉**，
          然后保存时撞上「请至少选择一个适宜目标」，看起来像按钮坏了，
          实际是用例的假设错了。这个坑和饮食偏好那组一模一样：
          凡是 chip/toggle 类控件，正确姿势都是"先读状态，缺了才点"。
        """
        card = self.modal()
        btn = card.locator(".field").filter(
            has=self.page.get_by_text("适宜目标", exact=True)
        ).get_by_role("button", name=name, exact=True)
        if "on" not in (btn.get_attribute("class") or "").split():
            btn.click()
        return self

    def save(self):
        self.modal().locator(".modal-ft").get_by_role(
            "button", name=re.compile("保存食谱|保存中")
        ).first.click()
        return self

    def cancel(self):
        self.modal().locator(".modal-ft").get_by_role("button", name="取消", exact=True).click()
        return self

    def expect_saved(self, timeout=EXPECT_TIMEOUT):
        """保存成功 = 非 error 提示 + 弹层关闭。

        弹层关闭是"真的存进去了"的旁证：saveCustom 里只有 code===200
        才会 modalOpen=false，接口失败会保持打开让用户改。
        """
        self.expect_success_toast(timeout=timeout)
        self.expect_modal_closed(timeout=timeout)
        return self

    def expect_modal_closed(self, timeout=EXPECT_TIMEOUT):
        expect(self.page.locator(".overlay.open")).to_have_count(0, timeout=timeout)
        return self

    def expect_rejected(self, text, timeout=EXPECT_TIMEOUT):
        """被拦下：出现红色提示，且弹层**仍然开着**。

        第二半句才是关键：如果只断言提示，遇到"提示弹了但数据也存进去了"
        （校验写成事后校验）会漏 —— 弹层还开着才说明真的没提交。
        """
        super().expect_rejected(text, timeout=timeout)
        expect(self.modal()).to_be_visible(timeout=timeout)
        return self

    # ---------------- 删除 ----------------

    def delete(self, name):
        """删除自定义食谱：点删除 → 二次确认框点「删除」。

        前端用的是 confirmDialog（.overlay.open .modal），危险操作按钮文案是「删除」，
        和卡片上那个「删除」按钮同名 —— 所以确认框必须用 confirm_dialog 从弹层里取，
        不能再用 card 作用域。
        """
        self.card(name).get_by_role("button", name="删除", exact=True).click()
        self.confirm_dialog(ok_text="删除")
        return self
