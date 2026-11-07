# common/auth_state.py
# 作用：**用接口拿 token，直接写进浏览器 localStorage（sh_session），跳过 UI 登录**。
#
# 这是整层 UI 自动化里唯一"值得单独写一个模块"的东西，原因：
#   一次 UI 登录 = 填表(2 次输入) + 点按钮 + 等 axios + 等路由跳转 + 等档案接口，
#   实测 2.5~4s。十几条用例就是 40s 纯等待，而且每次都走同一段代码 ——
#   登录表单一旦改版，十几条用例一起红，失败原因全指向"登录页选择器变了"，
#   真正的业务缺陷被埋在中间。
#
#   直注之后：一次 requests 登录（约 80ms）+ 一次 add_init_script，几乎零成本。
#
# ── 为什么直注是"等价于登录"，不是伪造 ──────────────────────────
#   front2 的登录成功回调（stores/app.js 的 enter(res.data)）做的事情就是：
#       localStorage['sh_session'] = JSON.stringify(res.data 挑出的字段)
#   这里注入的 payload 和它**是同一个东西**（字段清单见 build_session），
#   所以"注入了还是被踢回登录页"只可能是注入本身不对，而不是"测试环境特殊"。
#
#   健康档案不在 session 里（front2 用 sh_health / sh_health_filled 另存），
#   且档案页挂载时会 GET /health/info 以后端为准 —— 所以这里**不伪造档案数据**，
#   缺档案时由 ensure_profile() 用接口补建（那是测试数据准备，不是绕过校验）。
#
#   写错 key 的症状很隐蔽：守卫读不到 session 会把你送回 /login，
#   看起来像"token 无效"，实际是 key 名不对。所以 key 名提成常量，
#   和 front2/src/services/http.js 的 SESSION_KEY 保持字面一致。
#
# ── 为什么不 import 接口层的 common.accounts ────────────────────
#   两个项目各有一个 `common` 包，同名包同时进 sys.path 会互相盖住，
#   症状是 ImportError 或"导进来的是另一个项目的函数"，且只在 IDE 里偶发。
#   这里直接用 requests 打同一个 /auth/login（同一套账号、同一份契约、同一个测试库），
#   复用的是**接口和账号体系**，不是代码文件 —— 这是刻意选择，不是省事。

import json
import time

import requests

from config.config import BACKEND_URL, PROFILE, TEST_USER, TEST_USERNAME

LOGIN_PATH = "/auth/login"
REGISTER_PATH = "/auth/register"

# 与 front2/src/services/http.js 的 SESSION_KEY、stores/app.js 的 K.session 一致。
# http.js 从这里读 token 发请求 —— 写错这个 key，注入后所有请求都是 401。
SESSION_KEY = "sh_session"

# token 缓存文件。和 storage_state 放一起，方便人工打开看。
# 缓存的唯一目的是**同一台机器连跑多轮时省一次登录**，
# 不是"持久保持登录状态"—— 每次仍会校验 exp。
CACHE_TTL = 600  # 秒；超过就重新登，别拿一个快过期的 token 去跑一整场


class AuthBootstrapError(RuntimeError):
    """拿不到可用 token。消息直接面向人，调用方原样展示。"""


# ==================== 账号准备（走接口）====================

def _json(resp):
    try:
        return resp.json()
    except ValueError:
        return {"raw": (resp.text or "")[:200]}


def _ok(status_code, body):
    return status_code == 200 and body.get("code") == 200


def login_via_api(email=None, password=None, timeout=10):
    """用接口登录，返回 data：{userId, username, email, phone, avatar, role, token}。

    账号不存在时自动注册一次 —— 和接口层 common/accounts.py 同一个思路：
    空库换机器时，要给出的应该是"账号已自动补建"，而不是十几条 UI 用例红在登录页。
    """
    email = email or TEST_USER["email"]
    password = password or TEST_USER["password"]
    payload = {"email": email, "password": password}

    resp = requests.post(BACKEND_URL + LOGIN_PATH, json=payload, timeout=timeout)
    body = _json(resp)
    if _ok(resp.status_code, body):
        data = body.get("data") or {}
        if not data.get("token"):
            raise AuthBootstrapError(f"登录成功但响应里没有 token：{body}")
        return data

    # 登录失败 → 尝试注册（空库/换机器时的保险丝）
    reg = requests.post(
        BACKEND_URL + REGISTER_PATH,
        json={"username": TEST_USERNAME, "email": email, "password": password},
        timeout=timeout,
    )
    reg_body = _json(reg)
    if _ok(reg.status_code, reg_body):
        data = reg_body.get("data") or {}
        if data.get("token"):
            return data

    message = str(reg_body.get("message", ""))
    raise AuthBootstrapError(
        f"UI 自动化拿不到 token：{email} 登录失败（HTTP {resp.status_code}），"
        f"自动注册也没成功。\n"
        f"  · 登录响应：{body}\n"
        f"  · 注册响应：{reg_body}\n"
        f"  排查顺序：\n"
        f"    1) 后端在跑吗？{BACKEND_URL}\n"
        f"    2) 后端连的是测试库吗？（UI 用例会写档案/饮食记录，别打开发库）\n"
        f"    3) 密码对不上时改环境变量 AUTOTEST_PASSWORD，别改代码\n"
        + (f"    · 提示：{message}" if message else "")
    )


def token_exp_seconds(token):
    """从 JWT 里读 exp（秒），读不到返回 None。

    为什么要自己解 JWT 而不问后端：
      前端 isLoggedIn 也是看本地 session 里的 token 有没有过期，
      要保证"注入的 token 前端认可"，判据必须和前端一致。
  """
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        import base64

        raw = base64.urlsafe_b64decode(payload.encode("ascii"))
        return int(json.loads(raw).get("exp"))
    except Exception:
        return None


