# test_cases/health/test_health_契约.py
# 【任务：健康类三个接口的**结构契约**】
#
# ══ 和老文件 test_health_info.py / test_health_goal.py 的分工 ══════════
#   老文件     验「值」：BMI 算得对不对、缺字段报什么、history 有没有追加
#   本文件     验「形状」：字段齐不齐、类型对不对、analysis 挂在哪一层
#
# ══ 写操作怎么做到不留痕 ══════════════════════════════════════════════
#   契约用例不该为了"看一眼响应"而改掉账号数据 —— 主测试账号的档案被改了，
#   AI 助手那批"带画像"的用例会跟着不稳定，排查起来会误判成模型的锅。
#
#   所以这里用的是**原样回写**：先 GET 拿到现状，再把这些值原封不动 POST 回去。
#   实测（2026-10-27 种子库）确认幂等：
#       id 不变、bmi 不变（22.792022792022795）、bmr 不变（1729.1309）
#
#   ⚠️ 唯一残留副作用：每 POST 一次会往 health_info_history 追加一条快照。
#      那条链路由 test_health_info.py::test_save_info_appends_history 负责，
#      它用的是**临时靶子账号**，所以不受这里影响。

import uuid

import pytest

from common import cleanup, db
from common.schemas import (
    HEALTH_GOAL_SCHEMA,
    HEALTH_HISTORY_SCHEMA,
    HEALTH_INFO_EMPTY_SCHEMA,
    HEALTH_INFO_SCHEMA,
)

# 回写时允许带的字段：必填四件套 + 后端认的可选项。
# 只挑**后端接受的**，多塞字段会被 DTO 拒掉，那是造数据的问题不是契约的问题。
INFO_FIELDS = (
    "age", "gender", "height", "weight",
    "activityLevel", "exerciseDuration", "exerciseType",
    "bloodPressure", "bloodSugar", "chronicDiseases",
)

# 建一份"标准档案"用。值本身不重要，合法就行（gender 只能是 male/female）。
STANDARD_PROFILE = {
    "age": 25,
    "gender": "male",
    "height": 175.5,
    "weight": 70.2,
    "activityLevel": "中度",
    "exerciseDuration": 45,
    "exerciseType": "跑步",
}


@pytest.fixture
def health_profile(api, auth_headers):
    """保证主测试账号**已有健康档案**，返回当前的 data。

    ⚠️ 为什么需要这个夹具（2026-10-27 CI 第一次跑暴露的）：
      下面几条用例验的是"已建档"时的形状，但它们默认主账号一定建过档。
      本地确实如此（跑了很多轮，档案早就有了），可 CI 每次用干净库重建，
      账号只有 user 行、没有 health_info 行 → GET 返回 data=null → 三条集体红。

      不是断言写错了，是**用例依赖了一个从没被写下来的前提**。
      现在 seed_test.sql 已显式种了主账号档案；这个夹具保留作兜底：
      只导表没导种子时，缺档就补一份标准的，已有就原样用（幂等）。
    """
    body = api.assert_ok(api.health.get_info(headers=auth_headers), "读取健康档案应成功")

    if body["data"] is None:
        api.assert_ok(
            api.health.save_info(STANDARD_PROFILE, headers=auth_headers),
            "主账号没建档，补一份标准档案应成功",
        )
        body = api.assert_ok(api.health.get_info(headers=auth_headers), "补齐后重读应成功")

    assert body["data"] is not None, "补建档之后 data 仍是 null —— upsert 没生效"
    return body["data"]



# ==================== 健康档案 ====================

def test_get_info_shape(api, auth_headers, health_profile):
    """GET /health/info → 信封 + data 16 个字段 + 顶层 analysis 的 13 个字段。

    这个接口的形状最值得盯，因为有两处特别容易踩：
      ① analysis 在**信封顶层**（body.analysis），不在 data 里；
      ② bmr / bloodSugar 这一类是**可能为 null** 的（没填就不会算）。
    两者写错，契约用例会在"功能完全正常"的时候红 —— 那种红最容易被当成测试不准。
    """
    resp = api.health.get_info(headers=auth_headers)

    api.assert_ok(resp, "获取健康档案应成功", schema=HEALTH_INFO_SCHEMA)


def test_get_info_without_profile_returns_null_data(api):
    """**没建过档**时是另一套形状：data 是 null，analysis 只给 4 个字段。

    这条是 CI 第一次跑帮我发现的 —— 本地永远看不到这个分支，
    因为本地主账号早建过档了。用临时账号（用完就删）造出真·未建档状态，
    比 mock 一个响应可信：它证明的是后端的真实行为，不是我编的。
    """
    uniq = "np_" + uuid.uuid4().hex[:10]
    data = {"username": uniq, "password": "123456", "email": uniq + "@example.com"}
    reg = api.assert_ok(api.auth.register(data), "注册探针账号应成功")
    headers = {"Authorization": "Bearer " + reg["data"]["token"]}
    cleanup.register_user(reg["data"]["userId"], data["email"])

    try:
        resp = api.health.get_info(headers=headers)
        # 注意：未建档不是 404，是 200 + data:null —— 这点容易想当然
        api.assert_ok(resp, "未建档时读取也应成功", schema=HEALTH_INFO_EMPTY_SCHEMA)
    finally:
        db.execute("DELETE FROM `user` WHERE email = %s", (data["email"],))
        cleanup.unregister_user(reg["data"]["userId"])


