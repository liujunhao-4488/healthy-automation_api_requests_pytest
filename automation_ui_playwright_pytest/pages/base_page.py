# pages/base_page.py
# 作用：Page Object 的公共底座 —— 只放"每个页面都要用"的东西，不放任何业务。
#
# POM 的边界在这儿（很重要，划错了会烂成另一个样）：
#   Page Object 里**只写"怎么操作这个页面"**：元素在哪、怎么点、怎么填、怎么读。
#   断言留一部分在页面对象里：
#     · "这个页面到了没有"（expect_loaded）—— 这是页面自己的知识
#     · "业务对不对"（BMI 算得对不对、记录是不是真进了库）—— 留在用例里
#   把业务断言塞进 page 对象，用例读起来就是一行 page.xxx()，等于没写用例，
#   出了问题也看不出"哪条需求被违反了"。
#
# ── DOM 约定（被测前端 front2 是零依赖实现，没有 Element Plus）──────────
# 组件名和源码（front2/src）一一对应：
#
#   轻提示        ToastHost.vue      → .toast-wrap .toast（error 类名区分红/绿）
#   二次确认      ConfirmDialog.vue  → .overlay.open .modal（按钮文案由 okText 决定）
#   表单项        各 View 里的 .field（<label> + input/textarea，label 没有 for 关联）
#   分段选择      .seg（一排 button，选中项带 .on）
#   多选 chip     .chip（选中项带 .on）
#
# ── 定位策略（这个项目没有 data-testid，只能靠语义）────────────────────
#   顶用的是 placeholder / 可访问名 / 文案，加上 front2 给关键输入框留的 id
#   （foodSearch / gramsInput / noteInput）—— 弹窗里的操作优先用 id，比文案稳。
#
#   ⚠️ 最推荐的做法是给关键元素加 data-testid（`<input data-testid="login-email">`），
#      定位就从"猜文案"变成"查固定锚点"。这件事该提给前端，属于可测性改进 ——
#      在简历里它是"发现了可测性风险并推动解决"，比多写 20 条用例更能说明问题。
#      在这之前，靠 placeholder + label 文案定位，**文案一改选择器就断**，
#      而这恰恰是最该被自动化发现的变化（改了文案，用例应该红，提示去同步）。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT, FRONTEND_URL


class BasePage:
    """所有 Page Object 的父类。"""

    # 子类覆盖：该页面的路由路径
    path = "/"

    def __init__(self, page, base_url=None):
        self.page = page
        self.base_url = (base_url or FRONTEND_URL).rstrip("/")

    # ---------------- 导航 ----------------

    def url_for(self, path=None):
        path = self.path if path is None else path
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def open(self, path=None, wait_until="domcontentloaded"):
        """打开页面。

        wait_until 用 domcontentloaded 而不是 networkidle：
          Vite dev server 有 HMR 的 websocket 长连接，
          networkidle 会一直等不到"网络空闲"，白白耗掉 30s 再超时。
          页面"加载完没完"由各页面的 expect_loaded() 判定，不靠这个参数。
        """
        self.page.goto(self.url_for(path), wait_until=wait_until)
        return self

    def reload(self):
        self.page.reload(wait_until="domcontentloaded")
        return self

    def current_path(self):
        return self.page.evaluate("() => location.pathname")

    # ---------------- 定位辅助 ----------------

    def by_role_button(self, name, exact=False):
        """按可访问名找按钮。

        默认 exact=False 是 Playwright 的语义（子串匹配）；
        名字可能撞车的场景（"登录" vs "登录/注册"）由调用方传 exact=True。
        """
        return self.page.get_by_role("button", name=name, exact=exact)

    def by_placeholder(self, placeholder):
        """placeholder 匹配。优先精确：'请输入邮箱地址' 和 '请输入邮箱' 会互相误伤。"""
        return self.page.get_by_placeholder(placeholder)

    def field(self, label, exact=True):
        """按 label 文案抓一个表单项 .field。

        label 没有 for 属性、input 也没有 id（弹窗里那几个除外），
        只能靠"包含这段文案的 .field"来圈定范围。
        用 exact：'年龄（岁）' 和 '年龄' 是两个不同的字段，模糊匹配会填错框。
        """
        return self.page.locator(".field").filter(
            has=self.page.get_by_text(label, exact=exact)
        ).first

    def field_input(self, label, exact=True):
        """表单项里的输入控件（input 或 textarea 都覆盖）。"""
        return self.field(label, exact=exact).locator("input, textarea").first

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

    # ---------------- 反馈类（全局组件）----------------

    def toast(self, text=None, timeout=EXPECT_TIMEOUT):
        """轻提示（ToastHost）。

        两个坑：
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

    def expect_success_toast(self, timeout=EXPECT_TIMEOUT):
        """保存类动作成功的判据：出现一条**非 error** 的提示。

        为什么不写死文案：成功文案大多来自后端 message（「目标已更新」
        「保存成功」…），前端只是兜底。写死就把后端改文案变成 UI 用例的红 ——
        那不是我们要测的东西。反过来失败提示一定带 .error 类，
        用它区分成功/失败是稳定的。
        """
        toast = self.toast(timeout=timeout)
        assert "error" not in (toast.get_attribute("class") or ""), (
            f"操作失败，提示为错误样式：{toast.inner_text()!r}"
        )
        return self

    def expect_rejected(self, text, timeout=EXPECT_TIMEOUT):
        """「被前端拦下」的统一判据：出现指定文案的**红色**提示。

        为什么要额外断言 error 类：
          只匹配文案的话，把同样的字写进成功提示也能过（文案是可能被复用的）；
          红色是"这是错误"的唯一硬信号，前端用 class="error" 表达。
        """
        toast = self.toast(text, timeout=timeout)
        assert "error" in (toast.get_attribute("class") or ""), (
            f"提示 {text!r} 出现了，但不是错误样式 —— 判据可能写错，或前端把校验提示写成了成功样式"
        )
        return self

    def confirm_dialog(self, ok_text="确认"):
        """二次确认弹窗（ConfirmDialog）。

        普通弹窗和确认框都是 .overlay.open .modal，
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

    # ---------------- 等待 / 断言辅助 ----------------

    def expect_visible(self, locator, timeout=EXPECT_TIMEOUT):
        expect(locator).to_be_visible(timeout=timeout)
        return self

    def expect_hidden(self, locator, timeout=EXPECT_TIMEOUT):
        expect(locator).to_be_hidden(timeout=timeout)
        return self

    def expect_text(self, locator, text, timeout=EXPECT_TIMEOUT):
        expect(locator).to_contain_text(text, timeout=timeout)
        return self

    def expect_path(self, path, timeout=EXPECT_TIMEOUT):
        """等路由跳到位。

        用 expect(page).to_have_url 而不是 `assert current_path() == path`：
          路由跳转是异步的（router.replace 之后还可能有一次 window.location 兜底），
          裸断言会在跳转完成前的瞬间判死 —— 这类失败重跑就绿，是最浪费时间的一种。
        """
        pattern = re.compile(re.escape(path) + r"(\?.*)?$")
        expect(self.page).to_have_url(pattern, timeout=timeout)
        return self

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        """子类覆盖：断言"这个页面真的到了"。"""
        raise NotImplementedError("各页面自己定义'加载完成'的标志")
