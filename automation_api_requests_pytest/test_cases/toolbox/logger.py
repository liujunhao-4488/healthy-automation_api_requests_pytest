# test_cases/toolbox/logger.py
# 【日志工具】一个配好的 logger + 一个"把接口响应打印好看"的函数。
#
# 为什么需要它？
#   用例里最高频的动作就是"发请求 → 看返回"。
#   直接 log.info(resp.json()) 打出来是一坨：单引号、挤在一行、
#   中文还会变成 \u4e2d\u6587 这种（因为 Python 默认 json.dumps 用 ASCII 转义）。
#   这个模块把「发到哪、状态码、耗时、返回了什么」整理成几行，扫一眼就够。
#
# 类比：log.info(resp.json()) 是把一箱零件直接倒桌上；
#       log_response(resp) 是按装配图摆好，一眼能看出哪个是哪个。

import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_LOG_NAME = "autotest"

# 当前是不是在 pytest 里跑？import 这一刻就能判断出来（pytest 早就加载了）。
# 用途见 get_logger() 里「控制台交给谁打」的注释。
_IN_PYTEST = "pytest" in sys.modules


def get_logger(name=_LOG_NAME):
    """拿一个配好的 logger：控制台打 INFO 以上，文件里记 DEBUG 以上。

    重复调用返回同一个对象（靠 `if logger.handlers` 拦），不会把日志打两遍。
    用法：log = get_logger()  →  log.info("xxx")
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件日志：按大小切割，永远都加（不管是不是在 pytest 里，都要留档）
    os.makedirs("logs", exist_ok=True)
    fh = RotatingFileHandler("logs/autotest.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # ---- 控制台日志：谁打？这里有个坑，记一下 ----
    # pytest 跑测试时会自己往 root 上挂一个 live log handler，按 pytest.ini 里的
    # log_cli_format（`I | autotest | ...`）实时显示日志。
    #   · 如果我们再加一个自己的 StreamHandler → 同一条打两遍；
    #   · 如果靠 propagate=False 把它挡住 → 更糟：pytest 专门有个逻辑，
    #     会去遍历所有「propagate=False 的 logger」并把 handler 补挂上去
    #     （源码 _pytest/logging.py：Attach to all non-propagating loggers），
    #     等于亲手把第二个 handler 请过来，照样打两遍。
    # 所以：pytest 环境下控制台交给它自己输出，我们只写文件；
    #       脱离 pytest 单独跑脚本时（PyCharm 直接运行）才自己加控制台 handler。
    if not _IN_PYTEST:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    # 配合上面的分工：pytest 下要往外传（它才能在 root 上接住），
    # 独立跑时不外传（避免和别人的 logging.basicConfig() 撞成两份）。
    logger.propagate = _IN_PYTEST
    return logger


def format_response(resp, max_chars=0):
    """把一次响应整理成好读的多行文本。只生成字符串，不写日志。

    单独拆出来是为了"可以被复用"——比如你想写进文件、或者塞进断言失败的提示里。
    """
    # requests 自己会记录耗时，不用我们拿 time 手动掐表
    ms = int(resp.elapsed.total_seconds() * 1000) if resp.elapsed else 0

    try:
        method, url = resp.request.method, resp.request.url
    except AttributeError:  # 理论上不会走到，兜个底
        method, url = "?", getattr(resp, "url", "?")

    head = "{} {}  ->  HTTP {}  ({}ms)".format(method, url, resp.status_code, ms)

    # ensure_ascii=False 是中文能正常显示的关键：不写它，中文会变成 \u4e2d\u6587
    # indent=2 让它换行缩进，嵌套结构一眼看清
    try:
        body = json.dumps(resp.json(), ensure_ascii=False, indent=2)
    except ValueError:
        # 返回的不是标准 JSON（比如 500 的空体、或 HTML 错误页），退化成原文
        body = (resp.text or "").strip() or "(空响应体)"

    if max_chars and len(body) > max_chars:
        body = "{}...\n（已截断，完整内容 {} 字符；要全量就把 max_chars 传 0）".format(
            body[:max_chars], len(body)
        )

    return "{}\n{}".format(head, body)


def log_response(resp, logger=None, max_chars=0):
    """把一次接口响应打进日志。用例里一行搞定：

        log_response(api.get("/user/profile", headers=auth_headers))

    返回 resp 本身，所以也能链式接着用：
        body = log_response(resp).json()

    - 成功（HTTP 2xx/3xx）打成 INFO，失败打成 WARNING —— 日志里一眼能挑出红的。
    - max_chars 默认 0 = 不截断（学习阶段建议全量看）。
      响应特别长（比如上百条列表）时可以传 2000 之类，只看开头。
    """
    log = logger or get_logger()
    text = format_response(resp, max_chars=max_chars)

    if resp.ok:
        log.info(text)
    else:
        log.warning(text)

    return resp


# 模块级默认 logger：这样 import 之后就能直接用
#   from test_cases.toolbox.logger import log, log_response
log = get_logger()
