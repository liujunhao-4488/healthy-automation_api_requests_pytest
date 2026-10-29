# test_cases/auth/test_register.py
# 【任务：注册接口 · 数据驱动 + 副作用清理】
#
# 注册和登录最大的不同：**它会往库里写一个新用户**（有副作用）。
#   登录：只读，跑一百遍库都不变。
#   注册：写库，跑一遍就多一个用户。
#
# 所以成功用例**不能写死邮箱**——第一次跑成功，第二次就跑成"邮箱已被注册"了。
# 做法：每次用唯一的 username/email（uuid 后缀），跑完再从库里删掉。
# 一句话：造了数据，自己负责收拾干净。

import uuid

import pytest

from common import db
from common.accounts import ensure_login_seed_account
from common.data_loader import load_cases
from common.schemas import REGISTER_SCHEMA

# 本模块会直接查库/删库（注册后对账、清理），数据库不可用时由根 conftest 跳过。
pytestmark = pytest.mark.requires_db

# 失败场景：每次只有一个字段不合法，期望值全部来自实测（见数据文件注释）。
CASES = load_cases("register_注册_cases.yaml")


@pytest.fixture(scope="module", autouse=True)
def seed_login_account():
    """重复邮箱用例依赖 123456@qq.com 已存在；种子没导时自动补建。"""
    ensure_login_seed_account()


def case_name(case):
    """用数据里的 name 字段当中文用例名。"""
    return case["name"]


@pytest.fixture
def new_user():
    """造一份"库里绝对没有的"注册数据，用例跑完负责把它从库里删掉。

    为什么用 yield 而不是 return？
        return 之后就结束了，没有地方写清理；
        yield 把"清理代码"挂在用例跑完之后——**不管用例成功还是失败都会执行**。
        造数据的 fixture，几乎都长这个样子。
    """
    uniq = "at_" + uuid.uuid4().hex[:10]          # 例：at_3f9c1a2b4d
    data = {
        "username": uniq,
        "password": "123456",
        "email": uniq + "@example.com",
    }
    yield data

    # ---- 以下是清理：用例跑完才轮到这儿 ----
    affected = db.execute("DELETE FROM `user` WHERE email = %s", (data["email"],))
    print(f"\n[清理] 删除注册测试账号 {data['email']}，affected={affected}")


@pytest.mark.parametrize("case", CASES, ids=case_name)
def test_register_fail(api, case):
    """注册失败：8 类非法输入，期望值全部来自数据文件。

    ⚠️ 这里有**一处故意的放宽**，原因写清楚，别当成偷懒：
        一个字段挂了两个约束（如 password 的 @NotBlank + @Size），空值会让两个都失败，
        后端报哪一条由校验器内部顺序决定 —— 实测 15 次里会翻好几次（见数据文件注释）。
        所以这些用例断言 "message 属于候选集合"，而不是死等某一条。
        `want_msg_alt` 就是那个候选集合（可选字段，没写的用例仍然做精确相等）。
    """
    resp = api.auth.register({
        "username": case["username"],
        "password": case["password"],
        "email": case["email"],
    })

    # want_msg_alt 是"候选文案集合"，assert_error 的 message 参数直接吃 list，
    # 所以"属于其中之一"这件事不用在用例里手写 in 了。
    allowed = [case["want_msg"]] + list(case.get("want_msg_alt") or [])
    api.assert_error(resp, case["want_code"], allowed, http=case["want_http"])


def test_register_success(api, new_user):
    """注册成功：返回 200 + token（注册即登录），且用户真的进了库。

    schema=REGISTER_SCHEMA 顺带把**响应形状**也验掉（字段齐不齐、类型对不对）；
    值层面的断言（用户名/邮箱一致、库里真有这条）仍在下面单独写。
    """
    resp = api.auth.register(new_user)
    body = api.assert_ok(resp, "注册应成功", schema=REGISTER_SCHEMA)

    assert body["message"] == "注册成功"

    data = body["data"]
    assert data["token"], "注册成功必须直接返回 token（注册即登录）"
    assert data["username"] == new_user["username"], "返回的用户名应与提交的一致"
    assert data["email"] == new_user["email"], "返回的邮箱应与提交的一致"

    # 不只信响应——去库里核对，确实多了这一条（这是"接口 + DB 双重验证"）
    row = db.query(
        "SELECT id, username, email FROM `user` WHERE email = %s",
        (new_user["email"],), one=True,
    )
    assert row is not None, "注册成功后库里应该有这个用户"
    assert row["username"] == new_user["username"]
