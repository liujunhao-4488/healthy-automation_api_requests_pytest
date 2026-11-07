# conftest.py
# UI 自动化的"公共工具间"：浏览器生命周期、登录态注入、失败留痕、分层标记。
#
# 和接口层的 conftest.py 分工不同，不要互相抄：
#   接口层管的是 requests.Session + 日志分块；
#   UI 层管的是 browser / context / page 三级对象 + trace + 截图。
#   两者唯一的交集是"拿到同一个账号的 token"，这件事在 common/auth_state.py 里。
#
# ── 浏览器对象的生命周期（Playwright 的三层结构，必须先想清楚）──────────
#   browser  ：一个浏览器进程。**整个 session 只起一次** —— 起一次 Chromium 要 1~2s，
#              每条用例起一次，十几条用例光启动就 30s。
#   context  ：一个隔离的浏览器上下文（独立 cookie / localStorage / 缓存）。
#              **每条用例一个**。这是隔离的边界：上一条用例写进 localStorage 的脏数据
#              不会漏到下一条。也是"注入 token"的天然位置。
#   page     ：一个标签页。用例实际操作的对象，Page Object 包的就是它。
#
#   为什么不在 session 级复用一个 context（更快）：
#     省下的 200ms 换来"用例之间互相污染"——某条用例登出后，后面全部用例被踢回登录页，
#     而错误信息只会说"元素找不到"。隔离值这个钱。

import importlib.util
import os
import time

import pytest

try:
    from playwright.sync_api import sync_playwright
except Exception:  # noqa: BLE001 - 没装 playwright 时不要让 conftest 加载失败
    sync_playwright = None

from common import artifacts
from common.auth_state import (
    AuthBootstrapError,
    build_init_script,
    build_storage_state,
    is_expired,
    login_via_api,
)
from config.config import (
    ARTIFACTS,
    BROWSER,
    DEFAULT_TIMEOUT,
    EXPECT_TIMEOUT,
    FRONTEND_URL,
    HEADLESS,
    LOCALE,
    NAV_TIMEOUT,
    REQUIRE_SERVICE,
    SLOWMO,
    TEST_USER,
    TIMEZONE,
    TRACE_ON_FAILURE,
    VIEWPORT,
)


# ==================== 前置检查 ====================

def pytest_configure(config):
    """在任何收集动作之前拦一次：没装 playwright 就别往下走。

    为什么不用顶层 import 直接抛：
      那样 pytest 只会报 "ImportError while loading conftest"，再堆 20 行 traceback，
      看起来像项目坏了。这里换成一句"装什么、怎么装"，
      换机器 / 新同事接手时差别很大。
    """
    if sync_playwright is None and importlib.util.find_spec("playwright") is None:
        pytest.exit(
            "UI 自动化缺少 Playwright。执行：\n"
            "  pip install -r automation_ui_playwright_pytest/requirements.txt\n"
            "  python -m playwright install chromium\n"
            "（第二条会下 ~120MB 浏览器内核，只需下一次）",
            returncode=3,
        )

    # Allure 结果目录按 rootdir 算绝对路径，不写相对路径 ——
    # 相对路径按"当前工作目录"解析，在 PyCharm 里换个工作目录就写到别处去了。
    #
    # ⚠️ 必须用 getattr 取：allure_report_dir 这个属性是 allure-pytest 插件**注册**的，
    #    没装插件时 Namespace 里根本没有它，直接 config.option.allure_report_dir 会
    #    AttributeError: 'Namespace' object has no attribute —— 而且是在 pytest_configure 里炸，
    #    表现是 INTERNALERROR 一大段 traceback，看起来像 pytest 本身坏了。
    if getattr(config.option, "allure_report_dir", None) is None and importlib.util.find_spec(
        "allure_pytest"
    ):
        config.option.allure_report_dir = str(ARTIFACTS["allure"])
        os.makedirs(config.option.allure_report_dir, exist_ok=True)


def _probe(url, timeout=5):
    """探活：能拿到任何 HTTP 响应就算服务活着（404 也算）。

    为什么不判状态码 200：
      后端根路径通常是 404（Spring Boot 没配根路由），
      把 404 当"没起"会一直误报。这里要区分的是
      "进程在不在"和"业务对不对"，后者是用例的事。

    为什么 trust_env=False：
      requests 默认吃环境变量里的 http_proxy —— 本机挂着代理时，
      "服务没起"会被代理翻译成 502 返回回来，看起来像"活着"，
      预检形同虚设（实际踩过：5173 没起，探活照样过，用例整片红）。
      探的是本机地址，直连才是它的本意。
    """
    import requests

    try:
        session = requests.Session()
        session.trust_env = False
        session.get(url, timeout=timeout, allow_redirects=True)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc).splitlines()[0][:160]


