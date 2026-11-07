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
# 被测前端（front2，Vue3 + Vite5）
# ------------------------------------------------------------
# ⚠️ 用 localhost 而不是 127.0.0.1：Vite 5 默认只绑 ::1（IPv6 localhost），
#    写 127.0.0.1 会连接拒绝（症状是探活 000、用例整片超时）。
FRONTEND_URL = _env("AUTOTEST_UI_BASE_URL", "http://localhost:5174")

# 后端地址：用于①环境预检 ②接口侧账号准备/档案预建（common/auth_state.py）
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

# 账号不存在、需要自动注册时用的用户名。
# 刻意和 TEST_USER["username"] 不同 —— 和接口层同一个理由：
#   登录响应返回的 username 要和库里的一致，用同一个名字会让"后端连错库"这种问题
#   在自动补建时"碰巧对上"，检查就失效了。
TEST_USERNAME = _env("AUTOTEST_UI_AUTO_USERNAME", "autotest_primary_auto")

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
    # allure 结果目录（json 原始结果，出报告要 allure generate 再转一次）
    "allure": PROJECT_ROOT / "artifacts" / "allure-results",
}

for _p in ARTIFACTS.values():
    _p.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 2026-11-07 追加：断言 / 慢链路 / 档案基线
# ------------------------------------------------------------
# 导航超时。和 DEFAULT_TIMEOUT（找元素）分开：
#   首屏要等 Vite 编译 + 后端 JWT 校验，比"找一个按钮"慢得多。
NAV_TIMEOUT = _env_int("AUTOTEST_UI_NAV_TIMEOUT", 20_000)

# 断言等待（expect 的重试上限）。比找元素短：
#   断言失败是**结论**，不该跟"元素还没渲染"混为一谈，等太久只会拖长失败反馈。
EXPECT_TIMEOUT = _env_int("AUTOTEST_UI_EXPECT_TIMEOUT", 8_000)

# AI 对话整段回复的上限。流式输出 + 后端调大模型，实测 8~25s，
# 给 60s 是为了模型慢响应时不算失败（真断流由用例断言"有内容"兜住）。
AI_TIMEOUT = _env_int("AUTOTEST_UI_AI_TIMEOUT", 60_000)

# 健康档案回归基线。
# ⚠️ 两处使用，必须是**库里真实存在的档案值**：
#   ① common/auth_state.ensure_profile() 用它给测试账号补建档案
#   ② 档案用例断言"页面回显的就是库里的值"
#   否则 UI 显示和基线对不上 —— 那种失败最难查：看起来像前端 bug，其实是测试数据没对齐。
# 注意 activityLevel 填的是前端的 value（moderately_active），不是页面上的中文标签。
PROFILE = {
    "age": _env_int("AUTOTEST_UI_PROFILE_AGE", 26),
    "gender": _env("AUTOTEST_UI_PROFILE_GENDER", "male"),
    "height": float(_env("AUTOTEST_UI_PROFILE_HEIGHT", "178")),
    "weight": float(_env("AUTOTEST_UI_PROFILE_WEIGHT", "70")),
    # 这里是**接口契约**里的取值（sedentary / lightly_active / ...），
    # 注意与页面上的中文标签（"中度活动"）不同：ensure_profile() 发给后端时要转成标签，
    # 用例断言页面回显时又要按标签比对 —— 两套表示法别混（front2 的下拉 value 就是中文）。
    "activityLevel": _env("AUTOTEST_UI_PROFILE_ACTIVITY", "moderately_active"),
    "bloodPressure": _env("AUTOTEST_UI_PROFILE_BP", "120/80"),
    "bloodSugar": float(_env("AUTOTEST_UI_PROFILE_SUGAR", "5.2")),
    "exerciseDuration": _env_int("AUTOTEST_UI_PROFILE_EXERCISE", 45),
    "chronicDiseases": _env("AUTOTEST_UI_PROFILE_CHRONIC", "无"),
}
