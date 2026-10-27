# common/schemas.py
# 【契约层】响应"说明书"：每个核心接口的响应该长什么样，全写在这里。
#
# ══ 这个文件只做两件事 ══
#   1. 定义说明书（普通 JSON Schema 字典，draft-07 语法，**没有自定义任何语法**）
#   2. check() —— 拿说明书画圈，不符合就抛 AssertionError
#
# 为什么要这层？只断 `code == 200` 的话，下面这些全都发现不了：
#   · data 少了个字段（前端取到 undefined，页面白屏）
#   · 类型漂了（userId 从 1 变成 "1"，前端 === 比较全失效）
#   · 枚举越界（role 冒出个 "superadmin"）
# 这一层管的就是这三样。
#
# ══ jsonschema 速查（看不懂某条就回来查这里）══
#   {"type": "object", "required": [...], "properties": {...}}
#       对象要长这样；required 是**必须有**的字段名列表
#   {"type": "integer"} / "string" / "number" / "boolean" / "null" / "array"
#       类型；注意 boolean 不会被当成 integer（jsonschema 自带这个判断）
#   {"type": ["string", "null"]}
#       二选一：可以是字符串，也可以是 null
#   {"enum": ["user", "admin"]}
#       取值只能是这几个之一
#   {"anyOf": [A, B]}
#       满足 A 或 B 任一即可（本文件里主要用来表达"可以是 null 也可以是对象"）
#
# ══ 两条刻意的取舍（不是漏写）══
#   ① 不写 additionalProperties: False
#      后端**新增**字段是向后兼容的，不该让测试红。会红的只有"删字段 / 改类型 / 枚举越界"。
#   ② 数组只验"是数组"，不验元素（见 cards / sources）
#      实测这两个数组在有内容的场景才看得到元素结构，现在拿空数组猜元素长什么样 = 编。
#      ⚠️ 所以空数组永远通过 schema —— "必须非空"要开发例单独断 len()，schema 管不了。
#
# ══ 全部字段来自实测（2026-10-26 真打 8080 抓的响应），不是照 DTO 猜的 ══
#   猜出来的 schema 会把"后端本来就错的地方"当成标准，那就白做了。

from jsonschema import Draft7Validator


# ==================== 校验器 ====================

def check(instance, schema, label="响应"):
    """按说明书检查；不符合就抛 AssertionError，**一次列出全部问题**。

    为什么一次列全而不是发现第一个就抛：
      字段漂了通常是"整批一起漂"（比如后端换了 DTO），逐个改逐个跑太慢。
    """
    problems = list(Draft7Validator(schema).iter_errors(instance))
    if not problems:
        return instance

    lines = []
    for err in sorted(problems, key=lambda e: list(e.absolute_path)):
        path = ".".join(["body"] + [str(p) for p in err.absolute_path])
        lines.append(f"  · {path}：{_explain(err)}")

    raise AssertionError(
        f"{label}结构不符（{len(problems)} 处）：\n" + "\n".join(lines)
        + "\n→ 要么后端把契约改了（改代码），要么 schema 写错了（改这里）。"
          "先看实际响应再定，别顺手把 schema 改成现状。"
    )


def _explain(err):
    """把 jsonschema 的英文报错翻成能直接看懂的一句话。

    只翻最常见的四类；其余原样返回（英文也比没有强）。
    不翻的话报错长这样："'status' is a required property" —— 看得懂但费劲。
    """
    rule, expect, actual = err.validator, err.validator_value, err.instance

    if rule == "required":
        # err.message 形如 "'status' is a required property"，取中间那个字段名
        missing = str(err.message).split("'")[1]
        return f"缺少必填字段 {missing}"
    if rule == "type":
        return f"类型应为 {expect}，实际 {type(actual).__name__}（{actual!r}）"
    if rule == "enum":
        return f"取值只能是 {expect} 之一，实际 {actual!r}"
    if rule in ("minimum", "maximum", "minLength", "maxLength"):
        return f"实际 {actual!r}，不满足 {rule}={expect}"
    return err.message


# ==================== 信封 ====================

def ok(data, **extra):
    """成功响应的统一信封：{code, message, data}。

    extra 用来挂"在信封顶层、不在 data 里"的字段 ——
    目前只有 /health/info 的 analysis（后端 controller 直接 put 到外层）。
    """
    props = {"code": {"type": "integer"}, "message": {"type": "string"}, "data": data}
    props.update(extra)
    return {
        "type": "object",
        "required": list(props),
        "properties": props,
    }


def nullable(schema):
    """允许为 null 的字段。用于"没建档 / 没设置时 data 是 null"这类情况。"""
    return {"anyOf": [schema, {"type": "null"}]}


