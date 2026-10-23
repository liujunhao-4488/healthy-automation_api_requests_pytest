# common/accounts.py
# 【运行前提自愈】测试账号不存在时自动注册，而不是让全场用例红在登录上。
#
# 为什么需要它：
#   以前 token 夹具默认 2311697186@qq.com 已经在库里。换机器/空库时，
#   登录 400 → token 拿不到 → 所有鉴权用例一起失败，真正原因被埋在几十条
#   traceback 里。现在先"登录；失败就注册；再失败才报一条人话"。
#
# 它和 database/seed_test.sql 的关系：
#   seed 是主路径（确定性最好，登录/注册数据驱动用例也依赖其中的 123456@qq.com）；
#   本模块是保险丝 —— 有人只建了表、忘了导种子，也能自己补出账号。
#
# 为什么有 raw 版本：
#   环境预检刻意不走 BaseApiClient（否则会在 Allure 里留下假的业务请求）。
#   raw 版本直接用 requests，只做账号保障，不产生测试附件。

import requests

from config.config import BASE_URL, SEED_LOGIN_USER, TEST_USER, TEST_USERNAME


class AccountBootstrapError(RuntimeError):
    """账号既登不上、也注册不了。消息直接面向人，调用方原样展示即可。"""


def _json(resp):
    try:
        return resp.json()
    except ValueError:
        return {"raw": (resp.text or "")[:200]}


def _is_ok(status_code, body):
    return status_code == 200 and body.get("code") == 200


def _ensure(login, register, email, password, username):
    """login/register 都是 (data) -> (status_code, body) 的可调用对象。"""
    status, body = login({"email": email, "password": password})
    if _is_ok(status, body):
        return body["data"]

    reg_status, reg_body = register({
        "username": username,
        "email": email,
        "password": password,
    })
    if _is_ok(reg_status, reg_body):
        return reg_body["data"]

    message = reg_body.get("message", "") if isinstance(reg_body, dict) else str(reg_body)
    duplicate_hints = ("已注册", "已被注册", "已被使用", "已存在", "重复", "占用")
    if any(hint in message for hint in duplicate_hints):
        raise AccountBootstrapError(
            f"账号 {email} 已存在，但用配置的密码登录失败。\n"
            f"  · 要么把 AUTOTEST_PASSWORD 改成该账号的真实密码；\n"
            f"  · 要么重建测试库：..\\database\\rebuild_test_db.bat（在 automation_api_requests_pytest 下执行）。\n"
            f"  登录响应：{body}"
        )

    raise AccountBootstrapError(
        f"自动创建测试账号 {email} 失败：{reg_body}\n"
        f"  · 检查后端是否连的是测试库；\n"
        f"  · 空库先执行：..\\database\\rebuild_test_db.bat（在 automation_api_requests_pytest 下执行）。"
    )


def ensure_account(api, email, password, username):
    """用 Api 客户端确保账号存在；适合用例夹具（请求会进日志/Allure）。"""
    def login(data):
        resp = api.auth.login(data)
        return resp.status_code, _json(resp)

    def register(data):
        resp = api.auth.register(data)
        return resp.status_code, _json(resp)

    return _ensure(login, register, email, password, username)


def ensure_account_raw(email, password, username, timeout=5):
    """用裸 requests 确保账号存在；适合环境预检（不产生 Allure 假请求）。"""
    def login(data):
        resp = requests.post(BASE_URL + "/auth/login", json=data, timeout=timeout)
        return resp.status_code, _json(resp)

    def register(data):
        resp = requests.post(BASE_URL + "/auth/register", json=data, timeout=timeout)
        return resp.status_code, _json(resp)

    return _ensure(login, register, email, password, username)


def ensure_primary_account(api=None):
    """补建 conftest.py 的 TEST_USER，返回 data（含 userId/token）。"""
    if api is not None:
        return ensure_account(api, TEST_USER["email"], TEST_USER["password"], TEST_USERNAME)
    return ensure_account_raw(TEST_USER["email"], TEST_USER["password"], TEST_USERNAME)


def ensure_login_seed_account(api=None):
    """补建登录/注册数据驱动用例依赖的 123456@qq.com。"""
    if api is not None:
        return ensure_account(
            api, SEED_LOGIN_USER["email"], SEED_LOGIN_USER["password"], SEED_LOGIN_USER["username"])
    return ensure_account_raw(
        SEED_LOGIN_USER["email"], SEED_LOGIN_USER["password"], SEED_LOGIN_USER["username"])