def is_expired(token, skew=60):
    """token 是否过期（留 skew 秒余量：别拿一个 10 秒后过期的 token 跑用例）。"""
    exp = token_exp_seconds(token)
    if exp is None:
        return False  # 没有 exp 就当前端认为"不过期"，和前端判据保持一致
    return exp <= time.time() + skew


# ==================== 登录态直注 ====================

def build_session(account):
    """从接口登录返回的 data 里挑出会话需要的字段。

    前端 enter() 显式挑了这几个字段（多带不带都不报错，但少带会丢显示），
    这里保持同一份清单，别把 res.data 整包塞进去 ——
    后端将来往 data 里加字段时，整包塞会把这些字段悄悄变成"前端可读的隐藏数据"。
    """
    return {
        "userId": account.get("userId"),
        "username": account.get("username") or "",
        "email": account.get("email") or "",
        "phone": account.get("phone") or "",
        "role": account.get("role") or "user",
        "avatar": account.get("avatar") or "",
        "token": account.get("token") or "",
    }


def build_init_script(account):
    r"""生成往 localStorage 写 sh_session 的 init script。

    ⚠️ 三个必须踩对的点：
      1) 必须注册在 **context** 上，且在 new_page / goto **之前**。
         页面自己的 JS 跑之前先执行 —— pinia 的 store 在模块加载时就读一次
         localStorage，晚一步守卫就判完了，等于"人已经进登录页了才补票"。
         注册后该 context 下每次导航都会先跑这段脚本，不需要"先 goto 空白页再 evaluate"。
      2) localStorage 是**按 origin 隔离**的。前端在 5174，token 就写在 5174 下；
         写去 8081（后端）没有任何用。
      3) 用 json.dumps 序列化，别手拼字符串 —— 用户名里有中文、可能带引号，
         手拼一定会在某个账号上炸，而且报的是 JS 语法错误，与账号无关的样子。
         ensure_ascii=True 是为了把中文转成 \uXXXX：U+2028/U+2029 会截断 JS 字符串字面量。
    """
    payload = json.dumps({"session": build_session(account)}, ensure_ascii=True)
    return (
        "(() => {"
        f"  const p = {payload};"
        f"  localStorage.setItem('{SESSION_KEY}', JSON.stringify(p.session));"
        "})();"
    )


def build_storage_state(account, base_url):
    """Playwright storage_state 结构（人工调试用，运行走 init_script）。

    和 add_init_script 的区别：
      · init_script 每次新 context 都重新执行，天然干净；
      · storage_state 是一份"已经写好的快照"，可以直接喂给
        browser.new_context(storage_state=...)，也能被 `playwright codegen --load-storage`
        读去做手工调试 —— 排查"注入了还是被踢回登录页"时比截图直观。
    """
    from urllib.parse import urlparse

    origin = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    return {
        "cookies": [],
        "origins": [
            {
                "origin": origin,
                "localStorage": [
                    {
                        "name": SESSION_KEY,
                        "value": json.dumps(build_session(account), ensure_ascii=False),
                    }
                ],
            }
        ],
    }


# ==================== 健康档案预建 ====================
# 档案页的数据唯一来源是后端 GET /health/info（healthFilled 由此判定），
# 测试账号没档案时 KPI 区整个 v-if 掉，档案用例无从跑起。
# 所以在会话开始时用接口补建一条（幂等：有就不动），和 login_via_api
# 里"账号不存在自动注册"是同一个思路 —— 环境缺数据该补的是环境，不是改用例。
#
# payload 按前端适配器 toHealthDTO 的合同来（gender 收 male/female、
# activityLevel 存中文标签）。字段值必须跟前端形状一致，这正是
# "直注数据必须跟前端形状一致"的又一次体现。

_HEALTH_INFO = "/health/info"


def ensure_profile(account, profile=None, timeout=10):
    """保证测试账号在后端有健康档案。返回 True 表示新建了，False 表示本来就有。

    profile 默认取 config.PROFILE（档案回归基线），字段值按前端合同转换：
    activityLevel 存中文标签、慢病转逗号串。
    """
    profile = profile or PROFILE
    token = account["token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(BACKEND_URL + _HEALTH_INFO, headers=headers, timeout=timeout)
    body = _json(resp)
    if _ok(resp.status_code, body) and body.get("data"):
        return False  # 已有档案，不动 —— 别覆盖测试库里的既有数据

    payload = {
        "age": profile["age"],
        "gender": "male" if profile["gender"] == "male" else "female",
        "height": profile["height"],
        "weight": profile["weight"],
        "bloodPressure": profile["bloodPressure"],
        "bloodSugar": profile["bloodSugar"],
        # 下拉选项是中文标签，后端原样存
        "activityLevel": "中度活动",
        "exerciseDuration": profile["exerciseDuration"],
        "exerciseType": "",
        "chronicDiseases": "" if profile["chronicDiseases"] in ("无", "") else profile["chronicDiseases"],
    }
    resp = requests.post(
        BACKEND_URL + _HEALTH_INFO, json=payload, headers=headers, timeout=timeout
    )
    body = _json(resp)
    if not _ok(resp.status_code, body):
        raise AuthBootstrapError(
            f"健康档案预建失败（HTTP {resp.status_code}）：{body}\n"
            f"  档案用例依赖测试账号有档案；也可以手动在档案页填一次。"
        )
    return True
