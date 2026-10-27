# test_cases/auth/test_login_契约.py
# 【任务：登录响应的**结构契约**】
#
# ══ 和老文件 test_login.py 的分工 ═══════════════════════════════════
#
#   test_login.py      验「**值**对不对」：谁能登录、密码错了报什么、token 能不能用
#   本文件              验「**形状**对不对」：字段齐不齐、类型对不对、枚举有没有越界
#
#   一个观测点只归一个文件 —— 红了就知道该往哪边看：
#   值不对是业务逻辑，形状不对是 DTO / 序列化。
#
# ══ 为什么单独开文件而不是往老文件里加 ══════════════════════════════
#
#   老文件是「已验证过的、稳定对照物」，改它会把"原来是怎样的"这个信息毁掉。
#   新写法先在新文件里立住，等它自己跑出成绩，再决定要不要迁移。
#   （这也是本项目一直的做法：不动旧文件，新建对照。）

import pytest

from common.schemas import LOGIN_SCHEMA
from config.config import TEST_USER


# ==================== 一、成功：整份响应都要看住 ====================

def test_login_response_shape(api):
    """成功登录 → 信封 + data 的**每个字段**都要符合契约。

    对比老写法差在哪：
        body = api.assert_ok(resp)              # 只断 HTTP 200 + code 200
        assert "token" in body["data"]          # 只断 token 在
    —— 剩下 6 个字段是 int 变成 "1"、还是整个消失了，一条都发现不了。
    """
    resp = api.auth.login({
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
    })

    body = api.assert_ok(resp, "登录应成功", schema=LOGIN_SCHEMA)

    # 形状由 spec 看住，这里只补一条**语义**断言：token 必须真的能用
    # （non-empty 是形状，能拿去鉴权才是价值 —— 但那是 profile 用例的事，此处不越界）
    assert body["data"]["token"].strip(), "token 不该是空白字符串"


# ==================== 二、失败：三种原因，同一套信封 ====================
# 期望值全部来自实测（2026-10-26 真打 8080）：
#   密码错     → 400 / 密码错误
#   邮箱不存在 → 400 / 用户不存在
#   空邮箱     → 400 / 邮箱不能为空
#
# ⚠️ 三条都是 400 不是 401：说明后端把"凭据不对"和"没带凭据"分开了 ——
#    后者才是 401（见 user 模块的 401 用例）。这个区分值得钉住：
#    前端据此决定"跳登录页"还是"提示密码错了"，混成一个就做不到。

LOGIN_FAILURES = [
    ({"email": TEST_USER["email"], "password": "wrong-pwd-xxx"}, "密码错误"),
    ({"email": "nobody_xyz@qq.com", "password": "123456"}, "用户不存在"),
    ({"email": "", "password": "123456"}, "邮箱不能为空"),
]
LOGIN_FAILURE_IDS = ["密码错", "邮箱不存在", "空邮箱"]


@pytest.mark.parametrize("payload, expected_message", LOGIN_FAILURES, ids=LOGIN_FAILURE_IDS)
def test_login_failure_envelope(api, payload, expected_message):
    """失败响应的信封形状 + 业务码 + 文案，**一行**断完。

    老写法要三行：

        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == 400
        assert body["message"] == "密码错误"

    ⭐ 新写法多出来的那部分：`message` 必须是非空字符串（信封契约里有这一条）。
       老写法在这里有个洞 —— 如果后端某天把 message 改成 null，
       `body["message"] == "密码错误"` 会红，但报的是"文案不对"，
       人会去查文案，而真正的问题是**序列化把消息丢了**。
    """
    resp = api.auth.login(payload)

    api.assert_error(resp, 400, expected_message)
