# 【任务 #4.1a：写操作闭环 + 数据复原（健康档案）】
# 本文件只测一个资源：/health/info（健康档案）。
# 前几课的用例全在测"读"接口——发请求、看响应，不改动服务端任何数据。
# 这一课第一次测"写"接口，它带来两个全新问题，也是本文件要示范的两件事：
#
#   ① 怎么证明"真的写进去了"？
#      → 写完必须再读一次来验证（写读回环）。只断言 POST 返回 200 是不够的：
#        接口完全可能"告诉你成功了、实际没落库"。
#
#   ② 写坏了怎么收场？
#      → 这个接口是"更新或新增"（upsert）语义，测试往里写数据会覆盖张三的真实档案。
#        所以用 yield 夹具：测之前备份、测之后（无论成功失败）自动还原。
#
# 【为什么档案和目标分成了两个文件？】
# 见同目录的 test_health_goal.py。简单说：一条只测档案的用例，
# 不该白白去打"饮食目标"的接口——夹具的粒度要匹配用例的需求。

from datetime import datetime

import pytest

# updateTime 的服务端格式固定为"秒级 ISO"，实测形如 '2026-09-29T10:56:11'，
# 且**同一秒内的两次写入会返回同一个值**——这一点直接决定了下面那条断言的写法。
TS_FMT = "%Y-%m-%dT%H:%M:%S"

# ============================================================================
# 一、字段清单
# ============================================================================
# 从 GET 拿到的 data 里除了业务字段，还有 id / userId / createTime / updateTime，
# 这些是服务端生成的，POST 时不该回传。所以只挑出"请求字段"。

INFO_FIELDS = [
    "age", "gender", "height", "weight", "bmi", "bmr", "bloodPressure",
    "bloodSugar", "activityLevel", "exerciseDuration", "exerciseType", "chronicDiseases",
]

# 实测出来的必填项（删掉哪个字段会报"XX不能为空"）—— 不是猜的，是逐个删出来跑出来的
INFO_REQUIRED = [
    ("age", "年龄不能为空"),
    ("gender", "性别不能为空"),
    ("height", "身高不能为空"),
    ("weight", "体重不能为空"),
]


# ============================================================================
# 二、数据复原夹具（本课最核心的新东西）
# ============================================================================

@pytest.fixture
def info_env(api, auth_headers):
    """备份当前健康档案；用例结束后自动还原。

    【yield 夹具】和之前见过的 fixture（直接 return）不同，这里分两段：
        yield 之前 = setup（用例开始前执行）
        yield 之后 = teardown（用例结束后执行，**就算用例断言失败了也会执行**）
    这个"一定会执行"的保证，是它比"用例最后一行手动还原"更可靠的原因——
    用例中途挂掉时，手动还原那行根本不会被执行，真实数据就留在脏状态了。

    返回值是档案备份（dict），用例里拿它当"一份合法的请求体"用。

    注意它**只管 /health/info**：不碰 /health/goal。
    所以每条用它的用例只花 2 次请求（1 次 GET 备份 + 1 次 POST 还原），
    而不是"不管测什么都要连目标一起备份还原"的 4 次。
    """
    info = api.assert_ok(api.get("/health/info", headers=auth_headers))["data"]
    backup = {k: info[k] for k in INFO_FIELDS}

    yield backup

    # ---- 以下是 teardown：把数据写回原样 ----
    api.assert_ok(api.post("/health/info", json=backup, headers=auth_headers))


# ============================================================================
# 三、鉴权：未登录一律 401
# ============================================================================
# API.md 把 /health/* 标为"用户"级别，实测确实要 token（无 token → 401 且响应体为空）。
# 拆分后本文件只剩一个接口，原来为"省函数"而写的 parametrize 也就没必要了，
# 直接写成普通函数更直白。

def test_get_info_requires_token(api):
    """未登录读健康档案 → 401"""
    assert api.get("/health/info").status_code == 401


def test_post_info_requires_token(api):
    """未登录写健康档案 → 401（鉴权发生在参数校验之前，所以空 body 也是 401）"""
    assert api.post("/health/info", json={}).status_code == 401


# ============================================================================
# 四、读接口：不只是 code==200，还要验结构
# ============================================================================

def test_get_info_has_analysis(api, auth_headers):
    """GET /health/info 的信封里除了 data 还多一个 analysis（API.md 第 2 节提过）。

    assert_ok 只负责判 "HTTP 200 + code 200"，**字段级结构**要自己断言。
    """
    body = api.assert_ok(api.get("/health/info", headers=auth_headers))
    assert "data" in body
    assert "analysis" in body, "健康档案接口应额外返回 analysis 分析块"
    assert "summary" in body["analysis"], "analysis 里应有 summary 结论文本"


# ============================================================================
# 五、写读回环：写进去 → 读回来对账
# ============================================================================

def test_write_info_then_read_back(api, auth_headers, info_env):
    """POST 改档案 → GET 反查确认值**真的变了**。

    技巧：不写死 "age=25"，而是写 **当前值 + 1**。
    因为如果写死 25，而库里本来就是 25，那"写入没生效"也照样能通过——
    等于什么都没证明。取"当前值+1"保证写入前后的值一定不同。
    """
    info = info_env
    new_age = (info["age"] or 0) + 1
    new_weight = float(info["weight"]) + 1.5

    resp = api.post("/health/info", json={**info, "age": new_age, "weight": new_weight},
                    headers=auth_headers)
    body = api.assert_ok(resp)
    # ① 响应体里返回的就是写入后的对象
    assert body["data"]["age"] == new_age

    # ② 再读一次，确认落库了（这一半才是"数据闭环"的关键）
    back = api.assert_ok(api.get("/health/info", headers=auth_headers))["data"]
    assert back["age"] == new_age, "写入后反查，年龄应已更新"
    assert back["weight"] == new_weight, "写入后反查，体重应已更新"


