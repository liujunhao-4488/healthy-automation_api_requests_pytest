# pages/account_page.py
# 个人中心（front2/src/views/AccountView.vue）
#
# 一页装五件事：账号资料 / 饮食偏好 / 我的收藏 / 阅读历史 / 通知中心。
# 结构上是个 tab-panel，**五个面板同时挂在 DOM 里**，靠 v-show 切显隐 ——
# 所以这里的每个选择器都必须限定在 `section.tab-panel:visible` 里，
# 否则会命中隐藏面板里的同名元素（比如"保存"按钮隐藏面板里也有几个）。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT
from pages.base_page import BasePage


class AccountPage(BasePage):
    path = "/account"

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        expect(self.page.get_by_role("heading", name="个人中心", exact=True)).to_be_visible(
            timeout=timeout
        )
        return self

    # ---------------- tab ----------------

    @property
    def panel(self):
        """当前可见的那个 tab 面板。所有面板内元素都从它下面找。"""
        return self.page.locator("section.tab-panel:visible").first

    def open_tab(self, label):
        self.page.locator(".tabs").get_by_role("button", name=re.compile(rf"^{re.escape(label)}")).first.click()
        # 等面板真的切过去：v-show 只改 display，所以要等"可见性"而不是"存在性"
        expect(self.panel).to_be_visible(timeout=EXPECT_TIMEOUT)
        return self

    # ---------------- 账号资料 ----------------

    @property
    def username_input(self):
        # 前端给这个框留了 id（pfName），是全页最稳的锚点，优先用 id
        return self.page.locator("#pfName")

    @property
    def email_input(self):
        return self.panel.locator('input[type="email"]').first

    @property
    def phone_input(self):
        return self.panel.locator('input[type="tel"]').first

    def set_username(self, name):
        self.username_input.fill(name)
        return self

    def username(self):
        return self.username_input.input_value()

    def set_phone(self, phone):
        self.phone_input.fill(phone)
        return self

    def save_profile(self):
        self.panel.get_by_role("button", name=re.compile("保存资料|保存中")).first.click()
        return self

    def expect_profile_saved(self, timeout=EXPECT_TIMEOUT):
        self.toast("资料已更新", timeout=timeout)
        return self

    # ---------------- 饮食偏好 ----------------

    @property
    def _pref_card(self):
        """口味与禁忌卡片。不圈范围的话，下面「每日餐次」的 .seg 也会被当成 chip 选项。"""
        return self.panel.locator("article.card").filter(
            has=self.page.get_by_role("heading", name="口味与禁忌", exact=True)
        ).first

    def toggle_pref(self, name):
        """勾选/取消一个偏好 chip。名字在 DIET / ALLERGENS / DISLIKES / LIKES 里。"""
        self._pref_card.get_by_role("button", name=name, exact=True).click()
        return self

    def pref_selected(self, name):
        """某个偏好是否处于选中态（选中带 .on 类，不靠背景色判断）。"""
        cls = self._pref_card.get_by_role("button", name=name, exact=True).get_attribute("class") or ""
        return "on" in cls.split()

    def save_prefs(self):
        self._pref_card.get_by_role("button", name=re.compile("保存偏好|保存中")).first.click()
        return self

    def expect_prefs_saved(self, timeout=EXPECT_TIMEOUT):
        self.toast("饮食偏好已保存", timeout=timeout)
        return self
