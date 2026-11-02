# config/config.py
# 作用：UI 自动化的「会变的东西」集中放一处，全部可用环境变量覆盖。
#
# 和接口自动化 automation_api_requests_pytest/config/config.py 走同一套约定：
#   AUTOTEST_* 前缀，换机器 / 换 CI 只改环境变量，不改代码。
#
# 默认值保证「本机 clone 下来、服务起来、直接能跑」。

import os


def _env(name, default):
    return os.getenv(name, default)


def _env_int(name, default):
    return int(os.getenv(name, str(default)))


def _env_bool(name, default=False):
    return os.getenv(name, ("1" if default else "0")) == "1"


# ------------------------------------------------------------
# 被测前端
# ------------------------------------------------------------
# frontend/（Vue3 + Element Plus，老版）—— 主目标
FRONTEND_URL = _env("AUTOTEST_UI_BASE_URL", "http://127.0.0.1:5173")
# front2/（Vue3 + Vite5，新版）—— 次目标，单独一套用例
FRONT2_URL = _env("AUTOTEST_FRONT2_URL", "http://127.0.0.1:5174")

# 后端地址：只用于「环境预检」判断服务活没活，UI 用例本身不直连它
BACKEND_URL = _env("AUTOTEST_BASE_URL", "http://127.0.0.1:8081/api")

# ------------------------------------------------------------
# 账号
# ------------------------------------------------------------
# 与接口自动化保持一致：主账号由 database/seed_test.sql 提供（id=1, autotest_primary）
TEST_USER = {
    "email": _env("AUTOTEST_UI_EMAIL", _env("AUTOTEST_EMAIL", "2311697186@qq.com")),
    "password": _env("AUTOTEST_UI_PASSWORD", _env("AUTOTEST_PASSWORD", "123456")),
    "username": _env("AUTOTEST_UI_USERNAME", "autotest_primary"),
}

# 管理员账号 —— /admin/* 鉴权矩阵的对照组
ADMIN_USER = {
    "email": _env("AUTOTEST_UI_ADMIN_EMAIL", _env("AUTOTEST_ADMIN_EMAIL", "admin@qq.com")),
    "password": _env("AUTOTEST_UI_ADMIN_PASSWORD", _env("AUTOTEST_ADMIN_PASSWORD", "123456")),
}

# ------------------------------------------------------------
# 浏览器行为
# ------------------------------------------------------------
HEADLESS = _env_bool("AUTOTEST_UI_HEADLESS", True)

# 有头模式下是否放慢动作（毫秒）。调试 / 录屏时用：
#   set AUTOTEST_UI_SLOWMO=300
SLOWMO = _env_int("AUTOTEST_UI_SLOWMO", 0)

# 视口默认 1440x900 —— 前端 Dashboard 是「左侧栏 + 内容区」布局，
# 小于 1280 会把侧边栏折叠掉，选择器跑偏。
VIEWPORT = {
    "width": _env_int("AUTOTEST_UI_WIDTH", 1440),
    "height": _env_int("AUTOTEST_UI_HEIGHT", 900),
}

# Chromium / Firefox / WebKit
BROWSER = _env("AUTOTEST_UI_BROWSER", "chromium")

LOCALE = _env("AUTOTEST_UI_LOCALE", "zh-CN")
TIMEZONE = _env("AUTOTEST_UI_TIMEZONE", "Asia/Shanghai")

# ------------------------------------------------------------
# 稳定性 / 可观测
# ------------------------------------------------------------
# 单个元素等待上限。整页首屏（Vite 冷启动 + 后端 JWT 校验）实测 3~5s，
# 给到 15s 是为了 CI 上冷启动也稳；用例层不要再自己写 sleep。
DEFAULT_TIMEOUT = _env_int("AUTOTEST_UI_TIMEOUT", 15_000)

# 失败时是否记录 trace 并截图 / 录像（产物挂到 Allure 附件）
TRACE_ON_FAILURE = _env_bool("AUTOTEST_UI_TRACE", True)

# 是否复用「一次登录、多次用例」的 storage_state 缓存。
#   纯 UI 登录链路用例（登录/注册）自己走完整表单，不走这里。
COOKIE_CACHE = _env_bool("AUTOTEST_UI_COOKIE_CACHE", True)

# 环境预检：进程没起就不要跑，避免整片红
REQUIRE_SERVICE = _env_bool("AUTOTEST_UI_REQUIRE_SERVICE", True)

# ------------------------------------------------------------
# 产物目录（按文件位置算，换工作目录也不会写错地方）
# ------------------------------------------------------------
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS = {
    "screenshots": PROJECT_ROOT / "artifacts" / "screenshots",
    "traces": PROJECT_ROOT / "artifacts" / "traces",
    "videos": PROJECT_ROOT / "artifacts" / "videos",
    "storage": PROJECT_ROOT / "artifacts" / "storage",
}

for _p in ARTIFACTS.values():
    _p.mkdir(parents=True, exist_ok=True)
