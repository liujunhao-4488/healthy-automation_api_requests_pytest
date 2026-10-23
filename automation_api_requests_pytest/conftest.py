# conftest.py
# pytest 的"公共工具间"：夹具（fixture）与全局日志钩子都放这里，pytest 会自动加载。

import logging
import time
import unicodedata
from datetime import datetime

import pymysql
import pytest
import requests

from api import Api
from api.base_api_client import set_unauthorized_handler
from common import allure_helper, eval_record
from common.accounts import (
    AccountBootstrapError,
    ensure_login_seed_account,
    ensure_primary_account,
)
from common.logger import begin_run_log, log, pad
from config.config import (
    BASE_URL,
    DB,
    KB_BASE_URL,
    REQUIRE_DB,
)


# ==================== 夹具 ====================

class _SessionAuth:
    """整场只登录一次；token 失效时（401）重登一次并更新当前值。

    为什么不直接把 token 做成 session 夹具：
      token 是字符串，拿到手的用例改不了它；后端重启 / JWT 过期后，
      旧字符串会一直用下去。这里把"登录状态"做成对象，auth_headers
      每次按**当前** token 生成，重登后自然拿到新值。
    """

    def __init__(self, api):
        self.api = api
        self.token = None
        self.login()

    def login(self):
        # 账号不存在时先自动注册（common/accounts.py）——空库换机器时，
        # 失败原因会是一条明确的账号提示，而不是几十条登录 400。
        data = ensure_primary_account(self.api)
        assert data.get("token"), "登录成功必须返回 token"
        self.token = data["token"]
        return self.token

    def refresh(self, used_authorization):
        """给 401 钩子用：只重登"用当前 token 发出"的请求。

        不带 token / 伪 token 的负向用例必须保持 401 —— 所以先对一下
        这次请求实际用的 Authorization 是不是当前值，不是就别动。
        """
        if used_authorization != f"Bearer {self.token}":
            return None
        self.login()
        return f"Bearer {self.token}"


@pytest.fixture(scope="session")
def api():
    """接口总入口夹具：用例里 api.auth.login(...) 就能发请求。

    ⚠️ 从 function 级改成 session 级：session 级的登录状态不能依赖
    function 级的夹具（pytest 会直接报 ScopeMismatch）。Api 本身无状态，
    整场共用一个 requests.Session 是安全的（单进程串行）。
    """
    return Api()


@pytest.fixture(scope="session")
def _auth_state(api):
    """会话级登录状态 + 401 重登钩子；token / auth_headers 都从这里取。"""
    state = _SessionAuth(api)
    set_unauthorized_handler(state.refresh)
    yield state
    set_unauthorized_handler(None)


@pytest.fixture
def token(_auth_state):
    """登录夹具：整场只登录一次，这里取当前 token（重登后自动变新值）。"""
    return _auth_state.token


@pytest.fixture
def auth_headers(_auth_state):
    """把**当前** token 包成请求头：{"Authorization": "Bearer xxx"}。"""
    return {"Authorization": f"Bearer {_auth_state.token}"}


# ==================== 控制台分块日志 ====================
# 目标效果：每条用例一个边界框，运行期间的日志以 │ 前缀归入框内，
#           结尾一行给出结果与耗时；多行完整响应体默认不刷控制台。
#
# 关键点：
#   ① 用例运行期间 pytest 会接管（捕获）stdout，直接写终端的日志会被吞掉。
#      所以每条记录写入前先 suspend 全局捕获、写完再 resume，保证框内实时可见。
#   ② 框架/分块的"记账"信息（会话横幅、块头、结果）只写文件，
#      用独立 logger "autotest.meta"，控制台处理器直接过滤，避免重复。

_NAME_WIDTH = 36
_INDENT = "│  "

# 只写文件、不进控制台的记账 logger
meta_log = logging.getLogger("autotest.meta")

# pytest_configure / sessionstart 时赋值，供各 hook 使用
_reporter = None
_capturemanager = None
_handler = None

# ---- 结尾汇总的记账（见文件末 pytest_terminal_summary）----
_started_at = 0.0        # 会话开始时刻（perf_counter）
_module_duration = {}    # 模块名 -> 累计耗时（setup + call + teardown 全算，才是真实耗时）

# 评测留痕的落盘位置（--eval-out 可覆盖，默认 tools/eval_results.json）
_eval_out = None
_eval_path = None        # 本次实际写到了哪（结尾汇总要显示给用户）

# Allure 结果目录（None = 本次不出报告，所有上报动作自动变成空操作）
_allure_dir = None
_started_wall = None     # 会话开始的"墙上时间"，environment.properties 要用


