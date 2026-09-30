import time

import pytest

from common.db import execute


CASES=[
    ("空邮箱",""),
    ("空格"," "),
    ("非法邮箱","123456#qq.com"),
    ("超长","a" * 300 + "@qq.com"),
]
@pytest.mark.parametrize("case_name,email",CASES,ids=[c[0] for c in CASES])
def test_register_fail(api, case_name, email):
    resp=api.post("/auth/register",json={"username":case_name,"email":email,"password":"123456","phone":"17888888888"})
    assert resp.status_code==400


# ============================================================
# 成功路径（2026-09-28 补）
# ------------------------------------------------------------
# 上面 4 条测的是"它拒绝什么"，下面测"它接受什么"。
# 只测拒绝、不测接受 = 只测了半个圆：
# 万一合法输入也被拒，上面 4 条照样全绿，什么都不会告诉你。
# ============================================================


@pytest.fixture
def new_user():
    """造一份"唯一的"注册信息，并在用例跑完后把它从库里删掉。

    ── 为什么邮箱和用户名都要带时间戳？ ──
    user 表上 username 和 email 都有唯一索引。写死固定值的话：
        第一次跑 → 注册成功
        第二次跑 → "邮箱已被注册" → 测试红
    测试必须能反复跑，所以每次生成不一样的值。
    ⚠️ 只给 email 加时间戳还不够 —— username 也有唯一索引，两个都得随。

    ── 为什么用 yield 夹具做清理，而不是写在用例最后一行？ ──
        yield 之前 = 准备（造数据）
        yield 之后 = 收尾（删数据）
      pytest 保证收尾一定执行 —— 就算用例断言挂在中途也会跑到。
      写成"用例最后一行删数据"的话，用例一挂就永远执行不到，
      库里会留下垃圾用户，跑一百次积一百个。
    """
    stamp = int(time.time() * 1000)          # 毫秒时间戳：每次运行都不同
    user = {
        "username": f"tmp_register_{stamp}",
        "email": f"tmp_register_{stamp}@qq.com",
        "password": "123456",
        "phone": "17888888888",
    }

    yield user                                # ← 把这份数据交给用例

    # ↓ 收尾：删掉这次造的临时用户
    # 用固定前缀 tmp_ 是为了好认：一眼看出哪些行是测试造的。
    # 删 0 行也不会报错（比如注册压根没成功），所以这行是安全的。
    execute("delete from `user` where email = %s", (user["email"],))


def test_register_success(api, new_user):
    """合法输入 → 注册成功，且响应里直接带回 token（注册即登录）。

    这条是"期望成功"的用例，所以可以用 api.assert_ok ——
    它一次搞定"HTTP==200 + 业务 code==200"，并把 body 返回给你。
    """
    resp = api.post("/auth/register", json=new_user)
    body = api.assert_ok(resp)

    data = body["data"]
    assert data["email"] == new_user["email"]        # 回显的是我刚传的邮箱
    assert data["username"] == new_user["username"]  # 回显的是我刚传的用户名
    assert data["role"] == "user"                    # 新用户默认是普通角色
    assert data["userId"]                            # 分配到了 id
    assert data["token"]                             # 注册即登录：直接给了 token


def test_register_then_login(api, new_user):
    """闭环验证：注册完立刻用同一套账号密码登录，能拿到 token。

    为什么不只断言"注册返回 200"？
      接口完全可能"嘴上说成功、实际没落库"。要证明账号真的可用，
      最直接的方式就是拿它去登录一次 —— 这是"写读回环"。

    （这条的断言我还没实测过，跑一遍确认；不对就把实际响应贴给我。）
    """
    api.assert_ok(api.post("/auth/register", json=new_user))

    login = api.assert_ok(api.post("/auth/login", json={
        "email": new_user["email"],
        "password": new_user["password"],
    }))
    assert login["data"]["token"]