ERROR = {
    "type": "object",
    "required": ["code", "message"],
    "properties": {
        "code": {"type": "integer"},
        "message": {"type": "string"},
    },
}


# ==================== 复用零件 ====================

# 角色枚举 —— 实测只有这两个值。冒出第三个就说明权限模型变了，该红。
ROLE = {"type": "string", "enum": ["user", "admin"]}


# ==================== 各接口 ====================

# ---- 认证 ----

# ⚠️ login 和 register 的 data 与 /user/profile **不是同一个结构**（实测）：
#    login/register 有 token，没有 status/createTime/updateTime；
#    profile 反过来。想当然共用一个"用户对象"契约，两边必红。
LOGIN_SCHEMA = ok({
    "type": "object",
    "required": ["userId", "username", "email", "phone", "avatar", "role", "token"],
    "properties": {
        "userId": {"type": "integer"},
        "username": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": ["string", "null"]},    # 新注册账号没填手机号 → null
        "avatar": {"type": ["string", "null"]},
        "role": ROLE,
        "token": {"type": "string"},
    },
})

REGISTER_SCHEMA = LOGIN_SCHEMA   # 实测两者 data 字段完全一致，共用一份，改一处就够


# ---- 用户资料 ----

PROFILE_SCHEMA = ok({
    "type": "object",
    "required": ["userId", "username", "email", "phone", "avatar",
                "role", "status", "createTime", "updateTime"],
    "properties": {
        "userId": {"type": "integer"},
        "username": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": ["string", "null"]},
        "avatar": {"type": ["string", "null"]},
        "role": ROLE,
        "status": {"type": "integer"},            # 实测 1 = 正常；前后端拿它判禁用
        # createTime / updateTime 是字符串（后端直接序列化 LocalDateTime）。
        # 以前全项目没有任何断言碰过这两个字段 —— null 或变成数字都全绿。
        "createTime": {"type": "string"},
        "updateTime": {"type": "string"},
    },
})


# ---- 健康档案 ----

# /health/info 的分析结论：**挂在信封顶层**（body.analysis），不在 data 里。
ANALYSIS = {
    "type": "object",
    "required": ["summary", "bmiAdvice", "bmiCategory", "bloodPressureAdvice",
                 "bloodPressureStatus", "bloodSugarAdvice", "bloodSugarStatus",
                 "activityAdvice", "activityStatus", "overallLevel",
                 "goalInsight", "recommendations", "tags"],
    "properties": {
        "summary": {"type": "string"},
        "bmiAdvice": {"type": "string"},
        "bmiCategory": {"type": "string"},
        "bloodPressureAdvice": {"type": "string"},
        "bloodPressureStatus": {"type": "string"},
        "bloodSugarAdvice": {"type": "string"},
        "bloodSugarStatus": {"type": "string"},
        "activityAdvice": {"type": "string"},
        "activityStatus": {"type": "string"},
        "overallLevel": {"type": "string"},
        "goalInsight": {"type": "string"},
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
}

HEALTH_INFO_SCHEMA = ok(
    nullable({
        "type": "object",
        "required": ["id", "userId", "age", "gender", "height", "weight", "bmi",
                     "bmr", "bloodPressure", "bloodSugar", "activityLevel",
                     "exerciseDuration", "exerciseType", "chronicDiseases",
                     "createTime", "updateTime"],
        "properties": {
            "id": {"type": "integer"},
            "userId": {"type": "integer"},
            "age": {"type": "integer"},
            # 实测枚举只有 male / female —— 传中文"男"是 400「性别取值不合法」。
            "gender": {"type": "string", "enum": ["male", "female"]},
            "height": {"type": "number"},
            "weight": {"type": "number"},
            "bmi": {"type": "number"},
            # bmr 在刚建档时是 null，之后 GET 会算出来 → 必须允许 null
            "bmr": {"type": ["number", "null"]},
            "bloodPressure": {"type": ["string", "null"]},
            "bloodSugar": {"type": ["number", "null"]},
            "activityLevel": {"type": ["string", "null"]},
            "exerciseDuration": {"type": ["integer", "null"]},
            "exerciseType": {"type": ["string", "null"]},
            "chronicDiseases": {"type": ["string", "null"]},
            "createTime": {"type": "string"},
            "updateTime": {"type": "string"},
        },
    }),
    analysis=ANALYSIS,        # 顶层的 analysis —— 不管建没建档都在
)

# /health/history：每次 POST /health/info 追加一条。
# ⚠️ 历史为空时 data 是 []，schema 对空数组无话可说（没元素可验）。
HEALTH_HISTORY_SCHEMA = ok({
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "userId", "weight", "bmi", "exerciseDuration",
                     "recordDate", "createTime"],
        "properties": {
            "id": {"type": "integer"},
            "userId": {"type": "integer"},
            "weight": {"type": "number"},
            "bmi": {"type": "number"},
            # 实测 20 条历史里有 2 条是 null —— 老记录没填运动时长。
            # 这不是缺陷，是历史数据本来就可以不填；写死 integer 会在"完全正常"时红。
            "exerciseDuration": {"type": ["integer", "null"]},
            "recordDate": {"type": "string"},
            "createTime": {"type": "string"},
        },
    },
})


