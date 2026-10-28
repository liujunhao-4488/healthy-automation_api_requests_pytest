# test_cases/health/conftest.py
# 本目录（health 模块）专用的夹具。
#
# 为什么不放根 conftest.py？因为它是**health 模块专用**的：
# 只有健康档案/饮食目标的用例才需要"临时靶子账号"。
# 按项目约定，夹具粒度要匹配用例需求 —— 别的模块用不到，就别放公共间里占地方。

import uuid
from pathlib import Path

import pytest

from common import cleanup

_HERE = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items):
    """health 用例都会直接查库/删库，统一标记为 requires_db。

    ⚠️ conftest 的 hook 会收到**全量** items，必须按路径过滤，
    否则会把别的模块也一起标成 requires_db（实测踩过）。
    """
    for item in items:
        if Path(str(item.fspath)).resolve().parent == _HERE:
            item.add_marker(pytest.mark.requires_db)


@pytest.fixture
def health_user(api):
    """造一个临时靶子账号（带 token），用完连它的健康数据一起删掉。

    为什么必须用靶子，不能用测试账号张三？
      /health/info 和 /health/goal 的 POST 都是 **upsert（会写库）**，
      而且每 POST 一次 /health/info 还会往 health_info_history **追加一条历史**。
      直接在张三身上跑，会把他真实的健康档案和目标是改掉、还会塞一堆历史记录。

    所以：造一个"用完就扔"的账号，它有真实的 userId 和 token，
    用例照样走完整链路，但污染不了任何真实数据。

    yield 之前 = 注册并交出账号；yield 之后 = 清理（无论用例成功还是失败都会执行）。
    """
    uniq = "hx_" + uuid.uuid4().hex[:10]
    data = {"username": uniq, "password": "123456", "email": uniq + "@example.com"}
    body = api.assert_ok(api.auth.register(data), "注册靶子账号应成功")

    user = {
        "userId": body["data"]["userId"],
        "email": data["email"],
        "username": uniq,
        "headers": {"Authorization": "Bearer " + body["data"]["token"]},
    }
    # 登记：万一下面的清理没跑完，会话收尾还能按 userId 再删一次
    cleanup.register_user(user["userId"], user["email"])
    yield user

    # ---- 清理：顺序不能反 ----
    # health_info_history 上有外键指向 user(id) 且是 ON DELETE RESTRICT，
    # 直接删 user 会直接炸 IntegrityError(1451)（实测踩过）。
    # 所以：先删"孩子"（message / history / info / goal / record …），最后删"家长"（user）。
    #
    # 这一整套（含"还剩哪几张子表"的清单）已经沉到 common/cleanup.py 的 purge_user()：
    # 它删完会**回查确认**，删不干净就抛异常，并且只有真删掉了才注销登记表。
    # 原来这里是自己写 4 句 DELETE、不看 affected、最后无条件注销 ——
    # 结果开发库里漏了 65 个 hx_ 账号（后端连开发库时，DELETE 打在测试库上，
    # affected 全是 0，照样"清完了"）。
    cleanup.purge_user(user["userId"])
    print(f"\n[清理] 已回查确认删除靶子账号 userId={user['userId']}")