# ============================================================================
# 六、必填校验：逐个删字段，看后端到底拦不拦
# ============================================================================

@pytest.mark.parametrize("field, want_msg", INFO_REQUIRED, ids=[f"缺{i[0]}" for i in INFO_REQUIRED])
def test_info_required_fields(api, auth_headers, info_env, field, want_msg):
    """删掉必填字段 → 400 + 统一信封 + 指定提示语。

    这类用例的价值：把"后端的校验规则"从口头约定变成可回归的断言。
    哪天有人把校验删了，这里立刻报红。
    """
    info = info_env
    payload = {k: v for k, v in info.items() if k != field}

    resp = api.post("/health/info", json=payload, headers=auth_headers)
    assert resp.status_code == 400, f"缺 {field} 应被拒绝"
    body = resp.json()
    assert body["code"] == 400, "失败也要走统一信封（code/message）"
    assert body["message"] == want_msg


# ============================================================================
# 七、曾经的缺陷，现已修复 —— 转为正式守卫用例（不再挂 xfail）
# ============================================================================
# 这三条原本挂着 @pytest.mark.xfail（因为后端确实有 bug）。2026-09-29 复跑时
# 它们全部变成 **XPASS** —— 这正是 xfail 的设计用途：后端修好了，它主动提醒你摘标记。
# 现在摘掉标记，它们回到"正常守卫"状态：**哪天再退化，就会直接变红**。
#
# 历史记录（保留备查，别照抄旧结论）：
#   ① height=0 → BMI 除零 → message 里泄露
#      "nested exception is org.apache.ibatis.type.TypeException: ... '∞' is not a valid numeric value"
#   ② age=-1 / weight=-5 / bloodSugar=-1 / age=999 → 实测返回 200 并被保存（当时无范围校验）
#   ④ upsert 更新数据时 updateTime 不刷新（值变了、时间戳没变）
#
# 注意：这些用例仍会往库里写数据，所以继续挂 info_env 由夹具还原。

def test_height_zero_rejected(api, auth_headers, info_env):
    """height=0 → 参数校验应提前拦住；就算拒绝，也绝不能把框架内部异常吐给调用方。

    【历史】曾实测到 message 为
      "nested exception is org.apache.ibatis.type.TypeException: ... '∞' is not a valid numeric value"
    —— 除零没防 + 内部实现泄露（安全问题）。本次复核确认已修复。
    """
    info = info_env
    resp = api.post("/health/info", json={**info, "height": 0}, headers=auth_headers)
    body = resp.json()
    assert "nested exception" not in (body.get("message") or ""), \
        f"不应把框架内部异常暴露给调用方，实际 message={body.get('message')!r}"


def test_negative_age_rejected(api, auth_headers, info_env):
    """age=-1 应被参数校验拒绝。

    【历史】曾实测返回 200 并被保存成功（同为 200 的还有 weight=-5、bloodSugar=-1、age=999）。
    本次复核确认已修复。
    """
    info = info_env
    resp = api.post("/health/info", json={**info, "age": -1}, headers=auth_headers)
    assert resp.status_code == 400, "负数年龄应被参数校验拒绝"


def test_update_time_refreshed_on_write(api, auth_headers, info_env):
    """写入新值后，反查 updateTime 应被刷新成"刚才"。

    【历史】曾实测写入后 updateTime 仍是旧值（2026-03-15T22:35:05）——值变了、时间戳没变。
    本次复核确认已修复。

    写法要点①：updateTime 不在 INFO_FIELDS 里（它是服务端生成的），
              所以要**写前先读一次、写后再读一次**。

    写法要点②（本条踩过的坑，值得单独记住）：
      最初我写的是 `assert after != before`——"变了没变"。**这是错的**，会假失败：
      上一个用例的 teardown 刚好 POST 过一次，两次写入落在**同一秒**，
      而 updateTime 精度只到秒（实测：相隔 0.2 秒的两次写入返回同一个值），
      于是 after == before → 红。单独跑这条却能过（前一次写入是很久以前），
      典型的"顺序依赖假失败"。
      正确写法：判它**是否接近当前时刻**——这才是"最后更新时间"的真实契约。
      这样既不受秒精度影响，又能抓到原来的 bug（旧值停在几个月前，离 now 十万八千里）。
    """
    info = info_env
    before = api.assert_ok(api.get("/health/info", headers=auth_headers))["data"]["updateTime"]

    api.assert_ok(api.post("/health/info", json={**info, "age": (info["age"] or 0) + 1},
                           headers=auth_headers))

    after = api.assert_ok(api.get("/health/info", headers=auth_headers))["data"]["updateTime"]

    after_dt = datetime.strptime(after, TS_FMT)
    before_dt = datetime.strptime(before, TS_FMT)
    now = datetime.now()

    assert after_dt >= before_dt, f"updateTime 不应倒退：写前 {before} → 写后 {after}"
    drift = abs((now - after_dt).total_seconds())
    assert drift <= 300, (
        f"写入后 updateTime 应反映本次写入（接近当前时刻），"
        f"实际 {after}，与当前时刻相差 {drift:.0f} 秒"
    )
