# conftest.py
# pytest 的"公共工具间"：夹具（fixture）与全局日志钩子都放这里，pytest 会自动加载。

import logging
import time
import unicodedata
from datetime import datetime

import pytest

from api import Api
from common import eval_record
from common.logger import begin_run_log, log, pad
from config.config import TEST_USER


# ==================== 夹具 ====================

@pytest.fixture
def api():
    """接口总入口夹具：用例里 api.auth.login(...) 就能发请求。"""
    return Api()


@pytest.fixture
def token(api):
    """登录夹具：拿测试账号登录一次，把 token 交给需要鉴权的用例。"""
    resp = api.auth.login(TEST_USER)
    body = api.assert_ok(resp)
    assert "token" in body["data"], "登录成功必须返回 token"
    return body["data"]["token"]


@pytest.fixture
def auth_headers(token):
    """把 token 包成请求头：{"Authorization": "Bearer xxx"}。"""
    return {"Authorization": f"Bearer {token}"}


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


def pytest_configure(config):
    # 先建本次运行的日志文件。terminalreporter / capturemanager 在 sessionstart 时使用。
    run_file = begin_run_log()
    meta_log.info("══════════ 会话开始 %s  本次日志: %s ══════════",
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"), run_file)


def pytest_sessionstart(session):
    global _reporter, _capturemanager, _handler, _started_at, _eval_out
    _started_at = time.perf_counter()          # 结尾汇总要用"整场跑了多久"
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


def pytest_sessionfinish(session, exitstatus):
    """会话结束：把评测留痕落盘，供 tools/eval_runner.py 离线算指标。

    ⚠️ 只在**真的采到观测**时才写 —— 跑一批非 AI 用例（0 次模型调用）
    不该把上一份完整评测数据覆盖成一份空的。
    """
    global _eval_path
    path = eval_record.dump(_eval_out, meta={
        "scope": " ".join(session.config.invocation_params.args),
        "rootdir": str(session.config.rootdir),
    })
    _eval_path = str(path) if path else None


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
    """
    stats = terminalreporter.stats

    def _reports(key, when=None):
        return [r for r in stats.get(key, []) if when is None or r.when == when]

    passed_reports = _reports("passed", "call")
    skipped_reports = _reports("skipped")
    xfailed_reports = _reports("xfailed")
    failed_reports = _reports("failed", "call") + _reports("error")

    passed_n = len(passed_reports)
    skipped_n = len(skipped_reports)
    xfailed_n = len(xfailed_reports)
    failed_n = len(failed_reports)
    total_n = passed_n + failed_n + skipped_n + xfailed_n
    elapsed = (time.perf_counter() - _started_at) if _started_at else 0.0

    # 按模块聚合：只统计"这次真跑过"的模块，没跑的模块不占一行
    rows = {}
    for key, when, field in (("passed", "call", "passed"),
                             ("failed", "call", "failed"),
                             ("error", None, "failed"),
                             ("skipped", None, "skipped"),
                             ("xfailed", None, "xfailed")):
        for rep in _reports(key, when):
            rows.setdefault(_module_of(rep.nodeid),
                            {"passed": 0, "failed": 0, "skipped": 0, "xfailed": 0})
            rows[_module_of(rep.nodeid)][field] += 1

    # ---------- ① 文件日志：留一份完整记账 ----------
    meta_log.info("══════════ 会话结束  passed=%d failed=%d error=%d skipped=%d xfailed=%d ══════════",
                  len(_reports("passed")), len(_reports("failed")),
                  len(_reports("error")), skipped_n, xfailed_n)
    for name in sorted(rows):
        r = rows[name]
        meta_log.info("  %-14s 通过=%-3d 失败=%-3d 跳过=%-3d 预期失败=%-3d 耗时=%.1fs",
                      name, r["passed"], r["failed"], r["skipped"], r["xfailed"],
                      _module_duration.get(name, 0.0))
    for rep in failed_reports:
        meta_log.error("  ✘ %s  %s", rep.nodeid, _reason(rep))

    # ---------- ② 控制台：接管 pytest 的末尾汇总行 ----------
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
        else:
            terminalreporter.write_line("没有失败用例 ✓", green=True)

        if _eval_path:
            c = eval_record.counts()
            terminalreporter.write_line(
                "评测留痕: %s（观测 %d 条；调模型 %d 次 / 硬拦 %d 次）"
                " —— 跑 tools/eval_runner.py 出指标"
                % (_eval_path, c["observations"], c["model_calls"], c["blocked_calls"]),
                cyan=True)

    terminalreporter.summary_stats = _enhanced_summary
