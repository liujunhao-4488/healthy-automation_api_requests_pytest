# test_cases/health/conftest.py
# 本目录（health 模块）专用的夹具。
#
# 为什么不放根 conftest.py？因为它是**health 模块专用**的：
# 只有健康档案/饮食目标的用例才需要"临时靶子账号"。
# 按项目约定，夹具粒度要匹配用例需求 —— 别的模块用不到，就别放公共间里占地方。

import uuid

import pytest

from common import db


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
    yield user

    # ---- 清理：顺序不能反 ----
    # health_info_history 上有外键指向 user(id) 且是 ON DELETE RESTRICT，
    # 直接删 user 会直接炸 IntegrityError(1451)（实测踩过）。
    # 所以：先删"孩子"（history / info / goal），最后删"家长"（user）。
    uid = user["userId"]
    n0 = db.execute("DELETE FROM health_info_history WHERE user_id = %s", (uid,))
    n1 = db.execute("DELETE FROM health_info WHERE user_id = %s", (uid,))
    n2 = db.execute("DELETE FROM diet_goal WHERE user_id = %s", (uid,))
    n3 = db.execute("DELETE FROM `user` WHERE id = %s", (uid,))
    print(f"\n[清理] 靶子 userId={uid}: history={n0} info={n1} goal={n2} user={n3}")
