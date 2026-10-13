# common/logger.py
# 【工具】测试日志：把"每一次跑用例的过程"记下来。
#
# 输出分工（2026-10-13 改版）：
#   · 控制台：只打"用例分块 + 一行请求摘要"，完整响应体不刷屏；
#             用例失败时，pytest 自动把该用例捕获到的日志/print 展开在失败详情里。
#   · 文件：每一次运行一个独立文件 logs/runs/run-YYYY-MM-DD_HHMMSS.log，
#           内容完整（含全部响应体）；同时刷新 logs/latest.log 始终指向最近一次。
#
# 谁会往这个日志里写东西：
#   · conftest.py 的 hook  → 每条用例的开始 / 结果 / 耗时（**自动**）
#   · api/base_api_client.py → 每次发请求记一行：方法 路径 → 状态码 (耗时)（**自动**，单行）
#   · 用例自己             → 想看完整响应时手动 `log_response(resp)`（多行进文件，控制台默认不展开）
#   · AI 类用例           → 用 `log_qa(问题, 回答)` 把"问什么答什么"压成一行
#
# 用法（用例里）：
#     from common.logger import log, log_response
#     resp = api.auth.login({"email": ..., "password": ...})
#     log_response(resp)                 # 完整 body 落日志文件
#     log_response(resp, max_chars=200)  # 只记前 200 字符

import json
import logging
import sys
import unicodedata
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# logs/ 在项目根下（本文件在 common/ 里，所以往上一级）
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
RUNS_DIR = LOG_DIR / "runs"
LATEST_LOG = LOG_DIR / "latest.log"
LEGACY_LOG = LOG_DIR / "autotest.log"

# ---- 格式 ----
# 三条原则：
#   ① 前缀只留必须的：HH:MM:SS + 一个字母级别。日期在同一份文件里重复几十遍，纯噪音。
#   ② 变的放后面：固定列（状态码、耗时）排前面并且对齐，长度不定的正文放最后。
#   ③ 一行一条：正文里不许有换行（多行响应体由 log_response 单独缩进）。
_FORMAT = "%(asctime)s %(levelname).1s %(message)s"
_DATEFMT = "%H:%M:%S"


def short_url(url):
    """把 `http://127.0.0.1:8080/api/auth/login` 砍成 `/auth/login`。"""
    try:
        from config import BASE_URL
    except Exception:
        return url
    return url[len(BASE_URL):] if url.startswith(BASE_URL) else url


def _display_width(text):
    """文本占几列。中文/全角字符占 2 列，其余占 1 列。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, width):
    """按"显示宽度"右补空格到指定列宽（至少留 1 个空格，避免两列粘一起）。"""
    return text + " " * max(width - _display_width(text), 1)


_IN_PYTEST = "pytest" in sys.modules
_ready = False


def _install_file_handler(handler):
    """把一个文件 handler 挂到 root，统一用精简格式。"""
    handler.setFormatter(logging.Formatter(_FORMAT, _DATEFMT))
    logging.getLogger().addHandler(handler)


def begin_run_log():
    """pytest 会话开始时调用：本次运行的日志写到独立文件，并刷新 latest.log。

    放在 pytest_configure 里调用，比"所有运行共用一个轮转文件"更容易回溯：
    一次运行一个文件，文件名带时间，互不覆盖；latest.log 永远是最近一次，方便快速打开。
    """
    global _ready
    if _ready:
        return
    _ready = True

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_file = RUNS_DIR / f"run-{stamp}.log"

    _install_file_handler(logging.FileHandler(run_file, encoding="utf-8"))
    # latest.log 每次运行以写模式打开，天然只留最近一次内容
    _install_file_handler(logging.FileHandler(LATEST_LOG, mode="w", encoding="utf-8"))
    logging.getLogger().setLevel(logging.INFO)
    return run_file


def _ensure_handlers():
    """非 pytest 场景（独立脚本）的兜底：写 autotest.log（轮转）+ 控制台。

    pytest 下不装这套，控制台分块由 conftest 的专用 handler 接管，
    文件由 begin_run_log() 按运行命名。
    """
    global _ready
    if _ready:
        return
    _ready = True

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fh = RotatingFileHandler(LEGACY_LOG, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(logging.Formatter(_FORMAT, _DATEFMT))
    root.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter(_FORMAT, _DATEFMT))
    root.addHandler(sh)


def get_logger(name="autotest", level=logging.INFO):
    """拿日志器。handler 只装一次，反复调用不会叠加。"""
    if not _IN_PYTEST:
        _ensure_handlers()
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


# 模块级日志器：用例里 `from common.logger import log` 直接用
log = get_logger()


def format_response(resp, max_chars=0):
    """把一次响应整理成「一行摘要 + 缩进的多行 body」。"""
    ms = resp.elapsed.total_seconds() * 1000
    head = "→ %-4s %-18s %3d %6.0fms" % (
        resp.request.method, short_url(resp.request.url), resp.status_code, ms)

    try:
        text = json.dumps(resp.json(), ensure_ascii=False, indent=2)
    except ValueError:
        text = resp.text

    if max_chars and len(text) > max_chars:
        text = text[:max_chars] + "\n...(已截断)"

    body = "\n".join("    " + ln for ln in text.splitlines())
    return head + "\n" + body


def log_response(resp, max_chars=0):
    """记录一次完整响应（摘要 + body），并把 resp 原样返回，方便链式调用。

    完整 body 只进日志文件；控制台默认不展开（由 conftest 的分块 handler 过滤）。
    5xx 才算警告——4xx 是我们主动测出来的正常剧情，"错得对不对"由断言判。
    """
    level = logging.WARNING if resp.status_code >= 500 else logging.INFO
    log.log(level, "%s", format_response(resp, max_chars=max_chars))
    return resp


def log_qa(question, answer, max_chars=100):
    """把"问了什么 → 答了什么"压成**一行**，给 AI 类用例当"肉眼观察窗"。"""
    text = " ".join(str(answer).split())
    if len(text) > max_chars:
        text = text[:max_chars] + "…"
    log.info("· AI    %s → %s", pad("问「%s」" % question, 22), text)
