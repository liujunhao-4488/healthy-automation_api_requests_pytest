# pages/login_page.py
# 登录页（frontend/src/views/Login.vue）
#
# 这个 page 对象只有一个职责：**把登录表单走完**。
# 它不负责"跳过登录" —— 直注 token 那条路在 conftest 里，两者刻意分开：
#   · 本文件代表"被测功能"
#   · 直注代表"测试准备手段"
#   混在一起，就会出现"为了测登录而绕开登录"的荒谬结构，
#   最终结果是登录页坏了一整天都没人发现（所有用例都从直注开始）。

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    # ---- 元素 ----
    @property
    def title(self):
        return self.page.get_by_text("欢迎回来")

    @property
    def email_input(self):
        return self.by_placeholder("请输入邮箱地址")

    @property
    def password_input(self):
        return self.by_placeholder("请输入密码")

    @property
    def submit_button(self):
        # 用可访问名定位而不是 .auth-submit：
        # class 是样式锚点，前端改版第一件事就是改它；文案"登录"是业务语义。
        return self.by_role_button("登录")

    @property
    def reset_button(self):
        return self.by_role_button("重置")

    def field_error(self, text):
        """表单校验错误（红色小字，el-form-item__error）。"""
        return self.page.locator(".el-form-item__error").filter(has_text=text).first

    # ---- 操作 ----
    def expect_loaded(self):
        self.expect_visible(self.email_input)
        self.expect_visible(self.submit_button)
        return self

    def fill_email(self, email):
        self.email_input.fill(email)
        return self

    def fill_password(self, password):
        self.password_input.fill(password)
        return self

    def submit(self):
        self.submit_button.click()
        return self

    def login(self, email, password):
        """完整登录动作：填 → 点 → （调用方自己等跳转）。

        故意不在末尾等跳转：
          登录有 3 种去向（admin / 档案完整 / 档案未完成），
          "该跳哪里"是**用例要断言的业务结论**，
          写死在 page 对象里会把用例的判断力抽走。
        """
        self.fill_email(email).fill_password(password).submit()
        return self

    # ---- 断言 ----
    def expect_login_success(self):
        """成功提示 + 离开登录页。"""
        self.toast("登录成功")
        self.expect_hidden(self.email_input)
        return self

    def expect_login_failed(self, message_fragment=""):
        """失败提示：密码错 / 账号不存在 / 格式非法都走这里。"""
        toast = self.page.locator(".el-message:visible").filter(has_text=message_fragment or "登录")
        self.expect_visible(toast.first)
        # 失败必须**留在登录页** —— 这条比提示文案更重要：
        # 提示文案会改，而"没登进去却跳走了"是严重缺陷。
        self.expect_visible(self.email_input)
        return self
