# pages/login_page.py
# 作用：front2 登录/注册页的 Page Object。
#
# ⚠️ 这个页面最大的坑：**登录和注册两个 <form> 同时挂在 DOM 里**，
#    靠 tab 状态切换 .auth-form.on 才显示。所以：
#      · 所有输入框/按钮都必须限定在 form.auth-form.on 里找，
#        否则 get_by_placeholder("you@example.com") 会命中两个元素，
#        Playwright 严格模式直接报 strict mode violation —— 这还算好的，
#        换成 .first 就可能把邮箱填进注册表单，报出来的是"登录失败"。
#      · 切 tab 用 .auth-tab 按钮，切完等目标 form 带 .on 再操作。
#
# 登录成功的落点是首页 '/'（LoginView 里 router.push('/')），
# 守卫只看登录态、不管档案 —— 登录成功即进首页。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    # ---------------- 作用域 ----------------

    def active_form(self):
        """当前显示的那个表单（.auth-form.on）。

        这是本页所有操作的根作用域 —— 必须先拿到它再往里找控件。
        """
        return self.page.locator("form.auth-form.on")

    def switch_tab(self, name):
        """切换 登录 / 注册。切完等表单真正切换再返回，避免下一句填错 form。

        用 get_by_role 按可访问名找 tab：.auth-tab 的 innerText 带模板换行，
        has_text 正则锚点匹配不上（注册用例第一次跑就红在这）。
        """
        self.page.get_by_role("button", name=name, exact=True).click()
        expect(self.active_form()).to_be_visible()
        return self

    # ---------------- 登录表单控件 ----------------

    def email_input(self):
        return self.active_form().get_by_placeholder("you@example.com")

    def password_input(self):
        # 登录 form 里只有一个密码框（注册 form 的在另一个 form 里，被作用域挡住）
        return self.active_form().locator("input[type=password]").first

    def submit_button(self):
        # 用 type=submit 定位而不是文案：busy 时文案会从「登录」变成「登录中」
        return self.active_form().locator("button[type=submit]")

    def demo_button(self):
        return self.active_form().get_by_role("button", name="使用体验账号快速进入")

    # ---------------- 操作 ----------------

    def open(self, path=None, wait_until="domcontentloaded"):
        super().open(path, wait_until)
        return self.expect_loaded()

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        # 品牌标题是登录页独有的，导航/壳层上没有
        expect(self.page.get_by_role("heading", name="今天，好好吃饭")).to_be_visible(
            timeout=timeout
        )
        return self

    def login(self, email, password):
        self.email_input().fill(email)
        self.password_input().fill(password)
        self.submit_button().click()
        return self

    # ---------------- 断言 ----------------

    def expect_login_success(self, timeout=EXPECT_TIMEOUT):
        self.toast("登录成功", timeout=timeout)
        return self

    def expect_login_failed(self, timeout=EXPECT_TIMEOUT):
        """失败 = 出了红色提示 + 人还在登录页。

        不断言具体文案：后端"邮箱或密码错误"的说法改过好几次，
        断言 .toast.error 这个**类型**才稳定 —— 文案变了用例不该红。
        """
        loc = self.toast(timeout=timeout)
        expect(loc).to_have_class(re.compile(r"error"), timeout=2000)
        expect(self.page).to_have_url(re.compile(r"/login/?$"), timeout=timeout)
        return self

    def field_error(self, text=None):
        """字段级错误文案（.field.has-error 里的 .field-error）。

        前端校验失败时只标红字段，不弹 toast —— 两套反馈别搞混：
          · 格式错误（邮箱/密码长度）→ 字段标红
          · 后端拒绝（密码不对）     → toast
        """
        loc = self.active_form().locator(".field.has-error .field-error")
        if text is not None:
            loc = loc.filter(has_text=text)
        return loc.first

    # ---------------- 注册表单控件 ----------------

    def register(self, username, email, password, phone=""):
        """走注册 tab 提交。注册成功直接发 token 并跳 /health（健康引导）。"""
        self.switch_tab("注册")
        form = self.active_form()
        form.get_by_placeholder("2–20 个字符").fill(username)
        form.get_by_placeholder("you@example.com").fill(email)
        if phone:
            form.get_by_placeholder("选填，用于接收饮食提醒").fill(phone)
        form.locator("input[type=password]").first.fill(password)
        form.locator("button[type=submit]").click()
        return self
