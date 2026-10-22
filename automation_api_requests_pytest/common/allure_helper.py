# common/allure_helper.py
# 【工具】Allure 报告的"总闸门"：整个项目只有这个文件 import allure。
#
# ── 为什么要多这一层，而不是各写各的 `import allure` ────────────────
# 项目里跟报告打交道的地方有四处，全散着写会出两个问题：
#   ① 换报告框架（allure → reportportal / 自研 HTML）要改四处；
#   ② **没装 allure 时整包 import 就炸** —— 一个"锦上添花"的报告
#      不该把"跑用例"这件事搞挂。降级必须是静默的。
# 所以：这里 try/except 包住 import，装了就干活、没装就全员变空操作。
# 调用方（api / logger / conftest）一律只认本文件暴露的函数。
#
# ── 这里的四件事 ────────────────────────────────────────────────
#   1. attach_http(resp)   每次 HTTP 请求 → 报告里贴"请求"+"响应"两个附件
#   2. attach_qa(...)      AI 用例的一问一答 → 贴成一段可读文本
#   3. derive_labels(...)  按**目录/文件名**自动推出 层级 与 严重级别
#                          （不用去几百个用例上逐个加 @allure.feature）
#   4. write_environment / copy_categories  给报告补"环境信息"和"缺陷分类"

import json
import os
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path

from config.config import BASE_URL, KB_BASE_URL

# ---- allure 的"装没装" ----
# 注意：这里 catch 的是 **Exception 而不是 ImportError**。
# 原因：allure-pytest 与 pytest 版本不匹配时抛的是别的异常（如 AttributeError），
# 只 catch ImportError 的话，一个坏掉的报告插件会把整场测试带崩。
try:
    import allure
    from allure_commons.types import AttachmentType

    _HAS_ALLURE = True
except Exception:                                    # pragma: no cover - 降级分支
    allure = None
    AttachmentType = None
    _HAS_ALLURE = False


# ---- 本次运行"到底出不出报告" ----
# 装了 allure ≠ 在出报告：可能只是 `-p no:allure`、或者压根没给结果目录。
# 由 conftest 在 sessionstart 时打开，之后所有 attach 才真的干活。
_ACTIVE = False

# 凭据脱敏开关：默认开。本地排查想看明文时设环境变量 ALLURE_NO_MASK=1。
_MASK = os.environ.get("ALLURE_NO_MASK", "") == ""

# 单段正文最多贴多少字符。SSE 和大响应体能到几十 KB，
# 全贴进去会让报告文件膨胀到几十 MB、浏览器打开卡死。
_MAX_BODY = 20_000

_MASK_TEXT = "***（已脱敏）"

# 这些 key 的值一律打码。全小写比较 —— JSON 里是 camelCase。
_SECRET_KEYS = {"password", "token", "accesstoken", "refreshtoken"}

# 这些请求头一律打码
_SECRET_HEADERS = {"authorization", "cookie", "set-cookie", "x-token"}


# ==================== 开关 ====================

def available():
    """allure 这个包到底装上没有。"""
    return _HAS_ALLURE


def activate(flag=True):
    """由 conftest 在会话开始时调用：本次运行要不要往报告里写东西。"""
    global _ACTIVE
    _ACTIVE = bool(flag and _HAS_ALLURE)


def enabled():
    """现在能不能往报告里写（既装了、又开着）。"""
    return _ACTIVE


# ==================== 底层：附件的安全写入 ====================

def _safe(func, *args, **kwargs):
    """执行一个上报动作；**任何异常都吞掉**。

    为什么敢吞：报告是旁路。它出错（allure 内部状态异常、磁盘满、
    在用例之外调用拿不到当前用例）时，正确的做法是"这条附件没有"，
    而不是让一条本来通过的用例变红 —— 那是把观测工具变成了被测对象。
    真要排查报告问题，设 ALLURE_DEBUG=1 让异常照常抛出。
    """
    try:
        return func(*args, **kwargs)
    except Exception:
        if os.environ.get("ALLURE_DEBUG"):
            raise
        return None


def attach_text(name, text, attachment_type=None):
    """贴一段纯文本到当前用例上。"""
    if not _ACTIVE:
        return
    body = text if isinstance(text, str) else str(text)
    _safe(allure.attach, _truncate(body), name=name,
          attachment_type=attachment_type or AttachmentType.TEXT)


def attach_json(name, obj):
    """贴一段 JSON（报告里会**格式化高亮**，不是一团字符串）。"""
    if not _ACTIVE:
        return
    text = json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    _safe(allure.attach, _truncate(text), name=name,
          attachment_type=AttachmentType.JSON)


