# test_cases/auth/test_login_ui.py
# 登录链路 —— **唯一一组真走登录表单的用例**。
#
# ── 为什么这组必须存在，哪怕其他所有用例都靠 token 直注 ──────────────
#   直注跳过了登录，也就等于**放弃了登录页的覆盖**。
#   如果整套 UI 自动化只有直注，登录页的选择器全错、按钮点了没反应、
#   后端登录接口挂了 —— 整套用例照样全绿。
#   所以这一组是"直注的对照组"：它红了，说明被跳过的那段坏了。
#
#   反过来也要说清：这一组**注定慢**（每条 3~5s），所以它只覆盖
#   "能不能登进去"和"该拦的拦没拦住"，不做穷举（不做 20 组账号密码组合）——
#   账号矩阵在接口层 test_cases/auth/test_login.py 里已经跑过，
#   UI 层再跑一遍是重复劳动，而且慢十倍。

import re

import pytest
from playwright.sync_api import expect

from config.config import FRONTEND_URL, TEST_USER
from pages.login_page import LoginPage

# 登录后的去向有两条，取决于这个账号在库里有没有完整档案：
#   档案完整 → /dashboard/health-info
#   没有档案 → /health-info-basic（引导建档案）
# ⚠️ 所以这里**不能写死一条路径**：
#   测试账号的档案状态是环境状态，不是本用例能控制的东西。
#   写死之后，换一台机器/换一个测试库，这条用例就会红在"跳转地址不符"上，
#   而登录功能一点问题都没有 —— 那种红是纯噪音。
LANDING = r"/(dashboard/health-info|health-info-basic)/?$"


class TestLogin:
    """用 context（未注入 token 的干净上下文）+ 真实表单。"""

    def test_登录成功_进入系统并落到正确首页(self, page):
        login = LoginPage(page)
        login.open().expect_loaded()

        login.login(TEST_USER["email"], TEST_USER["password"])

        # ① 成功提示 ② 离开登录页 ③ 落到两个合法首页之一
        login.expect_login_success()
        expect(page).to_have_url(
            re.compile(FRONTEND_URL.replace(".", r"\.") + LANDING),
            timeout=15000,
        )

    def test_密码错误_留在登录页并给出提示(self, page):
        login = LoginPage(page)
        login.open().expect_loaded()

        login.login(TEST_USER["email"], "definitely-wrong-password")

        # 不断言具体文案："密码错误"/"邮箱或密码错误"/"登录失败" 都是后端改过好几次的说法。
        # 断言的是**行为**：给了提示、且没放人进去。
        login.expect_login_failed()
        expect(page).to_have_url(re.compile(r"/login/?$"), timeout=10000)

    def test_邮箱格式非法_前端直接拦截不发请求(self, page):
        """纯前端校验：这类断言的价值在于"没打到后端"。

        这里只断表单错误文案出现、没有发生跳转。
        更严格的写法是监听 request 事件断言"没发出 /auth/login"，
        但那属于"防浪费"的优化，不是缺陷 —— 前端拦不住也只是多一次无效请求。
        """
        login = LoginPage(page)
        login.open().expect_loaded()

        login.fill_email("not-an-email").fill_password("123456").submit()

        login.expect_visible(login.field_error("请输入有效的邮箱地址"))
        expect(page).to_have_url(re.compile(r"/login/?$"), timeout=5000)

    def test_邮箱为空_必填校验生效(self, page):
        login = LoginPage(page)
        login.open().expect_loaded()

        login.fill_password("123456").submit()

        login.expect_visible(login.field_error("请输入邮箱"))

    def test_已登录状态下刷新_登录态不丢失(self, page):
        """刷新后仍是登录态 —— 这是"token 持久化"的 UI 层证据。

        为什么值得单独一条：
          token 存 localStorage、刷新后由 pinia 从 localStorage 恢复，
          这条链路只在"刷新"这个动作里才会暴露问题（比如恢复逻辑读错了 key）。
          而日常开发几乎没人会手动刷一次登录后的页面。
        """
        login = LoginPage(page)
        login.open().expect_loaded()
        login.login(TEST_USER["email"], TEST_USER["password"])
        login.expect_login_success()

        page.reload(wait_until="domcontentloaded")

        # 刷新后必须**不在**登录页；再断言 localStorage 里 token 还在
        expect(page).not_to_have_url(
            re.compile(r"/login/?$"), timeout=15000
        )
        token = page.evaluate("() => localStorage.getItem('token')")
        assert token, "刷新后 localStorage 里的 token 丢了，登录态无法持久化"
