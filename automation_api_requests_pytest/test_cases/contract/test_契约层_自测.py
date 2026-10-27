# test_cases/contract/test_契约层_自测.py
# 【任务：测「测别人的东西」本身对不对】
#
# 这一份是"测试的测试"：不给它任何服务，全是手写的假响应，1 秒跑完。
#
# 为什么必须有这一份 —— 两个理由：
#   ① 契约层如果自己有 bug（该红的没红），后面所有接口用例都会**假绿**，
#      而且看不出假绿。这是唯一能提前发现的办法。
#   ② 报错文案要能直接定位问题。所以每条"该报错"的用例，
#      不只断言"抛错了"，还要断言"报错里点到了对的字段"。
#      只断言"抛了 AssertionError"的话，判据写歪也能过。
#
# ⚠️ 这里的数据是从真实响应抄来的（2026-10-26 实测 8080），
#    和 test_cases/{auth,user,health,assistant} 里的契约用例是同一套事实。

import pytest

from common.schemas import (
    ANALYSIS,
    CHAT_SCHEMA,
    HEALTH_GOAL_SCHEMA,
    HEALTH_INFO_SCHEMA,
    LOGIN_SCHEMA,
    PROFILE_SCHEMA,
    check,
    nullable,
    ok,
)


# ==================== 一、check() 这个工具本身 ====================

def test_check_passes_on_conforming_data():
    """符合说明书 → 什么都不发生，原样返回数据。"""
    schema = {"type": "object", "required": ["a"], "properties": {"a": {"type": "integer"}}}
    data = {"a": 1}
    assert check(data, schema) == data


def test_missing_field_is_reported_with_field_name():
    """缺必填字段 → 报错里必须点出**缺的是哪个**。"""
    schema = {"type": "object", "required": ["a", "b"], "properties": {"a": {"type": "integer"}}}

    with pytest.raises(AssertionError) as exc:
        check({"a": 1}, schema)

    message = str(exc.value)
    assert "缺少必填字段 b" in message, f"应点名字段 b：{message}"


def test_wrong_type_is_reported_with_expected_and_actual():
    """类型不对 → 报错里要有"期望什么、实际什么"，否则没法判断该改哪边。"""
    schema = {"type": "object", "properties": {"userId": {"type": "integer"}}}

    with pytest.raises(AssertionError) as exc:
        check({"userId": "1"}, schema)

    message = str(exc.value)
    assert "期望 integer" in message or "应为 integer" in message, message
    assert "str" in message, f"应说明实际是 str：{message}"


def test_enum_violation_is_reported():
    """枚举越界 → 这是"字段在、类型也对、但值不合法"的情况，最容易漏。"""
    schema = {"type": "object", "properties": {"role": {"enum": ["user", "admin"]}}}

    with pytest.raises(AssertionError) as exc:
        check({"role": "superadmin"}, schema)

    assert "superadmin" in str(exc.value)


def test_all_problems_are_listed_at_once():
    """一次列全，不是发现第一个就停 —— 后端换 DTO 时通常是整批一起漂。"""
    schema = {
        "type": "object",
        "required": ["a", "b", "c"],
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
    }

    with pytest.raises(AssertionError) as exc:
        check({"a": "x"}, schema)

    message = str(exc.value)
    assert "3 处" in message, f"三处问题（a 类型错、b/c 缺失）应一次列全：{message}"


def test_error_path_points_at_the_field():
    """报错要给**完整路径**：body.data.userId，而不是光一个 userId。

    没有路径的话，深层嵌套里同名字段（比如到处都是 id）根本分不清。
    """
    schema = ok({"type": "object", "properties": {"userId": {"type": "integer"}}})

    with pytest.raises(AssertionError) as exc:
        check({"code": 200, "message": "ok", "data": {"userId": "1"}}, schema)

    assert "body.data.userId" in str(exc.value), str(exc.value)


def test_boolean_is_not_accepted_as_integer():
    """True 不能被当成 1 —— Python 里 bool 是 int 的子类，这是个经典坑。

    jsonschema 自己处理了这条，这里钉住它，防止将来换校验库时丢掉。
    """
    schema = {"type": "object", "properties": {"status": {"type": "integer"}}}

    with pytest.raises(AssertionError):
        check({"status": True}, schema)


# ==================== 二、nullable / ok 两个小工具 ====================