def _term_write(text, **markup):
    """临时解除 pytest 的输出捕获，把一行内容直接写到终端，再恢复捕获。

    块头/块尾/框内日志都必须走这里：默认的 fd 捕获会把写入先灌进管道，
    不挂起就会和下一条输出缓冲错位（出现两行挤在同一行）。
    """
    if _reporter is None:
        return
    if _capturemanager is not None:
        _capturemanager.suspend_global_capture()
    try:
        if markup:
            _reporter.write(text, **markup)
        else:
            _reporter.write(text)
    finally:
        if _capturemanager is not None:
            _capturemanager.resume_global_capture()


class _BlockConsoleHandler(logging.Handler):
    """控制台专用处理器：写终端原始输出流（绕过 pytest 捕获），
    每条记录加 │ 前缀归入当前用例块；多行记录（完整响应体）默认丢弃；
    autotest.meta 的记账记录不显示。
    """

    def __init__(self, reporter, capturemanager, full_log):
        super().__init__(logging.INFO)
        self.reporter = reporter
        self.capturemanager = capturemanager
        self.full_log = full_log
        self.in_test = False
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname).1s %(message)s", "%H:%M:%S"))

    def emit(self, record):
        # 记账记录只写文件，不进控制台
        if record.name == "autotest.meta":
            return
        try:
            msg = self.format(record)
            if not self.full_log and "\n" in msg:
                return  # 完整 body 只进文件；失败时 pytest 会在捕获区自动展开
            color = None
            if record.levelno >= logging.ERROR:
                color = "red"
            elif record.levelno >= logging.WARNING:
                color = "yellow"
            prefix = _INDENT if self.in_test else ""

            prefix = _INDENT if self.in_test else ""
            for line in msg.splitlines():
                if color:
                    _term_write(prefix + line + "\n", **{color: True})
                else:
                    _term_write(prefix + line + "\n")
        except Exception:
            pass