def test_get_info_analysis_is_not_empty(api, auth_headers, health_profile):
    """analysis 里的字段是**字符串**还不够 —— 它不该是空串。

    形状对了但内容空，前端显示一块空白区域，看起来像"后端没算"。
    这一步 schema 管不了（schema 只管类型），要单独断。
    """
    body = api.assert_ok(api.health.get_info(headers=auth_headers), "获取健康档案应成功")

    analysis = body["analysis"]
    for field in ("summary", "bmiCategory", "overallLevel"):
        assert analysis[field].strip(), f"analysis.{field} 是空串，等于没给结论"


def test_save_info_returns_same_shape(api, auth_headers, health_profile):
    """POST /health/info 返回的 data 和 GET 是**同一套字段**。

    为什么要单测：写接口很容易只回传"刚提交的那几个字段"，
    前端拿去做局部刷新时其它字段就变 undefined。同一份契约要管住两个出口。

    ⚠️ 原样回写（GET 拿到的值直接 POST 回去），不留痕 —— 见文件头说明。
    """
    current = health_profile

    payload = {k: current[k] for k in INFO_FIELDS if current.get(k) is not None}
    resp = api.health.save_info(payload, headers=auth_headers)

    body = api.assert_ok(resp, "保存健康档案应成功", schema=HEALTH_INFO_SCHEMA)

    assert body["data"]["id"] == current["id"], "upsert 不该插出第二条记录"


def test_save_info_missing_field_says_which_field(api, auth_headers):
    """缺必填字段 → 400，且文案**点出缺的是哪一个**。

    这条同时是 assert_error 的实战样板：三行变一行。
    """
    resp = api.health.save_info(
        {"gender": "male", "height": 175.5, "weight": 70.2},   # 故意不给 age
        headers=auth_headers,
    )

    api.assert_error(resp, 400, "年龄不能为空")


def test_save_info_gender_enum_is_strict(api, auth_headers):
    """gender 传中文"男"是 400 —— 枚举只有 male / female。

    这个坑我是真踩的：一开始按"人话"传"男"，接口 400，还以为是缺字段。
    实测文案：「性别取值不合法，只能是 male 或 female」。
    """
    resp = api.health.save_info(
        {"age": 25, "gender": "男", "height": 175.5, "weight": 70.2},
        headers=auth_headers,
    )

    api.assert_error(resp, 400, "性别取值不合法，只能是 male 或 female")


# ==================== 饮食目标 ====================

def test_get_goal_shape(api, auth_headers):
    """GET /health/goal → 18 个字段。

    里面那 8 个（targetWeight / proteinRatio / proteinTarget …）是后端**算**出来的：
    刚 POST 完是 null，GET 时才有值。所以 schema 里一律允许 null。
    """
    resp = api.health.get_goal(headers=auth_headers)

    api.assert_ok(resp, "获取饮食目标应成功", schema=HEALTH_GOAL_SCHEMA)


def test_save_goal_missing_calories(api, auth_headers):
    """只有 goalType 没有卡路里 → 400「目标卡路里不能为空」。

    ⚠️ 实测一个小坑：三个必填字段里**只给 goalType** 时，后端先报的是
       「开始日期不能为空」，不是卡路里 —— 校验顺序是"类型 → 日期 → 卡路里"。
       所以这条必须把 startDate 一起给上，才能真正测到卡路里那条。
       （这种"报错顺序"不看实测是猜不出来的）
    """
    resp = api.health.save_goal(
        {"goalType": "减脂", "startDate": "2026-10-26"},
        headers=auth_headers,
    )

    api.assert_error(resp, 400, "目标卡路里不能为空")


# ==================== 历史记录 ====================

def test_get_history_shape(api, auth_headers):
    """GET /health/history → 数组，每个元素 7 个字段。

    ⚠️ 这里是 schema 的**能力边界**，说清楚免得误会：
       历史为空时 data 是 []，jsonschema 没元素可验，照样通过。
       "必须有记录"要靠用例自己断 len()，schema 永远不会替你断这个。
    """
    resp = api.health.get_history(headers=auth_headers)

    body = api.assert_ok(resp, "获取历史记录应成功", schema=HEALTH_HISTORY_SCHEMA)

    # schema 管不到的那一半，在这里补上
    assert isinstance(body["data"], list), "history 的 data 应该是数组"
    for item in body["data"]:
        assert item["recordDate"].strip(), "历史记录的日期不该是空串"


# ==================== 鉴权：三个接口同一个口径 ====================

def test_health_endpoints_reject_without_token(api):
    """三个接口不带 token → 都是 401 + **空响应体**（实测）。

    401 不给信封（没有 code / message）—— 这是全站一致的约定。
    所以断言只能写 `http=401` 且不带文案，硬拿信封去套就会红，
    而那个红是判据用错了，不是系统坏了。
    """
    for resp in (
        api.health.get_info(),
        api.health.get_goal(),
        api.health.get_history(),
    ):
        api.assert_error(resp, 401, http=401)
