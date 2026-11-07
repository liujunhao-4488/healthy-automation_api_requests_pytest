# common/auth_state.py
# 作用：**用接口拿 token，直接注入浏览器本地存储，跳过 UI 登录**。
#
# 这是整层 UI 自动化里唯一"值得单独写一个模块"的东西，原因：
#   一次 UI 登录 = 填表(2 次输入) + 点按钮 + 等 axios + 等路由跳转 + 等档案接口，
#   实测 2.5~4s。十几条用例就是 40s 纯等待，而且每次都走同一段代码 ——
#   登录表单一旦改版，十几条用例一起红，失败原因全指向"登录页选择器变了"，
#   真正的业务缺陷被埋在中间。
#
#   直注之后：一次 requests 登录（约 80ms）+ 一次 add_init_script，几乎零成本。
#
# ── 为什么"不能只写 token 这一个键" ──────────────────────────────
#   前端存了两处（frontend/src/stores/user.js）：
#       localStorage['token']       = 裸 JWT 字符串
#       localStorage['health-user'] = 整个用户态 JSON（含 healthInfo / role / userId）
#
#   路由守卫（frontend/src/router/index.js）读的是 **health-user**，不是 token：
#       · 只写 token → 守卫里 `persisted` 为 null → role 默认 'user'、档案判为未完成
#       · 访问 /dashboard 能进（那条只查 token）
#       · 但进入任何"需要档案"的页面时，前端会认为你还没建档案，页面走空态
#       · 想测 /health-info-basic 引导流程时，反而**必须**不写 healthInfo
#   所以下面把「注入哪种状态」做成显式参数（profile_completed），
#   而不是让每个用例自己去拼 localStorage —— 拼错了会变成"前端 bug" 的假象。
#
# ── 为什么不 import 接口层的 common.accounts ────────────────────
#   两个项目各有一个 `common` 包，同名包同时进 sys.path 会互相盖住，
#   症状是 ImportError 或"导进来的是另一个项目的函数"，且只在 IDE 里偶发。
#   这里直接用 requests 打同一个 /auth/login（同一套账号、同一份契约、同一个测试库），
#   复用的是**接口和账号体系**，不是代码文件 —— 这是刻意选择，不是省事。
#
#   想彻底消除重复，正路是把账号保障抽成独立的 `autotest_shared` 包，
#   两个项目都装它。那是一次跨项目的结构调整，不该夹在 UI 层搭建里做。

import json
import time

import requests

from config.config import BACKEND_URL, TEST_USER, TEST_USERNAME

LOGIN_PATH = "/auth/login"
REGISTER_PATH = "/auth/register"

# token 缓存文件。和 storage_state 放一起，方便人工打开看。
# 缓存的唯一目的是**同一台机器连跑多轮时省一次登录**，
# 不是"持久保持登录状态"—— 每次仍会校验 exp。
CACHE_TTL = 600  # 秒；超过就重新登，别拿一个快过期的 token 去跑一整场


class AuthBootstrapError(RuntimeError):
    """拿不到可用 token。消息直接面向人，调用方原样展示。"""


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
      前端 isTokenExpired() 就是这么干的（裸 atob 解第二段），
      要保证"注入的 token 前端认可"，判据必须和前端一致。
      差一天就因为 exp 判错，症状是"注入了还是被踢回登录页"。
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
        return False  # 没有 exp 就当前端认为"不过期"，和 isTokenExpired 保持一致
    return exp <= time.time() + skew


def build_user_state(user, profile=None, profile_completed=True):
    """拼出前端 health-user 的完整结构。

    字段必须和 stores/user.js 的 loadPersistedUser() 一一对应 ——
    少写一个不会报错，只会让某个页面表现异常，排查时很难联想到"注入少了个字段"。

    profile_completed=False 时 healthInfo 置 None：
      路由守卫会判定"档案未完成"，用来测 /health-info-basic 的引导流程。
    """
    return {
        "userId": user.get("userId"),
        "username": user.get("username") or "",
        "email": user.get("email") or "",
        "phone": user.get("phone") or "",
        "avatar": user.get("avatar") or "",
        "role": user.get("role") or "user",
        "token": user.get("token") or "",
        "healthInfo": _profile_payload(profile) if profile_completed else None,
        "healthAnalysis": None,
        "dietGoal": None,
        "dietGoalMeta": None,
        "healthHistory": [],
        "recipeRecommendations": None,
        "ingredientAssistantHistory": [],
    }


