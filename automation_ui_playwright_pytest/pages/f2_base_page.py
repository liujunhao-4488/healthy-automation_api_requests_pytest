# pages/f2_base_page.py
# 作用：front2（膳衡重写版）Page Object 的公共底座。
#
# 和老版 base_page.py 的根本区别：**front2 是零依赖实现，没有 Element Plus**。
# 老版那套 .el-form-item / .el-select-dropdown / .el-message 定位全部作废，
# 这里按 front2 自己的 DOM 重建，组件名和源码（front2/src）一一对应：
#
#   轻提示        ToastHost.vue      → .toast-wrap .toast（error 类名区分红/绿）
#   二次确认      ConfirmDialog.vue  → .overlay.open .modal（按钮文案由 okText 决定）
#   表单项        各 View 里的 .field（<label> + input/textarea，label 没有 for 关联）
#   分段选择      .seg（一排 button，选中项带 .on）
#   多选 chip     .chip（选中项带 .on）
#
# 定位策略和老版一致：没有 data-testid，靠语义（placeholder / 可访问名 / 文案）。
# front2 有一个优势要利用上：关键输入框带 id（foodSearch / gramsInput / noteInput），
# 弹窗里的操作优先用 id，比文案稳。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT, FRONT2_URL

from pages.base_page import BasePage


class F2BasePage(BasePage):
    """front2 所有 Page Object 的父类。

    继承老版 BasePage 只为了拿导航 / expect 辅助那部分通用逻辑；
    Element Plus 专属的 form_item / el_select / table_rows 在 front2 里
    不要用 —— 留在父类里不碍事，但子类一律用下面这套 f2_* 方法。
    """

    def __init__(self, page, base_url=None):
        # 默认指向 front2 的 dev server（5174），别吃老版的默认值
        super().__init__(page, base_url or FRONT2_URL)

    # ---------------- 定位辅助（front2 专属） ----------------

    def f2_field(self, label, exact=True):
        """按 label 文案抓一个表单项 .field。

        front2 的 label 没有 for 属性、input 也没有 id（弹窗里那几个除外），
        只能靠"包含这段文案的 .field"来圈定范围。
        用 exact：'年龄（岁）' 和 '年龄' 是两个不同的字段，模糊匹配会填错框。
        """
        return self.page.locator(".field").filter(
            has=self.page.get_by_text(label, exact=exact)
        ).first

    def f2_input(self, label, exact=True):
        """表单项里的输入控件（input 或 textarea 都覆盖）。"""
        return self.f2_field(label, exact=exact).locator("input, textarea").first

    def seg_option(self, scope, name, exact=True):
        """.seg 分段选择里的一个选项按钮。

        scope 必传：性别、餐次的 .seg 都不止一个，不圈范围会点到别的。
        用 get_by_role（可访问名匹配）而不是 has_text 正则锚点：
          Vue 模板 `{{ name }}` 渲染出来的按钮 innerText 带换行缩进，
          ^name$ 永远匹配不上；可访问名会做空白归一化，稳。
        """
        return scope.get_by_role("button", name=name, exact=exact)

    def chip(self, scope, name):
        """多选 chip 按钮（慢病 / 饮食偏好）。scope 同样必传。"""
        return scope.get_by_role("button", name=name, exact=True)

    # ---------------- 反馈类（全局组件，DOM 与 Element Plus 完全不同） ----------------

    def toast(self, text=None, timeout=EXPECT_TIMEOUT):
        """轻提示（ToastHost）。

        和 el-message 一样的两个坑这里也有：
          · 2.6s 后自动淡出，断言必须用 expect 等"出现"，不能睡一觉再看；
          · 连续动作会叠出多条，filter(has_text=...) 后取 first。
        返回 locator 而不是 self：调用方经常还要断言它有 error 类（红色报错），
        返回 locator 才能继续 .to_have_class()。
        """
        wrap = self.page.locator(".toast-wrap .toast:visible")
        if text is None:
            loc = wrap.first
        else:
            loc = wrap.filter(has_text=text).first
        expect(loc).to_be_visible(timeout=timeout)
        return loc

    def wait_toast_gone(self, timeout=EXPECT_TIMEOUT):
        """等当前提示全部消失。删除/保存后的连续动作前要用它，否则会点到半透明的 toast。"""
        expect(self.page.locator(".toast-wrap .toast")).to_have_count(0, timeout=timeout)
        return self

    def confirm_dialog(self, ok_text="确认"):
        """二次确认弹窗（ConfirmDialog）。

        注意和老版的差异：front2 没有 el-message-box / el-dialog 之分，
        普通弹窗和确认框都是 .overlay.open .modal。
        按钮文案由调用方的 okText 决定（删除确认传的是「删除」）。
        """
        box = self.page.locator(".overlay.open .modal").last
        expect(box).to_be_visible(timeout=EXPECT_TIMEOUT)
        box.get_by_role("button", name=re.compile(f"^{re.escape(ok_text)}$")).click()
        return self

    def modal(self):
        """当前打开的页面级弹窗（添加记录这类 .modal.wide）。"""
        loc = self.page.locator(".overlay.open .modal").last
        expect(loc).to_be_visible(timeout=EXPECT_TIMEOUT)
        return loc

    # ---------------- 等待辅助 ----------------

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        """子类覆盖：断言"这个页面真的到了"。"""
        raise NotImplementedError("各页面自己定义'加载完成'的标志")
