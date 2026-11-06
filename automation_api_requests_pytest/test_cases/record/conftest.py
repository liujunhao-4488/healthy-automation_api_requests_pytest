# test_cases/record/conftest.py
# 饮食记录模块的专用夹具。
#
# ============ 这个模块为什么值得单独写 conftest ============
# /record/submit 是**唯一能让"我吃了什么"进库的入口**，而它连带写两张表
# （diet_record + diet_record_detail）。所有下游功能 —— 摄入趋势、饮食建议、
# AI 助手的"今天吃了多少" —— 都建立在这张表上。
# 所以这里造的数据必须**和真实用户造的一样**：走接口提交，不直插库。
# 直插库只能证明"库里的数据能读出来"，证明不了"接口能把数据写对"。
#
# ============ 和 recipe 模块的区别 ============
# recipe 那边的靶子食谱是直插库的，因为 recipe 表在测试库是空的、
# 且它是"别人给的素材"。record 不一样：记录是**用户自己产生的数据**，
# 走接口才能测到"提交时后端有没有算对总量、日期有没有解析对"。

import uuid
from pathlib import Path

import pytest

from common import cleanup

_HERE = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items):
    """本目录用例都会注册/删除临时账号，统一标 requires_db。

    ⚠️ 必须按路径过滤：conftest 的 hook 收到的是全量 items（实测踩过，
       不过滤会把整个项目的用例都标上 requires_db）。
    """
    for item in items:
        if Path(str(item.fspath)).resolve().parent == _HERE:
            item.add_marker(pytest.mark.requires_db)


def _register(api, prefix):
    """注册一次性账号，返回 userId / email / 带 token 的请求头。"""
    uniq = prefix + uuid.uuid4().hex[:10]
    email = uniq + "@example.com"
    reg = api.assert_ok(
        api.auth.register({"username": uniq, "password": "123456", "email": email}),
        f"注册 {prefix} 账号应成功",
    )
    return {
        "userId": reg["data"]["userId"],
        "email": email,
        "headers": {"Authorization": "Bearer " + reg["data"]["token"]},
    }


def _payload(date="2026-11-06", meal_type="breakfast", notes="夹具造的一餐",
             details=None):
    """拼一条提交用的请求体。

    details 默认给一条燕麦 50g / 194 kcal —— 数字取自 API.md 7.1 的示例，
    这样断言里的期望值有出处，不是随手编的。
    """
    if details is None:
        details = [{"foodName": "燕麦", "amount": 50, "unit": "g",
                    "calories": 194, "protein": 6.6, "carbs": 33.5, "fat": 3.1}]
    return {"date": date, "mealType": meal_type, "notes": notes, "details": details}


@pytest.fixture
def record_user(api):
    """一个临时账号，用完连它提交的记录一起删。

    ⚠️ 为什么不复用主测试账号张三：
       /record/list 返回的是**这个人的全部记录**，而张三名下有历史数据，
       "提交一条之后列表应该有 1 条"这种断言会直接崩。
       而且 delete 用例会真的删数据（软删），删到张三头上的账没法算。
    """
    user = _register(api, "rcd_")
    cleanup.register_user(user["userId"], user["email"])
    yield user
    cleanup.purge_user(user["userId"])


@pytest.fixture
def record_pair(api):
    """两个临时账号，专供越权（IDOR）用例。

    单账号测不了越权：`/record/detail/{id}` 和 `DELETE /record/{id}` 的入参
    只有 id，要证明"后端按 token 判归属"，必须有一个**真实的另一个登录身份**
    拿着别人的 id 去试。用不存在的 id 是无效样本 —— 后端在查库前就拒了，
    归属判断那行代码根本没跑到。
    """
    owner = _register(api, "rcdo_")
    intruder = _register(api, "rcdi_")
    for u in (owner, intruder):
        cleanup.register_user(u["userId"], u["email"])

    yield {"owner": owner, "intruder": intruder}

    for u in (owner, intruder):
        cleanup.purge_user(u["userId"])


@pytest.fixture
def submit_record(api):
    """提交一条饮食记录，返回它的 id。

    用法：

        rid = submit_record(record_user)                        # 默认那条燕麦
        rid = submit_record(record_user, meal_type="lunch")     # 换餐次
        rid = submit_record(record_user, details=[...])         # 换明细

    把它做成夹具而不是每个用例自己拼 8 行 JSON，是为了让用例里
    **一眼能看出"这条测的是提交还是查询"**，而不是淹没在请求体里。
    """
    def _submit(who, **overrides):
        body = api.assert_ok(
            api.record.submit(_payload(**overrides), headers=who["headers"]),
            f"用户 {who['userId']} 提交饮食记录应成功",
        )
        return body["data"]["id"]

    return _submit
