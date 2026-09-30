# 【任务 #4.1b：写操作闭环 + 数据复原（饮食目标）】
# 本文件只测一个资源：/health/goal（饮食目标）。
# 兄弟文件 test_health_info.py 测的是 /health/info（健康档案），两者刻意分开。
#
# 【为什么拆成两个文件？】
# 拆分前它们挤在 test_health_crud.py 里，共用同一个 health_env 夹具，
# 而那个夹具是"买一送一"的：不管用例测的是档案还是目标，
# 都要 GET 两个接口 + POST 两个接口（共 4 次请求）来备份和还原。
# 于是"只测目标"的用例也白白去打档案接口，还顺手动了档案的数据。
#
# 拆开后夹具各自只管自己那份（见下面的 goal_env），
# 一条用例的开销从 4 次请求降到 2 次，全文件请求数少一半。
# 这就是本节要记住的原则：
#
#     ★ 夹具的粒度，要匹配用例的需求。给多了就是白花的时间和多余的数据风险。
#
# 顺带一个判断标准——什么时候"不该拆"：
#   - 两个资源在业务上强耦合（一条用例必须同时改两边才能验证）→ 放一起更清楚
#   - 单个资源只有三五条用例 → 拆了反而碎片化
#   健康档案和饮食目标各自独立、用例也够多，属于"该拆"。

import pytest

# ============================================================================
# 一、字段清单
# ============================================================================
# 同样只挑"请求字段"，服务端生成的 id / userId / createTime / updateTime 不回传。

GOAL_FIELDS = [
    "goalType", "targetWeight", "targetCalories", "proteinRatio", "carbsRatio", "fatRatio",
    "proteinTarget", "carbsTarget", "fatTarget", "waterTarget", "status",
    "startDate", "endDate", "reminderEnabled", "reminderTime",
]

# 实测出来的必填项（删除测试一颗颗试出来的），只有 3 个
GOAL_REQUIRED = [
    ("goalType", "目标类型不能为空"),
    ("targetCalories", "目标卡路里不能为空"),
    ("startDate", "开始日期不能为空"),
]


# ============================================================================
# 二、数据复原夹具（只管 goal 的那一份）
# ============================================================================

@pytest.fixture
def goal_env(api, auth_headers):
    """备份当前饮食目标；用例结束后自动还原。

    【yield 夹具】两段式：
        yield 之前 = setup（用例开始前执行）
        yield 之后 = teardown（用例结束后执行，**就算用例断言失败了也会执行**）
    "一定会执行"这个保证，让它比"用例最后一行手动还原"可靠得多——
    用例中途挂掉时，手动还原那行根本走不到，真实数据就留脏了。

    返回值是目标备份（dict），用例里拿它当"一份合法的请求体"用。
    """
    goal = api.assert_ok(api.get("/health/goal", headers=auth_headers))["data"]
    backup = {k: goal[k] for k in GOAL_FIELDS}

    yield backup

    # ---- 以下是 teardown：把数据写回原样 ----
    api.assert_ok(api.post("/health/goal", json=backup, headers=auth_headers))


# ============================================================================
# 三、鉴权：未登录一律 401
# ============================================================================
# API.md 把 /health/* 标为"用户"级别，实测确实要 token。
# 拆分后本文件只剩一个接口，原先为"省函数"写的 parametrize 没必要了。

def test_get_goal_requires_token(api):
    """未登录读饮食目标 → 401"""
    assert api.get("/health/goal").status_code == 401


def test_post_goal_requires_token(api):
    """未登录写饮食目标 → 401（鉴权在参数校验之前，空 body 也是 401）"""
    assert api.post("/health/goal", json={}).status_code == 401


# ============================================================================
# 四、写读回环：写进去 → 读回来对账
# ============================================================================

def test_write_goal_then_read_back(api, auth_headers, goal_env):
    """POST 改饮食目标 → GET 反查确认值**真的变了**。

    技巧同档案：取"当前值 + 100"，不写死一个数字。
    写死的话，若库里本来就是那个值，"写入没生效"也会照样通过——等于什么都没证明。
    """
    goal = goal_env
    new_calories = float(goal["targetCalories"]) + 100

    api.assert_ok(api.post("/health/goal", json={**goal, "targetCalories": new_calories},
                           headers=auth_headers))
    back = api.assert_ok(api.get("/health/goal", headers=auth_headers))["data"]
    assert back["targetCalories"] == new_calories


# ============================================================================
# 五、必填校验：逐个删字段，看后端到底拦不拦
# ============================================================================

@pytest.mark.parametrize("field, want_msg", GOAL_REQUIRED, ids=[f"缺{i[0]}" for i in GOAL_REQUIRED])
def test_goal_required_fields(api, auth_headers, goal_env, field, want_msg):
    """饮食目标只有 3 个必填：goalType / targetCalories / startDate（实测）。

    把校验规则钉成可回归的断言：哪天有人把校验删了，这里立刻报红。
    """
    goal = goal_env
    payload = {k: v for k, v in goal.items() if k != field}

    resp = api.post("/health/goal", json=payload, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["message"] == want_msg


# ============================================================================
# 六、曾经的缺陷，现已修复 —— 转为正式守卫用例（不再挂 xfail）
# ============================================================================
# 这条原本挂着 @pytest.mark.xfail（因为后端确实有 bug：endDate 早于 startDate 也能存）。
# 2026-09-29 复跑时变成 **XPASS** —— 后端修好了，xfail 主动提醒可以摘标记。
# 摘掉后回到"正常守卫"状态：哪天再退化就会直接变红。
# 仍会往库里写数据，所以继续挂 goal_env 由夹具还原。

def test_end_before_start_rejected(api, auth_headers, goal_env):
    """endDate(2026-01-01) 早于 startDate(2026-12-31) 应被拒绝。

    【历史】曾被实测返回 200 并成功保存（当时不校验日期区间）。本次复核确认已修复。
    """
    goal = goal_env
    payload = {**goal, "startDate": "2026-12-31", "endDate": "2026-01-01"}
    resp = api.post("/health/goal", json=payload, headers=auth_headers)
    assert resp.status_code == 400, "结束日期早于开始日期应被拒绝"