def test_nullable_accepts_both_null_and_real_value():
    """nullable = "可以是 null，也可以是真正值"。

    用处：/health/info 没建档时 data 是 null，建档后是对象 —— 两种都合法。
    """
    schema = nullable({
        "type": "object",
        "required": ["id"],
        "properties": {"id": {"type": "integer"}},
    })
    check(None, schema)
    check({"id": 1}, schema)

    with pytest.raises(AssertionError):
        check({"id": "1"}, schema)     # 是对象，但类型错 → 照样红


def test_ok_makes_data_required():
    """ok() 拼出来的信封里，data 是**必填**的。

    这条防的是"后端某天不返回 data 了" —— 前端会直接白屏。
    """
    schema = ok({"type": "object"})

    with pytest.raises(AssertionError) as exc:
        check({"code": 200, "message": "ok"}, schema)

    assert "缺少必填字段 data" in str(exc.value)


def test_ok_puts_extra_fields_on_top_level():
    """/health/info 的 analysis 在信封**顶层**（body.analysis），不在 data 里。

    ok(data, analysis=...) 就是为这个场景写的。写错位置的话，
    真实用例会在"缺 analysis"上报红 —— 这里先自证一下。
    """
    schema = ok({"type": "object"}, analysis=ANALYSIS)
    assert "analysis" in schema["required"]
    assert "analysis" not in schema["properties"]["data"].get("properties", {})


# ==================== 三、四份真实 schema 的假数据快照 ====================
# 下面这些样本全部照实测响应抄的，字段名、类型、null 位置一个没动。
# 用处：接口用例红了的时候，先跑这一份 ——
#   这里绿 = 服务端真的变了；这里红 = schema 自己写歪了。

LOGIN_BODY = {
    "code": 200,
    "message": "登录成功",
    "data": {
        "userId": 2,
        "username": "测试账号",
        "email": "a@b.com",
        "phone": "13800000000",
        "avatar": None,
        "role": "user",
        "token": "eyJhbGciOi...",
    },
}

PROFILE_BODY = {
    "code": 200,
    "message": "操作成功",
    "data": {
        "userId": 2,
        "username": "测试账号",
        "email": "a@b.com",
        "phone": None,
        "avatar": None,
        "role": "user",
        "status": 1,
        "createTime": "2026-10-01T10:00:00",
        "updateTime": "2026-10-26T17:00:00",
    },
}

# 刚建档那一刻：bmr 等字段还是 null，POST 之后才算出来
HEALTH_INFO_BODY_FRESH = {
    "code": 200,
    "message": "保存成功",
    "data": {
        "id": 9, "userId": 2, "age": 25, "gender": "male",
        "height": 175.5, "weight": 70.2, "bmi": 22.79, "bmr": None,
        "bloodPressure": None, "bloodSugar": None, "activityLevel": None,
        "exerciseDuration": None, "exerciseType": None, "chronicDiseases": None,
        "createTime": "2026-10-26T17:00:00", "updateTime": "2026-10-26T17:00:00",
    },
    "analysis": {
        "summary": "整体状况良好", "bmiAdvice": "保持", "bmiCategory": "正常",
        "bloodPressureAdvice": "未填写", "bloodPressureStatus": "未填写",
        "bloodSugarAdvice": "未填写", "bloodSugarStatus": "未填写",
        "activityAdvice": "未填写", "activityStatus": "未填写",
        "overallLevel": "良好", "goalInsight": "暂无目标",
        "recommendations": ["多喝水"], "tags": ["正常体重"],
    },
}


def test_login_schema_accepts_real_sample():
    check(LOGIN_BODY, LOGIN_SCHEMA, label="登录")


def test_login_schema_catches_missing_token():
    """token 是登录响应的**核心交付物**，少了它前端根本没法继续。

    老用例 `assert "token" in body["data"]` 能抓到这一条；
    所以这里必须验证 schema 也抓得到 —— 别让新写法比旧的还弱。
    """
    broken = {**LOGIN_BODY, "data": {k: v for k, v in LOGIN_BODY["data"].items() if k != "token"}}

    with pytest.raises(AssertionError) as exc:
        check(broken, LOGIN_SCHEMA, label="登录")

    assert "缺少必填字段 token" in str(exc.value)


def test_login_schema_catches_role_enum_violation():
    """role 冒出第三个值 → 权限模型变了，必须红。"""
    broken = {**LOGIN_BODY, "data": dict(LOGIN_BODY["data"], role="superadmin")}

    with pytest.raises(AssertionError):
        check(broken, LOGIN_SCHEMA)


