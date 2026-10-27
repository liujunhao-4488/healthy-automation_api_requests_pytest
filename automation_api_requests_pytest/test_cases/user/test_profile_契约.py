# test_cases/user/test_profile_契约.py
# 【任务：个人资料响应的**结构契约**】
#
# ══ 和老文件 test_user_profile.py 的分工 ═══════════════════════════
#
#   test_user_profile.py  验「值」：改用户名生效了吗、只读字段被忽略了吗、库里对不对
#   本文件                验「形状」：9 个字段都在吗、类型对吗、枚举越界了吗
#
# ══ 为什么这个模块特别需要它 ═══════════════════════════════════════
#
#   老文件里**唯一**一处形状断言是 `assert set(data) == {9 个字段名}`（第 89 行）。
#   它只验「字段名齐不齐」，验不了「类型对不对」：
#
#       {"status": 1}     → 通过
#       {"status": "1"}   → 也通过          ← 洞在这一行
#       {"role": "root"}  → 也通过          ← 洞在这一行
#
#   而这两种恰恰是最容易悄悄发生、又最先让前端炸的变更。

from common.schemas import PROFILE_SCHEMA


def test_get_profile_response_shape(api, auth_headers):
    """GET /user/profile → 信封＋9 个字段的类型全部符合契约。

    对比老写法：`body = api.assert_ok(resp)` 只断 HTTP 200 + code 200。
    """
    resp = api.user.get_profile(headers=auth_headers)

    api.assert_ok(resp, "获取个人资料应成功", schema=PROFILE_SCHEMA)


def test_get_profile_without_token_rejects_with_empty_body(api):
    """不带 token → 401 且**响应体为空**。

    ⚠️ 这条同时说明一件事：401 是**不给信封**的（没有 code/message）。
       所以这里只给 http=401、不传期望文案 —— assert_error 看到空体会
       自动停在“只验 HTTP 状态”，不会硬去 resp.json() 套信封。
       把"哪些接口在 401 时不给 body"写清楚，比含糊地不断言有用。
    """
    resp = api.user.get_profile()

    api.assert_error(resp, 401, http=401)


def test_get_profile_with_fake_token_rejects_with_empty_body(api):
    """伪造 token → 401 空体，跟"没带 token"同一个口径。

    值一致性（401 vs 403 的选择）由老文件负责；这里只确认**形状**一致 ——
    两条失败路必须长得一样，否则前端要写两个分支。
    """
    resp = api.user.get_profile(headers={"Authorization": "Bearer not-a-real-token"})

    api.assert_error(resp, 401, http=401)


def test_update_profile_keeps_the_same_shape(api, auth_headers):
    """局部更新成功后，返回的 data **仍是同一套字段**。

    为什么值得单测：增量更新接口很容易写成"只回传被改的那几个字段"，
    前端拿去做局部刷新时，其他字段就变成了 undefined。
    同一份契约要管住 GET 和 PUT 两个出口。

    ⚠️ 故意提交**同一个用户名**（幂等）：老文件注释里实测过
       "张三提交'张三'是幂等保存、会 200"，所以这条不会改坏主测试账号。
    """
    current = api.assert_ok(
        api.user.get_profile(headers=auth_headers), "读取现状应成功"
    )["data"]

    resp = api.user.update_profile(
        {"username": current["username"]}, headers=auth_headers
    )

    body = api.assert_ok(resp, "提交同名（幂等）应成功", schema=PROFILE_SCHEMA)

    assert body["data"]["userId"] == current["userId"], "更新响应不该变成别人的资料"
