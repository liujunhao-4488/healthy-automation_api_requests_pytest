# common/artifacts.py
# 作用：失败现场留存 —— 截图 + trace，并挂到 Allure 附件。
#
# 设计原则：**只在失败时保存，且一定保存成功**。
#   UI 缺陷最难查的不是"错了"，而是"错在哪个瞬间"。
#   报错只给一行 TimeoutError 和 nodeid，等于让人拿 DOM 结构去猜页面长什么样。
#
# 三样东西互补，缺一个都要多花时间：
#   截图    → 看到失败瞬间长什么样（弹窗挡着？骨架屏还在转？）
#   trace   → 能拖时间轴回放，看到每一步的 DOM 快照、网络请求、console 报错
#   页面文本 → 断言失败时看不出"页面上写的是啥"，把相关文本抓出来最省事
#
# 为什么不直接用 pytest-playwright 的 --tracing=retain-on-failure：
#   它确实更省代码，但产物是"整场一个目录里的随机文件名"，
#   和 Allure 只能靠插件挂接，且无法按 nodeid 归档。
#   这个项目要的是"失败用例 → 点开就是它自己的 trace"，所以自己管文件名。

import re
import time
import traceback
from pathlib import Path

from config.config import ARTIFACTS

# Windows 文件名不允许的字符（nodeid 里带 :: / [] 这些）
_ILLEGAL = re.compile(r'[<>:"/\\|?*\[\]\s]+')


def safe_name(nodeid, max_len=120):
    """nodeid → 能当文件名的字符串。

    `test_cases/health/test_x.py::test_y[参数1]` → `health__test_x.py__test_y_参数1`
    保留目录段（而不是只留函数名）：同名函数在不同模块里很常见，
    全部落成 screenshot_1.png 就等于没留痕。
    """
    name = nodeid.replace("test_cases/", "").replace("test_cases\\", "")
    name = name.replace("::", "__")
    name = _ILLEGAL.sub("_", name)
    return name[:max_len].strip("_")


def save_screenshot(page, nodeid, full_page=True):
    """失败截图。返回路径，失败返回 None（截图失败绝不能再抛异常，否则盖住真错）。"""
    try:
        path = ARTIFACTS["screenshots"] / f"{safe_name(nodeid)}.png"
        page.screenshot(path=str(path), full_page=full_page)
        return path
    except Exception:
        return None


def save_trace(context, nodeid):
    """把 trace 落盘。返回路径，失败返回 None。"""
    try:
        path = ARTIFACTS["traces"] / f"{safe_name(nodeid)}.zip"
        context.tracing.stop(path=str(path))
        return path
    except Exception:
        return None


def stop_trace_discard(context):
    """用例通过时也要 stop，否则 context 关不干净（trace 缓冲留在内存里）。"""
    try:
        context.tracing.stop()
    except Exception:
        pass


def page_snapshot_text(page, limit=600):
    """抓一段当前页面可见文本 —— 断言失败时最省事的一份上下文。

    只取 body 的 innerText 前 limit 字：整页 HTML 有几十 KB，
    塞进报告没人看；innerText 恰好是"用户看到的内容"。
    """
    try:
        text = page.locator("body").inner_text(timeout=2000)
    except Exception:
        return ""
    text = re.sub(r"\n{2,}", "\n", text).strip()
    return text[:limit]


def attach(path, name, attachment_type=None):
    """挂到 Allure。没装 allure-pytest 时静默跳过（不影响本地跑）。"""
    if path is None:
        return
    try:
        import allure
    except ImportError:
        return

    path = Path(path)
    try:
        if attachment_type is not None:
            allure.attach.file(str(path), name=name, attachment_type=attachment_type)
        elif path.suffix == ".png":
            allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
        elif path.suffix == ".zip":
            # trace 是 zip。在报告里点下载后 `playwright show-trace x.zip` 打开。
            # ZIP 类型不是所有 allure 版本都有，取不到就不指定类型（照样能下载）。
            zip_type = getattr(allure.attachment_type, "ZIP", None)
            allure.attach.file(str(path), name=name, attachment_type=zip_type)
        else:
            allure.attach.file(str(path), name=name)
    except Exception:
        pass


def attach_text(content, name):
    if not content:
        return
    try:
        import allure
    except ImportError:
        return
    try:
        allure.attach(content, name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass


def current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def format_exc(exc):
    """异常压成"最后一行 + 位置"，给汇总用。"""
    lines = traceback.format_exception_only(type(exc), exc)
    return (lines[-1] if lines else str(exc)).strip()[:300]