# ---- 饮食目标 ----

HEALTH_GOAL_SCHEMA = ok(nullable({
    "type": "object",
    "required": ["id", "userId", "goalType", "targetWeight", "targetCalories",
                 "proteinRatio", "carbsRatio", "fatRatio", "proteinTarget",
                 "carbsTarget", "fatTarget", "waterTarget", "status",
                 "startDate", "endDate", "reminderEnabled", "reminderTime",
                 "createTime", "updateTime"],
    "properties": {
        "id": {"type": "integer"},
        "userId": {"type": "integer"},
        "goalType": {"type": "string"},          # 实测 "减脂"
        # ↓ 这 8 个是后端**算出来的**：刚 POST 完是 null，再 GET 才有值
        "targetWeight": {"type": ["number", "null"]},
        "targetCalories": {"type": ["number", "null"]},
        "proteinRatio": {"type": ["number", "null"]},
        "carbsRatio": {"type": ["number", "null"]},
        "fatRatio": {"type": ["number", "null"]},
        "proteinTarget": {"type": ["number", "null"]},
        "carbsTarget": {"type": ["number", "null"]},
        "fatTarget": {"type": ["number", "null"]},
        "waterTarget": {"type": ["integer", "null"]},
        "status": {"type": ["integer", "null"]},
        "startDate": {"type": "string"},
        "endDate": {"type": ["string", "null"]},
        "reminderEnabled": {"type": ["integer", "null"]},
        "reminderTime": {"type": ["string", "null"]},
        "createTime": {"type": "string"},
        "updateTime": {"type": "string"},
    },
}))


# ---- AI 助手 ----

MESSAGE_BASE = {
    "role": {"type": "string"},              # 实测 "user" / "assistant"
    "text": {"type": "string"},
    "messageType": {"type": "string"},
    "createTime": {"type": "string"},
    "id": {"type": "integer"},
    # cards 是"消息里挂的卡片"，可能为空。元素结构待有卡片场景再补。
    "cards": {"type": "array"},
}

# 用户消息：没有 source / intent / ragUsed（那三个是助手回复才有的）
USER_MESSAGE = {
    "type": "object",
    "required": list(MESSAGE_BASE),
    "properties": MESSAGE_BASE,
}

# 助手消息：多了检索相关的 5 个字段
ASSISTANT_MESSAGE = {
    "type": "object",
    "required": list(MESSAGE_BASE) + ["source", "intent", "ragUsed",
                                      "retrievalStatus", "sources"],
    "properties": dict(MESSAGE_BASE, **{
        "source": {"type": "string"},
        "intent": {"type": "string"},        # 不在 schema 里限枚举：意图词表会调整
        "ragUsed": {"type": "boolean"},
        "retrievalStatus": {"type": "string"},
        "sources": {"type": "array"},
    }),
}

CONVERSATION = {
    "type": "object",
    "required": ["id", "title", "summary", "messageCount",
                 "lastMessageAt", "createTime", "updateTime"],
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "messageCount": {"type": "integer"},
        "lastMessageAt": {"type": "string"},
        "createTime": {"type": "string"},
        "updateTime": {"type": "string"},
    },
}

CHAT_SCHEMA = ok({
    "type": "object",
    "required": ["conversationId", "userMessage", "assistantMessage",
                 "conversation", "contextMessage"],
    "properties": {
        "conversationId": {"type": "integer"},
        "userMessage": USER_MESSAGE,
        "assistantMessage": ASSISTANT_MESSAGE,
        "conversation": CONVERSATION,
        # 实测正常对话时是 null；带上下文的场景才可能是对象（结构未摸）
        "contextMessage": {"type": ["object", "null"]},
    },
})

CONVERSATION_LIST_SCHEMA = ok({"type": "array", "items": CONVERSATION})

# ⚠️ GET /assistant/conversations/{id}/messages 的元素**和 chat 返回的不一样**（实测）：
#    只有 6 个基础字段，没有 source / intent / ragUsed / retrievalStatus / sources。
#    同一条消息在两个接口里形状不同 —— 共用 ASSISTANT_MESSAGE 会立刻红，
#    而那个红是"schema 用错了位置"，不是接口坏了。
#    要查"模型的意图判成什么"，只能看 chat 的响应，列表接口看不到。
MESSAGE_LIST_SCHEMA = ok({"type": "array", "items": USER_MESSAGE})