def _profile_payload(profile):
    """把 config.PROFILE 转成前端 healthInfo 的形状。

    bmi / bmr 这里自己算而不是留空：
      它们是页面上的**只读派生值**，前端拿到 healthInfo 就直接渲染。
      留 null 的话页面上是空白，用例断言"BMI 有值"会失败，
      而失败原因是注入数据不全 —— 又会浪费一轮排查。
    """
    height_m = profile["height"] / 100.0
    bmi = round(profile["weight"] / (height_m ** 2), 1)

    # Mifflin-St Jeor（男 +5 / 女 -161）—— 和后端 HealthService 的公式一致
    base = 10 * profile["weight"] + 6.25 * profile["height"] - 5 * profile["age"]
    bmr = round(base + (5 if profile["gender"] == "male" else -161))

    return {
        "age": profile["age"],
        "gender": profile["gender"],
        "height": profile["height"],
        "weight": profile["weight"],
        "activityLevel": profile["activityLevel"],
        "bloodPressure": profile["bloodPressure"],
        "bloodSugar": profile["bloodSugar"],
        "exerciseDuration": profile["exerciseDuration"],
        "chronicDiseases": profile["chronicDiseases"],
        "bmi": bmi,
        "bmr": bmr,
    }


def build_init_script(token, user_state):
    """生成写 localStorage 的 JS。

    ⚠️ 三个必须踩对的点：
      1) add_init_script 注册在 **context** 上，且必须在 new_page / goto **之前**。
         它保证"页面自己的 JS 跑之前"先执行 —— pinia 的 state 初始化一上来就读
         localStorage，晚一步就等于用户已经进了登录页才补票，守卫早判完了。
         注意它**不要求先导航**：注册后该 context 下每次导航都会先跑这段脚本，
         所以不需要"先 goto 空白页再 evaluate"。那种写法多一次导航、多 300ms，
         而且遇到 SPA 内部路由变化时根本不会再执行。
      2) localStorage 是**按 origin 隔离**的。前端在 5173，token 就写在 5173 下；
         写去 8081（后端）没有任何用。脚本跟随页面 origin 自动落位，
         所以只能注入到"前端自己的页面"，这也是它必须是 init script 的原因。
      3) 用 json.dumps 序列化，别手拼字符串 —— 用户名/慢病描述里有中文、
         可能带引号，手拼一定会在某个账号上炸，而且报的是 JS 语法错误，与账号无关的样子。
    """
    # ensure_ascii=True：把中文转成 \uXXXX。
    # 直接用原字符也能跑，但 U+2028/U+2029 会截断 JS 字符串字面量，属于极难复现的坑。
    payload = json.dumps({"token": token, "user": user_state}, ensure_ascii=True)
    return (
        "(() => {"
        f"  const p = {payload};"
        "  localStorage.setItem('token', p.token);"
        "  localStorage.setItem('health-user', JSON.stringify(p.user));"
        "})();"
    )


def build_storage_state(token, user_state, base_url):
    """生成 Playwright 的 storage_state 结构（备用路径）。

    和 add_init_script 的区别：
      · init_script 每次新 context 都重新执行，天然干净；
      · storage_state 是一份"已经写好的快照"，可以直接喂给
        browser.new_context(storage_state=...)，也能被 `playwright codegen --load-storage`
        读去做手工调试 —— 排查时很有用，所以留着落盘。
    这里只生成当前前端 origin 下的条目，不掺别的域名。
    """
    from urllib.parse import urlparse

    origin = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    return {
        "cookies": [],
        "origins": [
            {
                "origin": origin,
                "localStorage": [
                    {"name": "token", "value": token},
                    {"name": "health-user", "value": json.dumps(user_state, ensure_ascii=False)},
                ],
            }
        ],
    }