def test_login_and_profile_are_different_shapes():
    """login 的 data ≠ profile 的 data（实测结论，最容易想当然的地方）。

    login 有 token 没有 status/createTime，
    profile 有 status/createTime 没有 token。
    共用一份 schema 的话，两边必有一边红 —— 这条钉住"它们是两回事"。
    """
    check(PROFILE_BODY, PROFILE_SCHEMA, label="资料")

    with pytest.raises(AssertionError):
        check(PROFILE_BODY, LOGIN_SCHEMA, label="资料当成登录")   # 缺 token

    with pytest.raises(AssertionError):
        check(LOGIN_BODY, PROFILE_SCHEMA, label="登录当成资料")   # 缺 status


def test_profile_schema_catches_status_type_drift():
    """status 从 1 变成 "1" → 前端 `status === 1` 会静默失效，页面就当没禁用。

    这是"能正常显示、但行为错了"的典型，靠肉眼和只断 code 都发现不了。
    """
    broken = {**PROFILE_BODY, "data": dict(PROFILE_BODY["data"], status="1")}

    with pytest.raises(AssertionError) as exc:
        check(broken, PROFILE_SCHEMA)

    assert "status" in str(exc.value)


def test_health_info_accepts_fresh_record_with_null_optional_fields():
    """刚建档时 bmr / bloodPressure 都是 null，schema 必须认。

    写死成 `{"type": "number"}` 的话，这条会红 —— 而且是在"功能正常"的时候红，
    那种红最伤人，会被当成测试不准。
    """
    check(HEALTH_INFO_BODY_FRESH, HEALTH_INFO_SCHEMA, label="健康档案")


def test_health_info_requires_analysis_on_envelope_top():
    """analysis 必须挂在信封顶层；挪进 data 里就要红。"""
    broken = dict(HEALTH_INFO_BODY_FRESH)
    broken.pop("analysis")

    with pytest.raises(AssertionError) as exc:
        check(broken, HEALTH_INFO_SCHEMA, label="健康档案")

    assert "缺少必填字段 analysis" in str(exc.value)


def test_health_goal_accepts_not_yet_computed_fields():
    """刚 POST 完，targetWeight / proteinTarget 这一批还是 null。

    它们由后端**算**出来，GET 时才填上 —— 所以一律允许 null。
    """
    body = {
        "code": 200,
        "message": "保存成功",
        "data": {
            "id": 3, "userId": 2, "goalType": "减脂", "targetWeight": None,
            "targetCalories": 1800.0, "proteinRatio": None, "carbsRatio": None,
            "fatRatio": None, "proteinTarget": None, "carbsTarget": None,
            "fatTarget": None, "waterTarget": None, "status": None,
            "startDate": "2026-10-26", "endDate": None, "reminderEnabled": None,
            "reminderTime": None,
            "createTime": "2026-10-26T17:00:00", "updateTime": "2026-10-26T17:00:00",
        },
    }
    check(body, HEALTH_GOAL_SCHEMA, label="饮食目标")


CHAT_BODY = {
    "code": 200,
    "message": "成功",
    "data": {
        "conversationId": 12,
        "userMessage": {
            "id": 31, "role": "user", "text": "每天喝多少水", "messageType": "text",
            "cards": [], "createTime": "2026-10-26T17:00:00",
        },
        "assistantMessage": {
            "id": 32, "role": "assistant", "text": "建议 1500-1700ml。",
            "messageType": "text", "cards": [], "createTime": "2026-10-26T17:00:01",
            "source": "model", "intent": "advice", "ragUsed": False,
            "retrievalStatus": "none", "sources": [],
        },
        "conversation": {
            "id": 12, "title": "喝水", "summary": "", "messageCount": 2,
            "lastMessageAt": "2026-10-26T17:00:01",
            "createTime": "2026-10-26T17:00:00", "updateTime": "2026-10-26T17:00:01",
        },
        "contextMessage": None,
    },
}


def test_chat_schema_accepts_real_sample():
    check(CHAT_BODY, CHAT_SCHEMA, label="聊天")


def test_chat_schema_catches_rag_flag_type_drift():
    """ragUsed 从 false 变成 "false" —— 字符串 "false" 是**真值**！

    前端 `if (ragUsed)` 会把"没用知识库"当成"用了"，标出假的引用来源。
    这类坑只有校验类型才抓得到。
    """
    broken = {
        **CHAT_BODY,
        "data": dict(
            CHAT_BODY["data"],
            assistantMessage=dict(CHAT_BODY["data"]["assistantMessage"], ragUsed="false"),
        ),
    }

    with pytest.raises(AssertionError) as exc:
        check(broken, CHAT_SCHEMA, label="聊天")

    assert "ragUsed" in str(exc.value)