def pytest_collection_finish(session):
    """收集完、开跑前做一次环境预检。

    放在这里而不是 sessionstart：
      sessionstart 时还没收集，--collect-only / -k 过滤的场景会白跑一次探活。
      收集完才知道"这次到底要不要起浏览器"。
    """
    if not REQUIRE_SERVICE:
        return
    if session.config.getoption("collectonly", default=False):
        return
    if not session.items:
        return

    problems = []
    ok, detail = _probe(FRONTEND_URL)
    if not ok:
        problems.append(
            f"前端 {FRONTEND_URL} 打不开（{detail}）\n"
            f"    → cd front2 && npm run dev（端口 5174）"
        )

    try:
        login_via_api()
    except AuthBootstrapError as exc:
        problems.append(str(exc))

    if problems:
        pytest.exit(
            "\nUI 自动化环境预检未通过：\n  · " + "\n  · ".join(problems) + "\n"
            "  确认后再跑；确实要跳过预检：set AUTOTEST_UI_REQUIRE_SERVICE=0",
            returncode=3,
        )


# ==================== 浏览器三层对象 ====================

@pytest.fixture(scope="session")
def browser():
    """整个 session 共用一个浏览器进程。"""
    with sync_playwright() as pw:
        launcher = getattr(pw, BROWSER)
        browser = launcher.launch(
            headless=HEADLESS,
            slow_mo=SLOWMO,
            # 关掉"Chrome 正受自动化软件控制"的提示条。
            # 它在视口底部盖一条横幅，偶尔会挡住页面底部的按钮 ——
            # 那类失败重现不了（人肉打开没有横幅），最难查。
            args=["--disable-blink-features=AutomationControlled"],
        )
        yield browser
        browser.close()


def _new_context(browser, inject_script=None):
    ctx = browser.new_context(
        viewport=VIEWPORT,
        locale=LOCALE,
        timezone_id=TIMEZONE,
        # 关掉动画？刻意**不关**：
        #   prefers-reduced-motion 会让前端走另一套样式分支，
        #   而真实用户不开这个开关 —— 那等于在测一个用户见不到的环境。
        #   动画导致的偶发由 Playwright 的自动等待 + reruns 兜住。
        ignore_https_errors=True,
    )
    if inject_script:
        ctx.add_init_script(script=inject_script)
    if TRACE_ON_FAILURE:
        # sources=False：带上源码会让 trace 体积翻几倍，而排查 UI 缺陷主要看 DOM 快照
        ctx.tracing.start(screenshots=True, snapshots=True, sources=False)
    return ctx


def _close_context(ctx, node):
    """关 context 前处理 trace：失败留下，通过丢掉。"""
    failed = getattr(node, "_ui_call_failed", False)
    if TRACE_ON_FAILURE:
        if failed:
            path = artifacts.save_trace(ctx, node.nodeid)
            if path:
                artifacts.attach(path, "trace（playwright show-trace 打开）")
                print(f"\n  trace 已保存：{path}")
        else:
            artifacts.stop_trace_discard(ctx)
    ctx.close()


@pytest.fixture
def context(browser, request):
    """**未登录**的干净上下文：登录链路用例专用。"""
    ctx = _new_context(browser)
    yield ctx
    _close_context(ctx, request.node)


@pytest.fixture(scope="session")
def account():
    """一次登录，整场复用。

    session 级而不是 function 级：
      login_via_api 要打一次接口 + 一次 bcrypt 校验（约 100ms），
      每条用例登一次纯属浪费。token 过期由下面的 _ensure_fresh 兜。
    """
    return login_via_api()


def _ensure_fresh(account):
    """跑一整个 session 可能超过 token 有效期（默认 24h，正常不会）。

    真到这一步说明这轮跑得离谱地久（比如挂了半天），
    与其让后半场全部"注入了还是被踢回登录页"，不如重登一次。
    """
    if is_expired(account["token"]):
        fresh = login_via_api()
        account.update(fresh)
    return account


def _open_page(ctx):
    page = ctx.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(NAV_TIMEOUT)
    return page


@pytest.fixture
def page(context):
    pg = _open_page(context)
    yield pg
    if not pg.is_closed():
        pg.close()


# ==================== 已登录夹具 ====================
# 登录态只有一个 key：sh_session（详见 common/auth_state.py）。
# 直注而不是走登录表单：一次 UI 登录 2.5~4s，十几条用例就是 40s 纯等待，
# 而且登录页一改版，全部用例一起红，失败原因全指向"登录页选择器变了"。