# ==================== 脱敏 ====================

def _mask_value(value):
    """递归给敏感字段打码（不改结构，只换值）。"""
    if isinstance(value, dict):
        return {k: (_MASK_TEXT if k.lower() in _SECRET_KEYS else _mask_value(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [_mask_value(item) for item in value]
    return value


def _mask_header(name, value):
    """请求头打码。

    Authorization 特殊处理：**留前 8 个字符**。
    全打码的话，报告里就分不清"用的是 A 的 token 还是 B 的 token"——
    而越权用例恰恰靠这一点回看现场（谁拿谁的 token 打了谁的数据）。
    留一截既能辨认，又不至于把可用凭据摊在一份会被转发出去的 HTML 里。
    """
    text = str(value)
    scheme, _, token = text.partition(" ")
    if scheme.lower() == "bearer" and token:
        return "%s %s…%s（共 %d 字符）" % (scheme, token[:8], _MASK_TEXT, len(token))
    return _MASK_TEXT


def _headers_text(headers):
    if not headers:
        return "（无）"
    lines = []
    for key, value in headers.items():
        if _MASK and key.lower() in _SECRET_HEADERS:
            value = _mask_header(key, value)
        lines.append("%s: %s" % (key, value))
    return "\n".join(lines)


def _body_text(body):
    """把请求体 / 响应体整理成"人能读"的样子。"""
    if body is None or body == "":
        return "（无）"

    if isinstance(body, bytes):
        try:
            body = body.decode("utf-8")
        except UnicodeDecodeError:
            return "（%d 字节二进制，不展开）" % len(body)

    if not isinstance(body, str):
        body = str(body)

    # JSON 才格式化；表单/纯文本原样。解析失败就说明它本来就不是 JSON。
    try:
        parsed = json.loads(body)
    except (ValueError, TypeError):
        return _truncate(body)

    if _MASK:
        parsed = _mask_value(parsed)
    return _truncate(json.dumps(parsed, ensure_ascii=False, indent=2))


def _truncate(text, limit=None):
    limit = limit or _MAX_BODY
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n…（正文共 %d 字符，此处截断；完整内容见 logs/runs/ 下的运行日志）" % len(text)


def _short_url(url):
    """`http://127.0.0.1:8080/api/user/profile` → `/user/profile`。"""
    for base in (BASE_URL, KB_BASE_URL):
        if url.startswith(base):
            return url[len(base):]
    return url


# ==================== 1. HTTP 请求 / 响应 ====================

def attach_http(resp):
    """把一次 HTTP 交互贴进报告：**两个附件**，请求一个、响应一个。

    从这里（BaseApiClient._log）上报的好处是"一处埋点、全覆盖"：
    项目里所有业务请求都走 BaseApiClient，所以几百条用例、上千次调用
    一次都不用改，报告里每一次交互都自然带上了完整现场。

    为什么拆成两个附件而不是一个大字符串：
      报告里点开附件是**独立面板**，请求和响应并排看才方便对账
      （"我传了这个，它回了我那个"）；混成一段要来回滚。

    ⚠️ SSE 流式响应**绝对不读 .text**：
      对 stream=True 的响应调 .text 会把整条流读干，接口层随后就拿不到数据
      （test_assistant_流式.py 直接挂）。所以内容类型是 event-stream 时只贴头。
    """
    if not _ACTIVE:
        return

    req = resp.request
    method = req.method
    path = _short_url(req.url)

    request_text = "%s %s\n\n【请求头】\n%s\n\n【请求体】\n%s" % (
        method, req.url, _headers_text(req.headers), _body_text(req.body))
    attach_text("→ 请求　%s %s" % (method, path), request_text)

    elapsed_ms = resp.elapsed.total_seconds() * 1000 if resp.elapsed else 0.0
    content_type = resp.headers.get("Content-Type", "")
    if "event-stream" in content_type.lower():
        body_text = "（SSE 流式响应，正文在读取过程中被消费，不在此抓取）"
    else:
        body_text = _body_text(resp.text)

    response_text = "HTTP %d　（耗时 %.0f ms）\n\n【响应头】\n%s\n\n【响应体】\n%s" % (
        resp.status_code, elapsed_ms, _headers_text(resp.headers), body_text)
    attach_text("← 响应　%d %s" % (resp.status_code, path), response_text)


# ==================== 2. AI 问答 ====================

def attach_qa(question, answer, turn=None):
    """把一问一答贴进报告。

    AI 用例的价值**全在回答文本里**，可断言往往只是"没出现某个词"——
    绿灯但答非所问的情况，只有把原文摊在报告里才看得出来。
    """
    if not _ACTIVE:
        return
    title = "第 %d 轮问答" % turn if turn else "问答"
    attach_text(title, "问：%s\n\n答：%s" % (question, answer))


# ==================== 3. 标签（层级 + 严重级别） ====================

# 目录 → (中文模块名, 默认严重级别)
#
# 级别为什么这么分：allure 的 severity 是给"先看哪条红的"用的，
# 不是给"这条重不重要"打分的。判据是**挂了会怎样**：
#   · 登录 / 用户资料：挂了说明鉴权或越权出了问题 —— 全站都要停
#   · 健康档案：挂了是单个功能不可用
#   · 工具自检：挂了只影响我们自己的脚手架
# 想改某一条：在用例上直接加 `@allure.severity(allure.severity_level.BLOCKER)`，
# 本表只提供默认值，**用例自己的标价优先**（见 conftest 的 _has_label 判断）。
MODULE_LABELS = {
    "auth": ("登录注册", "critical"),
    "user": ("用户资料", "critical"),
    "health": ("健康档案", "normal"),
    "ai_assistant": ("AI 助手", "normal"),
    "toolbox": ("测试工具自检", "minor"),
}

# 文件 → 中文"故事"名。
# 为什么不从文件名自动转：`test_assistant_结构鉴权` 机器拆出来是
# "assistant 结构鉴权"，而人想看的是"结构 / 鉴权 / 参数校验"。
# 这张表就是**唯一**需要维护的地方，加文件时补一行即可（漏了也有兜底）。
STORY_LABELS = {
    "test_login": "登录",
    "test_register": "注册",
    "test_user_profile": "个人资料",
    "test_health_info": "健康档案",
    "test_health_goal": "饮食目标",
    "test_data_loader": "数据加载器",
    "test_assistant_结构鉴权": "结构 / 鉴权 / 参数校验",
    "test_assistant_意图识别": "意图识别（模型行为）",
    "test_assistant_意图标签": "意图标签准确率",
    "test_assistant_安全拦截": "输入安全拦截（代码硬拦）",
    "test_assistant_注入": "提示注入",
    "test_assistant_越狱": "越狱对抗",
    "test_assistant_越权": "水平越权（IDOR）",
    "test_assistant_上下文": "多轮上下文",
    "test_assistant_流式": "SSE 流式响应",
    "test_assistant_RAG召回": "RAG 召回（直连 5000）",
    "test_assistant_RAG生成": "RAG 生成（经 8080）",
    "test_assistant_通用问题不追问档案": "通用问题不追问档案",
}

EPIC_NAME = "健康饮食后端 · 接口自动化"
PARENT_SUITE_NAME = "健康饮食后端 API"


def _fallback_story(stem, module):
    """表里没有的新文件：`test_recipe_search` → `recipe search`。"""
    name = stem[5:] if stem.startswith("test_") else stem
    if module and name.startswith(module + "_"):
        name = name[len(module) + 1:]
    return name.replace("_", " ") or stem


def derive_labels(nodeid):
    """按 nodeid 推出 7 个标签，返回 [(label_type, value), ...]。

    这样做的取舍，值得写清楚：
      · 逐个用例加 `@allure.feature("登录")` —— 想改分组要动上百个文件，
        而且新人加用例**一定会忘**（忘了就掉进报告里一个无分类的孤儿）。
      · 按目录/文件推 —— 一次都不用加，新增文件自动归位。
      代价是"文件"和"故事"必须同名同义，靠 STORY_LABELS 这张表兜住。
    """
    path = nodeid.split("::")[0]
    parts = path.replace("\\", "/").split("/")
    module = parts[1] if len(parts) > 1 else parts[0]
    stem = parts[-1][:-3] if parts[-1].endswith(".py") else parts[-1]

    feature, severity = MODULE_LABELS.get(module, (module, "normal"))
    story = STORY_LABELS.get(stem) or _fallback_story(stem, module)

    return [
        ("epic", EPIC_NAME),
        ("parentSuite", PARENT_SUITE_NAME),
        ("suite", feature),
        ("subSuite", story),
        ("feature", feature),
        ("story", story),
        ("severity", severity),
    ]


# ==================== 4. 结果目录 / 环境信息 / 缺陷分类 ====================

def results_dir(config):
    """本次 allure 结果目录；没装 allure 则返回 None。

    ⚠️ 这里**顺手把默认目录写回 config.option**，不是"只读一下"。
      理由见 conftest.py 的 pytest_configure —— 一句话：
      目录要用**绝对路径**，而且要赶在 allure 自己的 configure 之前定下来。
    """
    if not _HAS_ALLURE:
        return None

    configured = getattr(config.option, "allure_report_dir", None)
    if configured is None:
        # 默认目录钉在项目根下，而不是"当前工作目录"：
        # 在 PyCharm 里把工作目录设成 test_cases/ 时，相对路径会把结果写到别处，
        # 找不着还以为报告没生成。
        configured = str(Path(config.rootpath) / "reports" / "allure-results")
        config.option.allure_report_dir = configured
        # 默认目录是"一次运行一份"，所以默认清空；
        # 用户自己用 --alluredir 指定目录时不动他的（那是他自己要攒历史）。
        config.option.clean_alluredir = True

    return Path(configured).resolve()


def _properties_escape(text):
    """按 Java Properties 规则转义（非 ASCII → \\uXXXX）。

    为什么必须转义：allure-commandline 是 **Java 程序**，它用
    `Properties.load()` 读这个文件，而那玩意儿按 ISO-8859-1 解码。
    直接把中文写进去，报告顶部"环境信息"里会变成一串 `æµ‹è¯•` 乱码。
    转成 \\uXXXX 之后，Java 会自己还原成中文。
    """
    out = []
    for char in str(text):
        code = ord(char)
        if char == "\\":
            out.append("\\\\")
        elif char in ("\n", "\r", "\t"):
            out.append("\\" + {"\n": "n", "\r": "r", "\t": "t"}[char])
        elif code < 128:
            out.append(char)
        else:
            out.append("\\u%04X" % code)
    return "".join(out)


def _package_version(distribution, fallback="未知"):
    """读某个**已安装包**的版本号。

    不能 `import allure_pytest; allure_pytest.__version__` —— 那个包没导出
    `__version__`（会静默拿到"未知"）。要看发行包的元数据才是对的。
    """
    try:
        from importlib.metadata import version

        return version(distribution)
    except Exception:
        return fallback


def write_environment(directory, config, summary=None, started_at=None):
    """往结果目录写 environment.properties —— 报告首页右侧"环境"面板就是它。

    这块最容易被跳过，但它回答的是事故复盘时**第一个**要问的问题：
    "这份报告是在哪台机器、打哪个后端、什么版本下跑出来的？"
    没有它，一份三个月前的报告等于没有价值。
    """
    if not _HAS_ALLURE or directory is None:
        return None

    # 这两个只在真正写环境信息时才需要，懒加载：
    # 本模块会被 common/logger.py 导入，而 logger 是几乎每个文件都 import 的东西，
    # 没必要为了"可能不写报告"的运行提前把它俩拽进来。
    import pytest
    import requests

    # ⚠️ 键名**不要带空格**。allure 把键的第一个空格当成"分组"（实测：
    #    `Run Started = ...` 会被拆成 组名 "Run" + 值 "Started = ..."）。
    #    所以统一用大写下划线，报告里就是干干净净的一行一个指标。
    rows = [
        ("API_BASE_URL", BASE_URL),
        ("KB_BASE_URL", KB_BASE_URL + "（算法服务 / RAG 召回直连）"),
        ("PYTHON", platform.python_version()),
        ("PYTEST", pytest.__version__),
        ("ALLURE_PYTEST", _package_version("allure-pytest")),
        ("REQUESTS", requests.__version__),
        ("PLATFORM", platform.platform()),
        ("INTERPRETER", sys.executable),
        ("RUN_STARTED", (started_at or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")),
        ("COMMAND", " ".join(str(arg) for arg in config.invocation_params.args)),
    ]
    if summary:
        rows.append(("TOTAL", str(summary.get("total_n", ""))))
        rows.append(("PASSED", str(summary.get("passed_n", ""))))
        rows.append(("FAILED", str(summary.get("failed_n", ""))))
        rows.append(("SKIPPED", str(summary.get("skipped_n", ""))))
        rows.append(("XFAILED", str(summary.get("xfailed_n", ""))))

    text = "\n".join("%s = %s" % (key, _properties_escape(value)) for key, value in rows) + "\n"

    try:
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "environment.properties"
        target.write_text(text, encoding="utf-8")
        return target
    except OSError:
        return None


def copy_categories(directory):
    """把 config/allure_categories.json 复制进结果目录。

    allure 只从**结果目录**读 categories.json，所以不能只放一份在 config/ 下，
    每次运行都要搬一次。搬失败就当没有分类 —— 报告照样能看。
    """
    if not _HAS_ALLURE or directory is None:
        return None

    source = Path(__file__).resolve().parent.parent / "config" / "allure_categories.json"
    if not source.exists():
        return None
    try:
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "categories.json"
        shutil.copyfile(source, target)
        return target
    except OSError:
        return None