def test_user_message_must_not_have_assistant_only_fields():
    """反向约束的边界说明：schema **不禁止**多字段（向后兼容）。

    这条不是漏写，是有意的。所以这里断言"多字段仍然通过"，
    免得将来有人把 additionalProperties: False 加上，
    然后每条用例都在"后端加了字段"上红。
    """
    extra = {**CHAT_BODY["data"]["userMessage"], "intent": "advice"}
    body = {**CHAT_BODY, "data": dict(CHAT_BODY["data"], userMessage=extra)}

    check(body, CHAT_SCHEMA, label="聊天")


# ==================== 四、assert_error 这把尺子本身 ====================
# 为什么连这个也要测：迁移的 38 条失败用例现在全靠它判定。
# 如果它悄悄变弱（比如把"精确相等"写成"包含"），那 38 条会集体假绿，
# 而且从报告上看是"全过"，没有任何信号。
#
# 尤其是 test_exact_match_is_not_weakened 那一条 —— 它防的就是"迁移过程中
# 断言强度被悄悄放松"，这是所有重构里最容易发生、最难发现的退化。

import json

from api.base_api_client import BaseApiClient


class FakeResp:
    """假的 requests.Response，只实现 assert_error 用到的三样东西。

    不用真发请求：这些测试验的是"判据逻辑"，跟网络无关。
    """

    def __init__(self, status_code, payload=None, raw_text=None):
        self.status_code = status_code
        if raw_text is not None:
            self.text = raw_text
        else:
            self.text = json.dumps(payload, ensure_ascii=False) if payload is not None else ""
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("响应体不是 JSON")
        return self._payload


def err_body(code, message):
    return {"code": code, "message": message}


def test_assert_error_passes_on_exact_match():
    resp = FakeResp(400, err_body(400, "手机号格式不正确"))
    body = BaseApiClient.assert_error(resp, 400, "手机号格式不正确")
    assert body["code"] == 400, "应该把 body 返回出来，方便后续断言"


def test_assert_error_catches_wrong_http_status():
    resp = FakeResp(500, err_body(400, "手机号格式不正确"))

    with pytest.raises(AssertionError) as exc:
        BaseApiClient.assert_error(resp, 400, "手机号格式不正确")

    assert "HTTP 实际 500" in str(exc.value)


def test_assert_error_catches_wrong_business_code():
    """HTTP 对了但业务 code 不对 —— 这两个是独立维度，不能只验一个。"""
    resp = FakeResp(400, err_body(500, "手机号格式不正确"))

    with pytest.raises(AssertionError) as exc:
        BaseApiClient.assert_error(resp, 400, "手机号格式不正确")

    assert "业务 code 不符" in str(exc.value)


def test_assert_error_catches_wrong_message():
    resp = FakeResp(400, err_body(400, "用户名格式不正确"))

    with pytest.raises(AssertionError) as exc:
        BaseApiClient.assert_error(resp, 400, "手机号格式不正确")

    assert "错误文案不符" in str(exc.value)


def test_exact_match_is_not_weakened():
    """⚠️ 这条是整套迁移的**守门员**。

    老代码用的是 `body["message"] == case["want_msg"]`（精确相等）。
    迁移时如果图省事改成"包含"，下面这句更长的文案就会被放过 ——
    断言强度悄悄降了一档，而报告上什么都不会显示。

    所以：默认必须精确相等；要"包含"必须显式写 contains=True。
    """
    longer = FakeResp(400, err_body(400, "手机号格式不正确，请重新填写"))

    with pytest.raises(AssertionError):
        BaseApiClient.assert_error(longer, 400, "手机号格式不正确")

    # 显式要求"包含"时才放过 —— 这是有意的放松，看得见
    BaseApiClient.assert_error(longer, 400, "手机号格式不正确", contains=True)


def test_assert_error_accepts_candidate_messages():
    """候选文案集合：一个字段挂两个约束时，后端报哪条由校验器顺序决定。"""
    resp = FakeResp(400, err_body(400, "密码不能为空"))

    BaseApiClient.assert_error(resp, 400, ["密码不能为空", "密码长度需在 6 到 20 个字符之间"])

    with pytest.raises(AssertionError):
        BaseApiClient.assert_error(resp, 400, ["另一个文案", "再一个文案"])


def test_assert_error_handles_empty_body_for_401():
    """401 是**空响应体**（实测），不是 JSON 信封。

    这时只能验 HTTP 状态。传了文案反而要报错 —— 因为"没有 message 却要求比对"
    说明用例写错了，让它红出来比默默放过好。
    """
    empty = FakeResp(401, raw_text="")

    assert BaseApiClient.assert_error(empty, 401, http=401) is None

    with pytest.raises(AssertionError) as exc:
        BaseApiClient.assert_error(empty, 401, "未登录", http=401)

    assert "响应体是空的" in str(exc.value)