@pytest.fixture
def auth_context(browser, request, account):
    """**已登录**的上下文：token 直注，跳过 UI 登录。

    为什么要在 context 级注入而不是 page 级：
      add_init_script 注册在 context 上，该 context 下**所有**页面
      （包括用例中途打开的新标签页）都会自动带上 token。
      注册在 page 上就只对那一个页面有效，遇到 target="_blank" 就又变回未登录。
    """
    account = _ensure_fresh(account)

    # 落一份 storage_state 供人工调试（codegen --load-storage 直进登录态）。
    # 不是给运行用的（运行用 init_script），是给人排查用的。
    try:
        import json

        state_path = ARTIFACTS["storage"] / f"{artifacts.safe_name(request.node.nodeid)}.json"
        state_path.write_text(
            json.dumps(
                build_storage_state(account, FRONTEND_URL),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass

    ctx = _new_context(browser, inject_script=build_init_script(account))
    yield ctx
    _close_context(ctx, request.node)


@pytest.fixture
def user_page(auth_context):
    """已登录的页面 —— 绝大多数用例用这个。

    名字刻意叫 user_page 而不是 logged_in_page：
    用例里出现 logged_in_page 会让人以为"这条用例在测登录"，
    而它其实是在测别的功能、只是借了登录态。
    """
    pg = _open_page(auth_context)
    yield pg
    if not pg.is_closed():
        pg.close()


@pytest.fixture(scope="session")
def profile_ready(account):
    """保证测试账号在后端有健康档案（档案页数据唯一来源是后端）。

    session 级 + 幂等：第一场跑完档案就在了，之后每场只多一次 GET。
    health 域的用例依赖它；没有档案时 KPI 区是 v-if 掉的，用例无从断言。
    """
    from common.auth_state import ensure_profile

    ensure_profile(account)
    return account


# ==================== 失败留痕 ====================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """在 call 阶段失败的**那一瞬间**截屏。

    为什么不用 fixture 的 finally 去截：
      fixture teardown 发生在 call 之后，那时用例可能已经做了清理动作
      （关弹窗、跳回列表页），截到的是"收拾干净之后"的画面 ——
      最需要看的那一屏已经没了。
      这里拿到的 funcargs 还是失败现场。

    注意只认 call 阶段：
      setup 阶段失败（浏览器没起来 / 夹具报错）没有可用页面，
      teardown 阶段的失败通常是清理没做好，截屏意义不大，两者都只留文本。
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        if report.failed:
            # setup/teardown 失败也要让 context 知道"这条算失败"，否则 trace 会被丢掉
            setattr(item, "_ui_call_failed", True)
        return

    setattr(item, "_ui_call_failed", report.failed)
    if not report.failed:
        return

    pg = None
    for name in ("user_page", "page"):
        pg = item.funcargs.get(name)
        if pg is not None:
            break
    if pg is None or pg.is_closed():
        return

    shot = artifacts.save_screenshot(pg, item.nodeid)
    if shot:
        artifacts.attach(shot, "失败截图")
        print(f"\n  截图已保存：{shot}")

    # 页面上的可见文本：断言失败只告诉人"哪条断言没过"，
    # 真正想知道的是"那会儿页面上写的是什么"。
    artifacts.attach_text(artifacts.page_snapshot_text(pg), "失败瞬间的页面文本")


# ==================== 分层标记（自动挂，用例里不用写装饰器）====================

#   smoke    : 不调模型、不写业务数据的核心链路（登录 + 档案读取）
#   weekly   : 全部 —— 每周回归跑这一档
#   slow_ai  : 依赖大模型回复
# 新增目录时只改这张表，用例文件保持干净。
_SMOKE_MODULES = {"auth", "health"}
_AI_MODULES = {"assistant"}
_FORM_LOGIN_MODULES = {"auth"}
_PROFILE_MODULES = {"health"}


def pytest_itemcollected(item):
    """从 nodeid 推模块归属。

    ⚠️ Windows 的 nodeid 用反斜杠（test_cases\\auth\\test_x.py），
    先统一替换成正斜杠再切 —— 之前直接 split("/")，Windows 上永远切不出
    "auth"，smoke / slow_ai 标记整场一个都挂不上，-m smoke 等于跑了个寂寞。
    """
    path = item.nodeid.split("::")[0].replace("\\", "/")
    parts = path.split("/")
    module = parts[1] if len(parts) > 1 else ""

    item.add_marker(pytest.mark.regression)
    item.add_marker(pytest.mark.weekly)

    if module in _SMOKE_MODULES:
        item.add_marker(pytest.mark.smoke)
    if module in _AI_MODULES:
        item.add_marker(pytest.mark.slow_ai)
    if module in _FORM_LOGIN_MODULES:
        item.add_marker(pytest.mark.ui_form_login)
    if module in _PROFILE_MODULES:
        item.add_marker(pytest.mark.needs_profile)


# ==================== 结尾汇总 ====================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """跑完告诉人：失败现场在哪个目录、怎么看。

    只留了截图/trace 却不说怎么打开，等于没留 ——
    第一次跑的人看到 artifacts 目录里一堆 .zip 是不知道要 `playwright show-trace` 的。
    """
    failed = [
        rep for key in ("failed", "error") for rep in terminalreporter.stats.get(key, [])
        if rep.when == "call"
    ]
    if not failed:
        return

    terminalreporter.write_sep("-", "失败现场")
    terminalreporter.write_line(f"截图：{ARTIFACTS['screenshots']}")
    terminalreporter.write_line(f"trace：{ARTIFACTS['traces']}")
    terminalreporter.write_line(
        "查看 trace（比截图有用得多，能回放每一步）：\n"
        "  python -m playwright show-trace \"<某个 .zip 的完整路径>\""
    )
