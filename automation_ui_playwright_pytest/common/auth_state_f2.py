# common/auth_state_f2.py
# 作用：**front2（膳衡 Vue3 重写版）的 token 直注**。
#
# 和老版 auth_state.py 的差别必须写清楚，不能"顺手复用"：
#
#   老版 frontend/ 存两处：
#       localStorage['token']       = 裸 JWT
#       localStorage['health-user'] = 完整用户态 JSON（含 healthInfo）
#   front2/ 只存一处（stores/app.js 的 enter()）：
#       localStorage['sh_session']  = { userId, username, email, phone, role, avatar, token }
#
#   → 拿 login_via_api() 返回的 data **直接整体写进去**就够了，
#     形状就是后端登录响应的 data，一字不差 —— 这不是巧合：
#     前端 enter(res.data) 也是原样存。注入数据和真实登录产生的是同一个东西，
#     这是"直注等价于登录"最硬的证据，比任何注释都有说服力。
#
#   健康档案不放在会话里（sh_health / sh_health_filled 另存），
#   且档案页挂载时会 GET /health/info 以后端为准 —— 所以 front2 的直注
#   **不需要**伪造档案数据，那是老版路由守卫才有的特殊要求。
#
#   顺带：写错 key 的症状很隐蔽 —— 守卫读不到 session 会把你送回 /login，
#   看起来像"token 无效"，实际是 key 名不对。所以这里把 key 名提成常量，
#   和 stores/app.js 里的 K.session 保持字面一致。

import json

import requests

from common.auth_state import AuthBootstrapError, _json, _ok
from config.config import BACKEND_URL, PROFILE

# 与 front2/src/services/http.js 的 SESSION_KEY、stores/app.js 的 K.session 一致。
# http.js 从这里读 token 发请求 —— 写错这个 key，注入后所有请求都是 401。
SESSION_KEY = "sh_session"


def build_f2_session(account):
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


def build_f2_init_script(account):
    """生成往 localStorage 写 sh_session 的 init script。

    和老版同样的三条铁律（详见 auth_state.build_init_script 的注释）：
      1) 必须注册在 context 上，且在 new_page / goto 之前 ——
         pinia 的 store 在模块加载时就读一次 localStorage，晚一步守卫就判完了；
      2) localStorage 按 origin 隔离，注入只对 front2 自己的页面生效（5174）；
      3) 用 json.dumps 序列化，别手拼字符串。
    """
    payload = json.dumps({"session": build_f2_session(account)}, ensure_ascii=True)
    return (
        "(() => {"
        f"  const p = {payload};"
        f"  localStorage.setItem('{SESSION_KEY}', JSON.stringify(p.session));"
        "})();"
    )


def build_f2_storage_state(account, base_url):
    """Playwright storage_state 结构（人工调试用，运行走 init_script）。

    `playwright codegen --load-storage=<这个文件> <front2地址>` 能直接进已登录态，
    排查"注入了还是被踢回登录页"时比截图直观。
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
                        "value": json.dumps(build_f2_session(account), ensure_ascii=False),
                    }
                ],
            }
        ],
    }


# ---------------- 健康档案预建 ----------------
# front2 档案页的数据唯一来源是后端 GET /health/info（healthFilled 由此判定），
# 测试账号没档案时 KPI 区整个 v-if 掉，档案用例无从跑起。
# 所以在会话开始时用接口补建一条（幂等：有就不动），和 auth_state.login_via_api
# 里"账号不存在自动注册"是同一个思路 —— 环境缺数据该补的是环境，不是改用例。
#
# payload 按 front2 自己的适配器 toHealthDTO 的合同来（gender 收 male/female、
# activityLevel 存中文标签），别抄老版 PROFILE 的取值 —— 两版前端对同一字段
# 的约定不一样，这正是"直注数据必须跟前端形状一致"的又一次体现。

_F2_HEALTH_INFO = "/health/info"


def ensure_f2_profile(account, profile=None, timeout=10):
    """保证测试账号在后端有健康档案。返回 True 表示新建了，False 表示本来就有。

    profile 默认取 config.PROFILE（它同时是老版直注的档案基线），
    但字段值按 front2 的合同转换：activityLevel 存中文标签、慢病转逗号串。
    """
    profile = profile or PROFILE
    token = account["token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(BACKEND_URL + _F2_HEALTH_INFO, headers=headers, timeout=timeout)
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
        # front2 的下拉选项是中文标签，后端原样存
        "activityLevel": "中度活动",
        "exerciseDuration": profile["exerciseDuration"],
        "exerciseType": "",
        "chronicDiseases": "" if profile["chronicDiseases"] in ("无", "") else profile["chronicDiseases"],
    }
    resp = requests.post(
        BACKEND_URL + _F2_HEALTH_INFO, json=payload, headers=headers, timeout=timeout
    )
    body = _json(resp)
    if not _ok(resp.status_code, body):
        raise AuthBootstrapError(
            f"front2 档案预建失败（HTTP {resp.status_code}）：{body}\n"
            f"  档案用例依赖测试账号有档案；也可以手动在 front2 档案页填一次。"
        )
    return True