# ==================== 四、assert_error 这把尺子本身 ====================
# 为什么连这个也要测：迁移的 38 条失败用例现在全靠它判定。
# 如果它悄悄变弱（比如把"精确相等"写成"包含"），那 38 条会集体假绿，
# 而且从报告上看是"全过"，没有任何信号。
#
# 尤其是 test_exact_match_is_not_weakened 那一条 —— 它防的就是"迁移过程中
# 断言强度被悄悄放松"，这是所有重构里最容易发生、最难发现的退化。

import json

from api.base_api_client import BaseApiClient


class FakeResp:
    """假的 requests.Response，只实现 assert_error 用到的三样东西。

    不用真发请求：这些测试验的是"判据逻辑"，跟网络无关。
    """

    def __init__(self, status_code, payload=None, raw_text=None):
        self.status_code = status_code
        if raw_text is not None:
            self.text = raw_text
        else:
            self.text = json.dumps(payload, ensure_ascii=False) if payload is not None else ""
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("响应体不是 JSON")
        return self._payload


def err_body(code, message):
    return {"code": code, "message": message}


def test_assert_error_passes_on_exact_match():
    resp = FakeResp(400, err_body(400, "手机号格式不正确"))
    body = BaseApiClient.assert_error(resp, 400, "手机号格式不正确")
    assert body["code"] == 400, "应该把 body 返回出来，方便后续断言"


def test_assert_error_catches_wrong_http_status():
    resp = FakeResp(500, err_body(400, "手机号格式不正确"))

    with pytest.raises(AssertionError) as exc:
        BaseApiClient.assert_error(resp, 400, "手机号格式不正确")

    assert "HTTP 实际 500" in str(exc.value)


def test_assert_error_catches_wrong_business_code():
    """HTTP 对了但业务 code 不对 —— 这两个是独立维度，不能只验一个。"""
    resp = FakeResp(400, err_body(500, "手机号格式不正确"))

    with pytest.raises(AssertionError) as exc:
        BaseApiClient.assert_error(resp, 400, "手机号格式不正确")

    assert "业务 code 不符" in str(exc.value)


def test_assert_error_catches_wrong_message():
    resp = FakeResp(400, err_body(400, "用户名格式不正确"))

    with pytest.raises(AssertionError) as exc:
        BaseApiClient.assert_error(resp, 400, "手机号格式不正确")

    assert "错误文案不符" in str(exc.value)


def test_exact_match_is_not_weakened():
    """⚠️ 这条是整套迁移的**守门员**。

    老代码用的是 `body["message"] == case["want_msg"]`（精确相等）。
    迁移时如果图省事改成"包含"，下面这句更长的文案就会被放过 ——
    断言强度悄悄降了一档，而报告上什么都不会显示。

    所以：默认必须精确相等；要"包含"必须显式写 contains=True。
    """
    longer = FakeResp(400, err_body(400, "手机号格式不正确，请重新填写"))

    with pytest.raises(AssertionError):
        BaseApiClient.assert_error(longer, 400, "手机号格式不正确")

    # 显式要求"包含"时才放过 —— 这是有意的放松，看得见
    BaseApiClient.assert_error(longer, 400, "手机号格式不正确", contains=True)


def test_assert_error_accepts_candidate_messages():
    """候选文案集合：一个字段挂两个约束时，后端报哪条由校验器顺序决定。"""
    resp = FakeResp(400, err_body(400, "密码不能为空"))

    BaseApiClient.assert_error(resp, 400, ["密码不能为空", "密码长度需在 6 到 20 个字符之间"])

    with pytest.raises(AssertionError):
        BaseApiClient.assert_error(resp, 400, ["另一个文案", "再一个文案"])


def test_assert_error_handles_empty_body_for_401():
    """401 是**空响应体**（实测），不是 JSON 信封。

    这时只能验 HTTP 状态。传了文案反而要报错 —— 因为"没有 message 却要求比对"
    说明用例写错了，让它红出来比默默放过好。
    """
    empty = FakeResp(401, raw_text="")

    assert BaseApiClient.assert_error(empty, 401, http=401) is None

    with pytest.raises(AssertionError) as exc:
        BaseApiClient.assert_error(empty, 401, "未登录", http=401)

    assert "响应体是空的" in str(exc.value)
