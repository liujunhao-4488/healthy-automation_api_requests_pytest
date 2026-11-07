# test_cases/auth/test_login_ui.py
# 登录链路 —— 全套用例里**唯一真走登录表单**的一组，是 token 直注的对照组：
# 直注省掉了登录这一段，这里就必须有人替它守着，否则登录页坏了整套用例都发现不了。
# 账号矩阵、爆破类的穷举在接口层做过了，UI 只覆盖行为。
#
# 两处容易写错的前端行为，用例按它们的实际表现断言：
#   · 登录成功落点是首页 '/'
#   · 登录页预填了体验账号（DEMO_EMAIL / DEMO_PASSWORD）——
#     所以"邮箱为空"的用例必须先 clear，直接不填是测不到空态的

import re
import time

import pytest
from playwright.sync_api import expect

from config.config import FRONTEND_URL, TEST_USER
from pages.login_page import LoginPage

HOME_URL = re.compile(FRONTEND_URL.replace(".", r"\.") + r"/?$")


class TestLogin:
    """用 page 夹具（未注入登录态的干净上下文）。"""

    def test_登录成功_落到首页且登录态已写入(self, page):
        login = LoginPage(page)
        login.open()

        login.login(TEST_USER["email"], TEST_USER["password"])

        login.expect_login_success()
        expect(page).to_have_url(HOME_URL, timeout=15_000)
        # 登录态落进 sh_session（唯一存储 key，http.js 从这里取 token）
        session_raw = page.evaluate("() => localStorage.getItem('sh_session')")
        assert session_raw and "token" in session_raw, "登录成功但 sh_session 没写入"

    def test_密码错误_红色提示且留在登录页(self, page):
        login = LoginPage(page)
        login.open()

        login.login(TEST_USER["email"], "definitely-wrong-password")

        login.expect_login_failed()

    def test_邮箱格式非法_前端拦截_请求根本没发出去(self, page):
        """监听网络请求，断言 /auth/login 没发出。

        理由：这类"纯前端校验"的价值就在"不打后端"。
        只断言"留在登录页"的话，后端挂了/校验漏了都能给出同样的表象 ——
        监听请求才能把"校验生效"和"碰巧没成功"区分开。
        """
        login_requests = []
        page.on(
            "request",
            lambda req: login_requests.append(req.url)
            if "/auth/login" in req.url
            else None,
        )

        login = LoginPage(page)
        login.open()
        # 登录页预填了体验账号，必须先清空才能测"格式非法"
        login.email_input().fill("not-an-email")
        login.password_input().fill("123456")
        login.submit_button().click()

        expect(login.field_error("请输入有效的邮箱地址")).to_be_visible()
        expect(page).to_have_url(re.compile(r"/login/?$"), timeout=5_000)
        assert not login_requests, f"前端校验失效，/auth/login 被发出了：{login_requests}"

    def test_注册新账号_直接进入健康引导页(self, page):
        """注册成功直接发 token 并跳 /health，不需要再登一次。"""
        login = LoginPage(page)
        login.open()

        ts = int(time.time())
        email = f"f2ui_{ts}@test.local"
        username = f"ui自动化{ts % 100000}"

        login.register(username=username, email=email, password="123456")

        login.toast(re.compile(r"注册成功"), timeout=10_000)
        expect(page).to_have_url(
            re.compile(FRONTEND_URL.replace(".", r"\.") + r"/health/?$"), timeout=15_000
        )

    def test_刷新后登录态保留(self, page):
        """登录态持久化的 UI 层证据：刷新后不该被踢回登录页。"""
        login = LoginPage(page)
        login.open()
        login.login(TEST_USER["email"], TEST_USER["password"])
        expect(page).to_have_url(HOME_URL, timeout=15_000)

        page.reload(wait_until="domcontentloaded")

        expect(page).not_to_have_url(re.compile(r"/login/?$"), timeout=15_000)
        session_raw = page.evaluate("() => localStorage.getItem('sh_session')")
        assert session_raw, "刷新后 sh_session 丢了，登录态无法持久化"


class TestRouteGuard:
    """路由守卫：front2 的守卫只看 isLoggedIn（读 sh_session）。

    这两条也是直注方案的冒烟验证：注入对了守卫放行、注入错了踢回登录页，
    后面所有 user_page 用例都建立在这个前提上 —— 把它们放进 smoke。
    """

    def test_未登录访问受限页_被踢回登录页(self, page):
        page.goto(LoginPage(page).url_for("/record"), wait_until="domcontentloaded")
        expect(page).to_have_url(re.compile(r"/login/?$"), timeout=10_000)

    def test_直注登录态后_受限页直接放行(self, user_page):
        user_page.goto(LoginPage(user_page).url_for("/record"))
        expect(user_page).not_to_have_url(re.compile(r"/login/?$"), timeout=10_000)