def pytest_addoption(parser):
    parser.addoption(
        "--full-log",
        action="store_true",
        default=False,
        help="控制台展开完整响应体（默认只显示一行请求摘要；失败时自动展开捕获日志）",
    )
    parser.addoption(
        "--eval-out",
        action="store",
        default=None,
        metavar="PATH",
        help="评测留痕的落盘路径（默认 tools/eval_results.json，跑完整评测前可换个名字留着）",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """会话配置：建运行日志 + 定下 Allure 结果目录。

    ⚠️ 为什么挂 tryfirst：Allure 结果目录必须在 **allure 自己的
    pytest_configure 之前**定下来。allure-pytest 的实现是
    （plugin.py: `report_dir = config.option.allure_report_dir`）——
    它读的是当时的选项值，读不到就直接不出报告。
    而默认值是 None，所以我们要抢在它前面把路径塞进去。

    为什么不在 pytest.ini 里写 `--alluredir=reports/allure-results`：
      ① 相对路径是按**当前工作目录**解析的。在 PyCharm 里把工作目录设成
         test_cases/ 时，结果会写到 test_cases/reports/ 下面 —— 找不到，
         还以为是"报告没生成"；
      ② 没装 allure-pytest 的机器上，addopts 里的 --alluredir 会让
         pytest 直接报"unrecognized arguments"，**全场用例一条都跑不起来**。
         一个可选的报告不该有这种杀伤力。
    所以默认目录在这里算（按 rootdir 算绝对路径），装没装都不影响跑用例。
    """
    global _allure_dir

    # 先建本次运行的日志文件。terminalreporter / capturemanager 在 sessionstart 时使用。
    run_file = begin_run_log()
    meta_log.info("══════════ 会话开始 %s  本次日志: %s ══════════",
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"), run_file)

    # 本次运行要不要出 Allure 报告（没装 allure 时返回 None，后面全员降级）
    _allure_dir = allure_helper.results_dir(config)


def pytest_sessionstart(session):
    global _reporter, _capturemanager, _handler, _started_at, _eval_out, _started_wall
    _started_at = time.perf_counter()          # 结尾汇总要用"整场跑了多久"
    _started_wall = datetime.now()
    config = session.config
    _reporter = config.pluginmanager.get_plugin("terminalreporter")
    _capturemanager = config.pluginmanager.get_plugin("capturemanager")
    if _reporter is not None and _capturemanager is not None:
        _handler = _BlockConsoleHandler(
            _reporter, _capturemanager, config.getoption("--full-log"))
        logging.getLogger().addHandler(_handler)
    # 评测留痕：清空上一轮（同一个进程里跑多次 pytest.main 时才会有残留）
    eval_record.reset()
    _eval_out = config.getoption("--eval-out")

    # ⚠️ 上报开关只在**动手跑用例**的会话里打开。
    #    --collect-only 也走 sessionstart，但那种会话不该往报告里写半截数据。
    allure_helper.activate(
        _allure_dir is not None and not config.getoption("--collect-only", default=False))


# ==================== 环境探活（session 级） ====================
# 后端(8080) / MySQL(3306) / 算法服务 Flask(5000) 任何一个没起，
# 用例都会以 ConnectionError 红一片，真正的原因被埋在各条 traceback 里。
# 所以开跑前统一探一次：缺哪个报哪个，然后**中止整场**，一条用例都不跑。
#
# 为什么放在 pytest_collection_finish、而不是 session 级 autouse 夹具：
#   夹具要等"第一条用例 setup"才执行，那时中止会把首条用例记成 setup ERROR；
#   collection_finish 在收集完、一条用例还没跑时触发，退出最干净。
#
# 探活刻意**不复用** BaseApiClient：它会用业务超时(10s)、还会往 Allure/日志里
# 记一条假请求；探活只是环境检查，不该在报告里留下业务痕迹。

_PRECHECK_TIMEOUT = 5       # MySQL / 后端探活超时
_KB_PRECHECK_TIMEOUT = 30   # Flask 首次访问要懒加载知识库索引，给足时间


def _probe_mysql():
    """连测试库并 SELECT 1；连不上时把 MySQL 错误码翻成可执行建议。"""
    try:
        conn = pymysql.connect(connect_timeout=_PRECHECK_TIMEOUT,
                               read_timeout=_PRECHECK_TIMEOUT,
                               write_timeout=_PRECHECK_TIMEOUT, **DB)
    except pymysql.err.OperationalError as exc:
        code = exc.args[0] if exc.args else None
        if code == 1049:
            raise RuntimeError(
                f"数据库 {DB['database']} 不存在。先执行：..\\database\\rebuild_test_db.bat"
            ) from exc
        if code in (1044, 1045):
            raise RuntimeError(
                "账号无权限或密码错误。检查 AUTOTEST_DB_USER / AUTOTEST_DB_PASSWORD"
            ) from exc
        raise

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    finally:
        conn.close()
    return f"连接正常（{DB['database']}）"


def _probe_backend():
    """登录一次 —— 同时验证 Web 层、MySQL、测试账号、以及“后端连的是不是测试库”。

    · 账号不存在 → 自动注册（common/accounts.py）；
    · 后端连的是开发库 → 用 userId + username 跟测试库对账，不一致就中止。
      只对比 userId 不够：两个库里都可能恰好有 id=1，必须再比 username。
    """
    try:
        data = ensure_primary_account()
        ensure_login_seed_account()
    except AccountBootstrapError as exc:
        raise RuntimeError(str(exc)) from exc

    if REQUIRE_DB:
        from common import db as test_db

        row = test_db.query(
            "SELECT `username` FROM `user` WHERE `id` = %s",
            (data["userId"],), one=True,
        )
        if row is None:
            raise RuntimeError(
                f"后端连的库不是测试库 {DB['database']}："
                f"测试库里没有 userId={data['userId']}。\n"
                f"  启动后端前先执行：set DB_NAME={DB['database']}"
            )
        if row["username"] != data.get("username"):
            raise RuntimeError(
                "后端连的库和测试库不是同一个。\n"
                f"  测试库 {DB['database']} 中 userId={data['userId']} 是 {row['username']!r}，"
                f"后端登录返回 {data.get('username')!r}。\n"
                f"  启动后端前先执行：set DB_NAME={DB['database']}"
            )

    return "登录接口正常，测试账号已就绪"


def _probe_algorithm():
    """打 /api/kb/stats：既证明 Flask 在，也证明知识库索引装好了。

    不用 /api/kb/search —— 探活不该触发一次真实检索；stats 会懒加载索引，
    正好把"服务在但索引坏了"这种半启动状态也拦下来。
    """
    resp = requests.get(KB_BASE_URL + "/api/kb/stats",
                        timeout=_KB_PRECHECK_TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}（服务在，但 /api/kb/stats 异常）")
    return "索引正常"


def _env_probes():
    """按依赖顺序返回探活项；AUTOTEST_REQUIRE_DB=0 时不要求本机 MySQL。"""
    probes = []
    if REQUIRE_DB:
        probes.append(("MySQL", f"{DB['host']}:{DB['port']}/{DB['database']}", _probe_mysql))
    probes.append(("后端", BASE_URL, _probe_backend))
    probes.append(("算法服务", KB_BASE_URL, _probe_algorithm))
    return probes


def _apply_requires_db_skip(items):
    """AUTOTEST_REQUIRE_DB=0：跳过直接访问本机 DB 的用例，纯接口仍可跑。

    ⚠️ 必须由**唯一一个** pytest_collection_modifyitems 调用（见文件末尾）。
    同名的 hook 在同一模块里写两次，后一个会把前一个覆盖掉——
    覆盖后不报错、不警告，只是"一条都没跳过"，实测踩过。
    """
    if REQUIRE_DB:
        return
    skip = pytest.mark.skip(
        reason="AUTOTEST_REQUIRE_DB=0：本条用例直接访问 MySQL，已跳过"
    )
    for item in items:
        if "requires_db" in item.keywords:
            item.add_marker(skip)


def _probe_reason(exc):
    """把底层异常翻成一句人话 —— requests 原生报错有 300 字符，刷屏且没重点。"""
    if isinstance(exc, requests.exceptions.ConnectionError):
        return "连不上（服务没启动）"
    if isinstance(exc, requests.exceptions.Timeout):
        return "探活超时（进程在，但没响应）"
    if isinstance(exc, pymysql.err.OperationalError):
        return "连接失败：" + (str(exc.args[1]) if len(exc.args) > 1 else str(exc))
    text = str(exc).strip()
    return text.splitlines()[0][:160] if text else type(exc).__name__


def pytest_collection_finish(session):
    """收集完、开跑前探活；缺一个依赖就中止整场。"""
    # --collect-only 只是"看有哪些用例"，不跑用例，也不该要求服务全在
    if session.config.getoption("collectonly", default=False):
        return

    lines, missing = [], []
    for name, target, probe in _env_probes():
        try:
            lines.append(f"  ✔ {name}  {target}  {probe()}")
        except Exception as exc:
            lines.append(f"  ✘ {name}  {target}  {_probe_reason(exc)}")
            missing.append(name)

    if not missing:
        return

    order = ("MySQL(3306) → backend(8080) → algorithm/app.py(5000)"
             if REQUIRE_DB else "backend(8080) → algorithm/app.py(5000)")
    _term_write(
        "\n✘ 环境未就绪，已中止（一条用例都没跑）：" + "、".join(missing) + "\n"
        + "\n".join(lines) + "\n"
        + f"  启动顺序：{order}\n",
        red=True)
    meta_log.error("环境探活未通过：%s", "；".join(lines))
    pytest.exit("环境未就绪：" + "、".join(missing),
                returncode=pytest.ExitCode.TESTS_FAILED)


def _short_name(nodeid):
    return nodeid.split("::")[-1]


def pytest_runtest_logstart(nodeid, location):
    if _handler is not None:
        _handler.in_test = True
    eval_record.start_case(nodeid)      # 之后 observe() 记的观测都归这条用例
    path = nodeid.split("::")[0].replace("test_cases/", "")
    name = _short_name(nodeid)
    line = f"┌─ ▶ {name}    {path}"
    _term_write("\n" + line + "\n", cyan=True, bold=True)
    meta_log.info("┌─ ▶ %s (%s)", name, path)


def pytest_runtest_logfinish(nodeid, location):
    # 整块（含 setup/call/teardown）真正结束后，才停止 │ 前缀
    if _handler is not None:
        _handler.in_test = False


def pytest_report_teststatus(report, config):
    """静音 pytest 自带的进度点：用块尾的 ✔/✘/⊘ 作为唯一结果展示。

    返回空 letter（点/字母），quiet 模式下终端就不再逐个打印点；
    失败用例的完整报错仍由 pytest 在末尾集中输出，不受影响。

    ⚠️ 必须**先分流 xfail**：pytest 里 xfail 的 report 同样是 skipped=True，
    不先判 wasxfail 就会把它当成普通"跳过" —— 显示成 ⊘ SKIPPED、
    并混进汇总的 skipped 列。"跳过"=这条没写，"xfail"=已知缺陷等着修，
    两者混在一起，真缺陷会被当成没写而永远没人管。
    """
    if report.when != "call":
        return None
    wasxfail = getattr(report, "wasxfail", None)
    if wasxfail is not None and report.skipped:
        return "xfailed", "", "XFAIL"
    # strict XPASS：pytest 只把它标成 failed，不设 wasxfail（详见 _is_xpass）
    if wasxfail is not None and report.failed:
        return "failed", "", "XPASS"
    if _is_xpass(report):
        return "failed", "", "XPASS"
    if report.passed:
        return "passed", "", "PASSED"
    if report.failed:
        return "failed", "", "FAILED"
    if report.skipped:
        return "skipped", "", "SKIPPED"
    return None


def _reason(report):
    """从一长串报错里挑出最有用的那句（以 E 开头的最后一条）。"""
    lines = [ln.strip()[2:].strip()
             for ln in (report.longreprtext or "").splitlines()
             if ln.strip().startswith("E ")]
    return lines[-1][:200] if lines else ""


def _is_xpass(report):
    """这条是不是 **strict xfail 却通过了（XPASS）**？

    ⚠️ 坑（2026-10-14 实测撞上）：pytest 对 strict XPASS 的处理是
       `rep.outcome = "failed"` + `rep.longrepr = "[XPASS(strict)] 原因"`，
       **却不设 `rep.wasxfail`**（对比一下：XFAIL 那条会设 wasxfail 且 outcome=skipped）。
       所以只认 wasxfail 的代码会把它当成**普通回归失败** ——
       而这两件事含义完全相反：
         · FAILED = 以前好的现在坏了（要修）
         · XPASS = 标着 known_defect 的缺陷**这次没复现**（该复核、该摘标记）
       把它报成 FAILED，等于让"该摘的标记"永远没人摘、"真回归"又淹在里面。
    """
    return "[XPASS" in (report.longreprtext or "")


def _xpass_reason(report):
    """strict XPASS 的原因在 longrepr 里（形如 `[XPASS(strict)] xxx`），单独取出来。"""
    text = report.longreprtext or ""
    idx = text.find("[XPASS")
    if idx < 0:
        return ""
    return text[idx:].splitlines()[0].split("]", 1)[-1].strip()[:200]


# ---- 结尾汇总用到的小工具 ----

def _dw(text):
    """文本在终端里占几列：中文/全角算 2 列，其余算 1 列。

    表格只要含中文，str.ljust 就会歪 —— 它按"字符个数"补空格，
    而「模块」这两个字在终端里占的是 4 列。必须按显示宽度算。
    """
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _cell(text, width, align="left"):
    """把一个单元格补到指定"显示宽度"；至少留 1 个空格，免得两列粘在一起。"""
    fill = " " * max(width - _dw(text), 1)
    return fill + text if align == "right" else text + fill


def _module_of(nodeid):
    """`test_cases/ai_assistant/test_x.py::test_y` → `ai_assistant`。"""
    parts = nodeid.split("::")[0].split("/")
    return parts[1] if len(parts) > 1 else parts[0]


def _short_nodeid(nodeid):
    """失败清单里只留「文件名::用例名」—— 前面的 test_cases/ 路径对定位没用。"""
    path, _, rest = nodeid.partition("::")
    name = path.split("/")[-1]
    return f"{name}::{rest}" if rest else name


def _write_footer(reporter, text, color):
    _term_write("\n" + text + "\n", **{color: True})


def _record_outcome(report):
    """把一条用例的结果记进评测留痕（**纯旁路**，不改任何显示/判定）。

    和上面那套"画块尾"的逻辑刻意分开写，理由：
      · 画块尾只认 call 阶段（给人看的）；
      · 留痕要认 **setup/teardown 阶段的 error**（夹具就挂了的用例，评测报告里同样是失败），
        还要把 xfail 和 failed **分开**存 —— 报告里把"已知缺陷"算进"回归失败"，数字就废了。
    所以两件事不共用一份代码：显示可以省，数据不能省。
    """
    wasxfail = getattr(report, "wasxfail", None)
    if report.when == "call":
        if report.passed:
            outcome = "xpassed" if wasxfail is not None else "passed"
        elif report.skipped:
            outcome = "xfailed" if wasxfail is not None else "skipped"
        else:
            # strict XPASS 走这里（failed + longrepr 带 [XPASS）—— 不是回归失败
            outcome = "xpassed" if (wasxfail is not None or _is_xpass(report)) else "failed"
        reason = (wasxfail if wasxfail is not None else "") or _reason(report)
        if outcome == "xpassed" and not reason:
            reason = _xpass_reason(report)
        eval_record.record_outcome(report.nodeid, outcome, report.duration, reason)
    elif report.failed:
        eval_record.set_outcome_if_absent(report.nodeid, "error", report.duration, _reason(report))


def pytest_runtest_logreport(report):
    # 记账：这条 report 的耗时累加到它所属模块。
    # 一条用例会来三条 report（setup / call / teardown），三条都要加 ——
    # 只算 call 会漏掉夹具里登录、清场的时间，而那部分往往比用例本身还久。
    mod = _module_of(report.nodeid)
    _module_duration[mod] = _module_duration.get(mod, 0.0) + report.duration

    _record_outcome(report)             # 评测留痕（与下面的显示逻辑互不相干）

    # call 阶段：成功/失败/跳过都画块尾
    if report.when == "call":
        name = pad(_short_name(report.nodeid), _NAME_WIDTH)
        wasxfail = getattr(report, "wasxfail", None)
        if report.passed:
            text = f"└─ ✔ PASSED  {name} {report.duration:.2f}s"
            _write_footer(_reporter, text, "green")
            meta_log.info("✓ %s %.2fs", name, report.duration)
        elif wasxfail is not None and report.skipped:
            # xfail 与"真跳过"分开显示：前者是"已知缺陷等着修"，后者是"这条没写"
            text = f"└─ ⊘ XFAIL   {name}  {wasxfail}"
            _write_footer(_reporter, text, "yellow")
            meta_log.info("x %s (预期失败: %s)", name, wasxfail)
        elif report.skipped:
            text = f"└─ ⊘ SKIPPED {name}"
            _write_footer(_reporter, text, "yellow")
            meta_log.info("- %s (跳过)", name)
        else:
            is_xpass = wasxfail is not None or _is_xpass(report)
            label = "XPASS" if is_xpass else "FAILED"
            reason = _reason(report) or (_xpass_reason(report) if is_xpass else "")
            text = f"└─ ✘ {label}  {name} {report.duration:.2f}s  {reason}"
            _write_footer(_reporter, text, "red")
            meta_log.error("✗ %s %.2fs  %s", label + " " + name, report.duration, reason)
    elif report.failed:
        # setup / teardown 阶段挂掉（典型：夹具里就报错）
        reason = _reason(report)
        text = f"└─ ✘ ERROR   [{report.when} 阶段] {report.nodeid}  {reason}"
        _write_footer(_reporter, text, "red")
        meta_log.error("✗ [%s 阶段] %s  %s", report.when, report.nodeid, reason)


def _collect_summary(terminalreporter):
    """从 terminalreporter.stats 汇总一次，返回统计结果（无 reporter 时返回 None）。

    抽成独立函数是因为**两个钩子都要用**：
      · pytest_sessionfinish    → 写文件日志（不受 --no-summary 影响）
      · pytest_terminal_summary → 写控制台（会被 --no-summary 跳过）
    """
    if terminalreporter is None:
        return None

    stats = terminalreporter.stats

    # ⚠️ 必须按 nodeid 归并三个阶段（setup / call / teardown）的报告，不能直接数 report：
    #   一条用例可能 call 通过、teardown 报错（典型：越权用例的清理失败），
    #   在 stats 里会同时占 passed 和 error 两条 —— 直接相加，
    #   216 条用例会算成 221 条，总数从此不可信。
    by_node = {}
    for key in ("passed", "failed", "skipped", "xfailed", "error"):
        for rep in stats.get(key, []):
            by_node.setdefault(rep.nodeid, []).append(rep)

    outcome_of = {}
    for nodeid, reps in by_node.items():
        call = next((r for r in reps if r.when == "call"), None)
        has_error = any(r.when in ("setup", "teardown") and r.failed for r in reps)

        if call is not None and call.passed:
            # call 过了但 teardown 炸了，整条仍算"错误"——清场没做干净不能报绿
            outcome_of[nodeid] = "error" if has_error else "passed"
        elif call is not None and call.failed:
            outcome_of[nodeid] = "failed"
        elif call is not None and call.skipped:
            outcome_of[nodeid] = (
                "xfailed" if getattr(call, "wasxfail", None) is not None else "skipped"
            )
        else:
            # 没有 call 报告：setup 就挂了 / setup 里 skip 了
            outcome_of[nodeid] = "error" if has_error else "skipped"

    passed_n = sum(1 for o in outcome_of.values() if o == "passed")
    call_failed_n = sum(1 for o in outcome_of.values() if o == "failed")
    error_n = sum(1 for o in outcome_of.values() if o == "error")
    skipped_n = sum(1 for o in outcome_of.values() if o == "skipped")
    xfailed_n = sum(1 for o in outcome_of.values() if o == "xfailed")
    failed_n = call_failed_n + error_n
    total_n = len(outcome_of)

    # 按模块聚合：只统计"这次真跑过"的模块，没跑的模块不占一行
    rows = {}
    field_of = {"passed": "passed", "failed": "failed",
                "error": "failed", "skipped": "skipped", "xfailed": "xfailed"}
    for nodeid, outcome in outcome_of.items():
        name = _module_of(nodeid)
        rows.setdefault(name, {"passed": 0, "failed": 0, "skipped": 0, "xfailed": 0})
        rows[name][field_of[outcome]] += 1

    # 失败清单：一条用例只出一条（call 失败优先；只有夹具错误时用 error 报告）
    failed_reports = []
    for nodeid, outcome in outcome_of.items():
        if outcome not in ("failed", "error"):
            continue
        reps = by_node[nodeid]
        rep = next((r for r in reps if r.when == "call" and r.failed), None)
        if rep is None:
            rep = next(r for r in reps if r.when in ("setup", "teardown") and r.failed)
        failed_reports.append(rep)

    return {
        "passed_n": passed_n,
        "failed_n": failed_n,
        "error_n": error_n,
        "skipped_n": skipped_n,
        "xfailed_n": xfailed_n,
        "total_n": total_n,
        "call_failed_n": call_failed_n,
        "rows": rows,
        "failed_reports": failed_reports,
    }


def _log_summary(summary):
    """把总账写进文件日志。

    ⚠️ 必须由 pytest_sessionfinish 调用，不能只放在 pytest_terminal_summary：
      pytest 的 TerminalReporter 在 `--no-summary` 下会**整个跳过**
      pytest_terminal_summary 钩子（_pytest/terminal.py：
      `if exitstatus in summary_exit_codes and not self.no_summary:`）。
      而 PyCharm 默认的 pytest 参数就带 `--no-header --no-summary -q`，
      于是日志里只剩逐条结果，没有总数。
      pytest_sessionfinish 不受这个开关影响，总账放这里才稳。
    """
    elapsed = (time.perf_counter() - _started_at) if _started_at else 0.0
    meta_log.info(
        "══════════ 会话结束  passed=%d failed=%d error=%d skipped=%d "
        "xfailed=%d  总=%d  用时=%.1fs ══════════",
        summary["passed_n"], summary["call_failed_n"], summary["error_n"],
        summary["skipped_n"], summary["xfailed_n"],
        summary["total_n"], elapsed,
    )
    for name in sorted(summary["rows"]):
        r = summary["rows"][name]
        meta_log.info("  %-14s 通过=%-3d 失败=%-3d 跳过=%-3d 预期失败=%-3d 耗时=%.1fs",
                      name, r["passed"], r["failed"], r["skipped"], r["xfailed"],
                      _module_duration.get(name, 0.0))
    if summary["failed_reports"]:
        meta_log.error("  失败用例（%d 条）：", summary["failed_n"])
        for rep in summary["failed_reports"]:
            meta_log.error("  ✘ %s  %s", rep.nodeid, _reason(rep))


def pytest_sessionfinish(session, exitstatus):
    """会话结束：把评测留痕落盘，并把总账写进文件日志。

    ⚠️ 评测留痕只在**真的采到观测**时才写 —— 跑一批非 AI 用例（0 次模型调用）
    不该把上一份完整评测数据覆盖成一份空的。
    """
    global _eval_path
    path = eval_record.dump(_eval_out, meta={
        "scope": " ".join(session.config.invocation_params.args),
        "rootdir": str(session.config.rootdir),
    })
    _eval_path = str(path) if path else None

    # 文件日志的总账放在这里：--no-summary（PyCharm 默认参数）会跳过
    # pytest_terminal_summary，但不会跳过 sessionfinish。
    reporter = session.config.pluginmanager.getplugin("terminalreporter")
    summary = _collect_summary(reporter)
    # --collect-only 这类"没真跑用例"的会话不写全零总账，免得日志里多一行噪声
    if summary is not None and summary["total_n"]:
        _log_summary(summary)

    # ---- Allure：补上"环境信息"和"缺陷分类" ----
    # 这两样不属于任何一条用例，所以放在会话收尾统一写进结果目录。
    # 注意顺序无所谓：allure 是在**生成报告时**才去读它们的。
    if _allure_dir is not None:
        allure_helper.write_environment(
            _allure_dir, session.config, summary, started_at=_started_wall)
        allure_helper.copy_categories(_allure_dir)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """结尾汇总增强：总计行 + 按模块统计表 + 失败清单（压轴）。

    为什么是"总计 → 表 → 失败清单"这个顺序：
      跑完最想知道"整体过没过"，其次"哪个模块有问题"，最后才是
      "具体哪几条、为什么"。失败清单必须落在**整个输出的最末尾** ——
      失败时眼睛直接看最后几行就够了，不用往上翻页找 nodeid。

    ⚠️ 为什么敢接管 terminalreporter.summary_stats：
      pytest 最后那行 "===== N passed, M failed =====" 由 summary_stats() 打印，
      而所有插件的 pytest_terminal_summary 钩子都**早于**它执行
      （--durations 的表就出现在它上面）。想让"失败清单"排在最后，
      只能接管这个函数，在它原本要打印的位置换成我们的内容。

    统计口径（三处容易踩）：
      · passed / failed 只认 call 阶段 —— setup 阶段通过的报告不进 stats；
      · error（setup / teardown 挂了，典型是夹具报错）并进"失败"列，
        对看的人而言都是红的，单开一列没意义（清单里会标出是哪个阶段）；
      · skipped 全算（函数体内 skip 记在 call，夹具里 skip 记在 setup）；
      · 耗时按模块累加**三条** report（setup + call + teardown）——
        只算 call 会漏掉夹具里登录 / 清场的时间，那部分常常比用例本身还久。

    ⚠️ 文件日志的总账**不在这里写**，放在 pytest_sessionfinish：
      本钩子会被 `--no-summary` 整个跳过（PyCharm 默认就带这个参数），
      写在这里等于"IDE 里跑就没有总数"。
    """
    # --collect-only：一条用例都没跑，交给 pytest 自己打印
    # "N tests collected"；接管汇总行会把它替换成"未执行任何用例"，反而误导。
    if config.getoption("collectonly", default=False):
        return

    summary = _collect_summary(terminalreporter)
    if summary is None:
        return

    passed_n = summary["passed_n"]
    failed_n = summary["failed_n"]
    skipped_n = summary["skipped_n"]
    xfailed_n = summary["xfailed_n"]
    total_n = summary["total_n"]
    rows = summary["rows"]
    failed_reports = summary["failed_reports"]
    elapsed = (time.perf_counter() - _started_at) if _started_at else 0.0

    # 控制台：接管 pytest 的末尾汇总行
    def _enhanced_summary():
        terminalreporter.write_sep(
            "=", "测试结果: %d passed, %d failed, %d skipped, %d xfailed, %d in %.1fs"
                 % (passed_n, failed_n, skipped_n, xfailed_n, total_n, elapsed))

        if rows:
            terminalreporter.write_line(
                _cell("模块", 16) + _cell("通过", 6, "right")
                + _cell("失败", 6, "right") + _cell("跳过", 6, "right")
                + _cell("预期失败", 10, "right") + _cell("耗时", 10, "right"))
            for name in sorted(rows):
                r = rows[name]
                terminalreporter.write_line(
                    _cell(name, 16) + _cell(str(r["passed"]), 6, "right")
                    + _cell(str(r["failed"]), 6, "right") + _cell(str(r["skipped"]), 6, "right")
                    + _cell(str(r["xfailed"]), 10, "right")
                    + _cell("%.1fs" % _module_duration.get(name, 0.0), 10, "right"))

        terminalreporter.write_line("")
        if failed_reports:
            terminalreporter.write_line("失败用例（%d 条）：" % failed_n)
            for rep in failed_reports:
                phase = "" if rep.when == "call" else "[%s 阶段] " % rep.when
                mark = "✘ XPASS  " if _is_xpass(rep) else "✘ "
                terminalreporter.write_line(" " + mark + phase + _short_nodeid(rep.nodeid), red=True)
                reason = _reason(rep) or (_xpass_reason(rep) if _is_xpass(rep) else "")
                if len(reason) > 120:      # 汇总只给"一句话原因"，别把整段断言摊在这里
                    reason = reason[:120] + "…"
                if reason:
                    terminalreporter.write_line("     → " + reason)
        elif total_n:
            terminalreporter.write_line("没有失败用例 ✓", green=True)
        else:
            # 探活没通过 / 收集失败时会走到这里：一条用例都没跑，
            # 再打"没有失败用例 ✓"会让人以为这轮是绿的。
            terminalreporter.write_line("未执行任何用例（见上方原因）", red=True)

        if _eval_path:
            c = eval_record.counts()
            terminalreporter.write_line(
                "评测留痕: %s（观测 %d 条；调模型 %d 次 / 硬拦 %d 次）"
                " —— 跑 tools/eval_runner.py 出指标"
                % (_eval_path, c["observations"], c["model_calls"], c["blocked_calls"]),
                cyan=True)

    terminalreporter.summary_stats = _enhanced_summary


# ==================== Allure 报告的层级标签 ====================
# 目标：报告里能按 「接口自动化 → 模块 → 文件 → 用例」 点开，
#       而不是 98 条用例平铺成一坨、只能靠搜文件名。
#
# ⚠️ 关键决定：**不给用例加装饰器，按 nodeid 自动推标签。**
#   逐个加 `@allure.feature("登录")` 的代价不是"多打几行字"：
#     · 加新用例时**一定会忘**，忘了就掉进报告里一个无分类的孤儿；
#     · 想调整分组（"AI 助手"要不要再拆成"安全"和"功能"）要动几十个文件。
#   目录名 = 模块、文件名 = 资源，本来就是项目约定（README 第五节第 6 条），
#   标签直接从这套约定里长出来，**零维护**。
#
# 标签取值表放在 common/allure_helper.py（一张 dict），要改名去那里改。
# 用例若自己想要更细的标价，直接加装饰器即可 —— 这里会跳过已有的类型。

def _has_allure_label(item, label_type):
    """这条用例是不是已经有某类 allure 标签了（装饰器加的优先）。"""
    return any(mark.kwargs.get("label_type") == label_type
               for mark in item.iter_markers(name="allure_label"))


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    """收集完、开跑前：打 Allure 层级标签 + 按 AUTOTEST_REQUIRE_DB 跳过 DB 用例。

    为什么可以在这里加、值又是什么时候被读走的：
      allure-pytest 是在 **pytest_runtest_teardown** 里读 `allure_label`
      标记的（listener.py: `test_result.labels.extend(...allure_labels(item))`），
      远晚于收集阶段 —— 所以此刻 add_marker 来得及。

    ⚠️ 不能在这里用 `allure.dynamic.feature(...)`：
      那套 API 要求"当前有正在执行的用例"，收集阶段一条都还没跑，调用无效。
      记录这一点，是因为它看起来更"正宗"，很容易踩。

    trylast：必须等 health/ai_assistant 的 conftest 先把 requires_db 标上，
    这里才能按标记加 skip。否则顺序反过来会"一条都没跳过"。
    """
    if allure_helper.available():
        for item in items:
            for label_type, value in allure_helper.derive_labels(item.nodeid):
                if not _has_allure_label(item, label_type):
                    # 注意参数顺序：值是 args，类型是 kwargs["label_type"]。
                    # 写成 allure_label(label_type, value) 会静默不生效 —— 标记照挂，
                    # 但 allure 读不到 label_type，报告里那一栏永远是空的。
                    item.add_marker(pytest.mark.allure_label(value, label_type=label_type))

    _apply_requires_db_skip(items)
