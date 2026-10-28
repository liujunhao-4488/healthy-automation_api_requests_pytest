# test_cases/admin/test_admin_authz.py
# 【鉴权矩阵】管理端 5 个接口：未登录必须 401、普通用户必须 403、而且**越权不能真改数据**。
#
# ============ 这个文件为什么存在 ============
# 管理接口一旦拦不住，泄露的是**整库用户的邮箱和手机号**（/user/admin/list 一次返回
# 258 条完整用户记录），或者给所有人推垃圾通知。所以这块的价值不在"多覆盖了几个接口"，
# 而在"它坏了后果最重"。
#
# ============ 测什么 / 不测什么 ============
# 测：谁能进来（401 / 403 / 200）、越权有没有产生副作用、被拒时有没有泄露信息。
# 不测：进去之后业务逻辑对不对（总览数字准不准、通知格式对不对）。
#      那是另一个文件的事，混在一起会让失败原因说不清。
#
# ============ 断言强度：这里最容易写成垃圾的地方 ============
# 这类测试最省事的写法是复制 5 遍 `assert resp.status_code == 403`。
# 那确实是绿的，但它有三个漏洞，本文件逐条堵：
#
#   漏洞 1：只断 403，不管副作用。
#           → 第 3 节：越权改状态后，用 admin 视角回查，证明**数据真的没变**。
#   漏洞 2：只断"错角色被拒"，没有对照组。
#           → 第 6 节：admin 调同样的接口必须 200。
#             否则"接口整个坏了、永远返回 403"也能让全部用例绿。
#   漏洞 3：不区分 403 和 404。
#           → 第 4 节：不存在的 userId 也必须 403。若返回 404，
#             说明后端先查存在性再查权限，等于给攻击者一个"这个 id 存不存在"的探针。
#
# ============ 为什么不用查数据库来证明"数据没变" ============
# 因为测试库和后端连的库**可能不是同一个**（本机就踩过：后端连 health_diet，
# 测试连 health_diet_test）。那种情况下查库查出来是 None，断言要么崩、要么假绿。
# 改用 admin 的读取能力当证据 —— 走的是同一个后端，物理上不可能对不上。

import uuid

import pytest

# 每次跑用一个唯一标记，混进 publish 的标题里。
# 万一权限失守、通知真发出去了，靠这个标记能在列表里精确定位到、并且清理掉。
RUN_MARKER = "authz-probe-" + uuid.uuid4().hex[:8]

# 鉴权矩阵全部无副作用（不造数据、不调模型），跑起来是秒级的，
# 所以同时挂 smoke 和 p0：谁改动鉴权链，第一道闸就该红。
pytestmark = [pytest.mark.p0, pytest.mark.smoke]


# ==================== 5 个管理接口的统一调用形式 ====================
# 写成"函数 + 参数化"，而不是 5 个方法里各写 5 遍 —— 加一个新管理接口时
# 只需要在这里补一行，5 组用例自动都有了。
#
# 每个函数签名统一是 (api, headers, user_id)，因为改状态那个接口需要 userId，
# 其它三个用不上。参数不一致就没法参数化了。

def _overview(api, headers, user_id):
    return api.admin.overview(headers=headers)


def _list_users(api, headers, user_id):
    return api.admin.list_users(headers=headers)


def _set_status(api, headers, user_id):
    # user_id 传的是**当前登录用户自己**，见文件末尾"为什么拿自己当靶子"。
    return api.admin.set_user_status(user_id, 0, headers=headers)


def _collect_stats(api, headers, user_id):
    return api.admin.collect_stats(headers=headers)


def _publish(api, headers, user_id):
    return api.admin.publish_notification(
        {"title": RUN_MARKER, "content": "越权测试探针，正常情况下不应该发出去"},
        headers=headers,
    )


# 全部 5 个接口（用于 401 / 403 两组全量扫描）
ALL_ADMIN_CALLS = [
    pytest.param(_overview, id="总览"),
    pytest.param(_list_users, id="用户列表"),
    pytest.param(_set_status, id="改用户状态"),
    pytest.param(_collect_stats, id="收藏统计"),
    pytest.param(_publish, id="发布通知"),
]

# 只读的 3 个（用于"正角色能通过"对照）。
# 为什么排除写操作：admin 真去改状态 / 真发通知，会在环境里留下痕迹，
# 而"正角色能读"已经足够证明路由和鉴权链是通的，不需要为了对照去污染数据。
READ_ONLY_ADMIN_CALLS = [
    pytest.param(_overview, id="总览"),
    pytest.param(_list_users, id="用户列表"),
    pytest.param(_collect_stats, id="收藏统计"),
]


# ==================== 夹具 ====================

@pytest.fixture
def my_user_id(api, auth_headers):
    """当前登录用户的 userId —— 越权测试要拿它当靶子。

    为什么从接口拿而不是写死 1：主账号的 id 在开发库是 1、在 CI 的测试库里
    也可能是 1，但这是**巧合**不是约定。写死的话，哪天 seed 改了 id 顺序，
    这条用例会去改别人的账号 —— 那是最糟的一种测试 bug。
    """
    body = api.assert_ok(api.user.get_profile(headers=auth_headers), "读取自己资料应成功")
    return body["data"]["userId"]


def _find_user(api, admin_headers, user_id):
    """用 admin 视角查某个人的记录，查不到就报清楚。"""
    body = api.assert_ok(
        api.admin.list_users(headers=admin_headers), "管理员查用户列表应成功"
    )
    hit = [u for u in body["data"] if u["userId"] == user_id]
    assert hit, (
        f"管理员列表里找不到 userId={user_id}。\n"
        f"→ 注意：这可能是**后端连的库和测试连的库不是同一个**导致的，"
        f"不一定是接口坏了。先确认两边库名一致。"
    )
    return hit[0]


# ==================== 一、未登录：必须 401 ====================

@pytest.mark.parametrize("call", ALL_ADMIN_CALLS)
def test_admin_api_requires_login(api, my_user_id, call):
    """不带 token 调管理接口 → 401。

    这一层挡的是"完全没登录的人"。它是 403 之外的另一道门：
      401 = 我不知道你是谁  → 该去登录
      403 = 我知道你是谁，但你不够格 → 登了也没用
    两者混用是常见 bug（把未登录也返回 403），所以分开验。

    ⚠️ 实测：全站 401 都是**空响应体**，不是 JSON 信封。
       所以这里断"响应体为空"，而不是去 resp.json() —— 那样会抛 JSONDecodeError，
       报错指向"解析失败"，掩盖了真正要验的东西。
    """
    resp = call(api, {}, my_user_id)

    assert resp.status_code == 401, (
        f"未登录调管理接口应返回 401，实际 {resp.status_code}。\n"
        f"→ 200 = 管理接口对匿名用户开放了（严重）；"
        f"403 = 把「未登录」和「没权限」混为一谈（应该 401）；"
        f"500 = 后端崩了。\n"
        f"响应体：{(resp.text or '')[:300]}"
    )
    assert not (resp.text or "").strip(), (
        f"401 应是空响应体（实测全站如此），实际返回了：{(resp.text or '')[:300]}\n"
        f"→ 如果这是有意改的（比如想让前端能提示「请先登录」），"
        f"那要同步改这条断言，并检查其它接口的 401 是否也一起改了。"
    )


# ==================== 二、普通用户：必须 403 ====================

@pytest.mark.parametrize("call", ALL_ADMIN_CALLS)
def test_admin_api_rejects_normal_user(api, auth_headers, my_user_id, call):
    """带普通用户的合法 token 调管理接口 → 403。

    这是鉴权矩阵的主体：**身份是真的、token 是有效的，只是角色不够**。
    只有这种请求被拦住，才说明后端真的在检查角色，而不是在检查"有没有登录"。
    """
    resp = call(api, auth_headers, my_user_id)

    api.assert_forbidden(resp, f"普通用户调[{call.__name__}]应被 403 拒绝")


# ==================== 三、越权不能真改数据（核心）====================

def test_escalation_does_not_change_user_status(api, auth_headers, admin_headers, my_user_id):
    """普通用户试图禁用自己 → 403，而且**数据库里的 status 必须还是 1**。

    ══ 为什么这条比"返回 403"值钱 ══
    返回 403 只证明"响应是对的"。如果后端先执行了更新、再抛权限异常
    （保存点没回滚、或者在 @Transactional 外面 catch 掉了），
    响应照样是 403，但数据已经改了 —— 单看状态码永远发现不了。

    ══ 为什么靶子是"自己" ══
    改别人要造临时账号，跑完还要删；而临时账号在"后端库 ≠ 测试库"时
    清理会静默失败（本项目已经因为这个泄漏过 26 个 pf_ 账号）。
    改自己：一定存在、一定能在 admin 列表里查到、不需要任何清理。

    ══ 兜底 ══
    finally 里用 admin 把自己恢复成 1。万一权限真的失守（这条用例会红），
    也不会把主测试账号留在禁用状态、把后面所有用例一起带崩。
    实测：禁用后**旧 token 仍然有效**，所以恢复是可行的，不会卡在登不上。
    """
    before = _find_user(api, admin_headers, my_user_id)
    assert before["status"] == 1, (
        f"用例开始前主测试账号应该是启用状态，实际 status={before['status']}。\n"
        f"→ 上一次运行可能没恢复干净，先手工把它改回 1 再跑。"
    )

    try:
        resp = api.admin.set_user_status(my_user_id, 0, headers=auth_headers)
        api.assert_forbidden(resp, "普通用户禁用自己应被拒绝")

        after = _find_user(api, admin_headers, my_user_id)
        assert after["status"] == 1, (
            f"越权请求被 403 拒绝了，但 status 从 1 变成了 {after['status']}！\n"
            f"→ 这是**权限判断发生在写操作之后**的典型症状：响应拦住了，数据已经改了。\n"
            f"→ 后端要检查的：@Transactional 边界、或者 try/catch 把异常吞在了事务里面。"
        )
    finally:
        # 用例成功时这里是幂等的空操作；失败时它负责把环境恢复原状。
        api.admin.set_user_status(my_user_id, 1, headers=admin_headers)


# ==================== 四、被拒时不能泄露"这个 id 存不存在"====================

def test_nonexistent_user_also_returns_403(api, auth_headers):
    """普通用户改一个**不存在**的 userId → 也应该 403，不是 404。

    ══ 为什么这算安全问题 ══
    如果先查用户是否存在、再查权限，那么：
        存在的 id   → 403
        不存在的 id → 404
    攻击者不用登录就能把 id 从 1 试到 100 万，画出一张"哪些用户 id 存在"的地图
    （业界叫用户枚举 / user enumeration）。正确顺序是**先鉴权、再查资源**。

    实测当前后端是对的（全返 403），所以这条是**回归保护**：
    哪天有人在 Controller 里把 userService.findById 挪到 requireAdmin 前面，
    这条会红，而且报错会明确指出"泄露了存在性"。
    """
    resp = api.admin.set_user_status(999999999, 0, headers=auth_headers)

    assert resp.status_code != 404, (
        "改不存在的用户返回了 404 —— 说明后端**先查存在性、再查权限**。\n"
        "→ 这意味着任何人（哪怕没有权限）都能靠 404/403 的差异枚举出哪些 userId 存在。\n"
        "→ 正确顺序：先 requireAdmin()，再查用户。"
    )
    api.assert_forbidden(resp, "改不存在的用户应被 403 拒绝（而不是暴露它不存在）")


# ==================== 五、token 的三种坏形态 ====================

BAD_TOKENS = [
    pytest.param({"Authorization": "Bearer "}, id="Bearer后为空"),
    pytest.param({"Authorization": "Bearer aaa.bbb.ccc"}, id="格式对但内容是假的"),
    pytest.param({"Authorization": "definitely-not-a-token"}, id="缺Bearer前缀"),
]


@pytest.mark.parametrize("headers", BAD_TOKENS)
def test_malformed_token_is_rejected(api, headers):
    """token 缺失 / 伪造 / 格式不对 → 一律 401，不能 500。

    ══ 为什么单独列出来 ══
    鉴权链最容易在"token 存在但解析不了"这一支上漏掉异常处理，
    结果是 500 而不是 401。500 会出现在错误日志和监控里，
    把"有人在探测鉴权"伪装成"服务不稳定"。

    ══ 为什么用 401 而不是 403 ══
    这三种情况后端根本不知道你是谁 = 未认证，和"没带 token"是同一类。
    """
    resp = api.admin.overview(headers=headers)

    assert resp.status_code == 401, (
        f"坏 token 应返回 401（未认证），实际 {resp.status_code}。\n"
        f"→ 500 说明后端没接住 token 解析异常；"
        f"200 说明鉴权被完全绕过了（严重）。\n"
        f"响应体：{(resp.text or '')[:300]}"
    )


# ==================== 六、对照组：正角色必须能通过 ====================

@pytest.mark.parametrize("call", READ_ONLY_ADMIN_CALLS)
def test_admin_api_works_for_real_admin(api, admin_headers, my_user_id, call):
    """>>> 这一组是前面所有 403 断言的**前提**，不是补充。 <<<

    如果只测"普通用户返回 403"，有一个致命的假绿场景：
    接口整个坏掉了（路由没注册、Controller 抛异常被全局异常处理器转成 403、
    或者 token 解析对所有人都失败），普通用户拿到的仍然是 403 —— 用例全绿，
    但真实的管理员也用不了。

    有了这一组，"403 是因为权限"才成立：同样一个 URL、同一套代码，
    admin 进来是 200，普通用户进来是 403，差异只可能来自角色。
    """
    resp = call(api, admin_headers, my_user_id)

    body = api.assert_ok(resp, f"管理员调[{call.__name__}]应成功")

    # 除了 code=200，还要确认**真的拿到了数据**。
    # 只断 code 的话，接口返回 {"code":200,"data":null} 也算过 ——
    # 那可能是"查出了问题但没报错"，比如 SQL 写错、或者后端连错了库。
    #
    # ⚠️ 这里断的是"不是 None"，不是"非空"：
    #    收藏统计在库里没有收藏数据时，合理解就是空数组 []（新库/CI 就是这样）。
    #    断非空会把"合法的空结果"判成失败 —— 那种假红最伤测试的可信度。
    assert body.get("data") is not None, (
        f"管理员调[{call.__name__}]返回的 data 是 null。\n"
        f"→ 通常意味着查询本身有问题（条件写错、表读错库），不是权限问题。"
        f"整份响应：{str(body)[:300]}"
    )


# ==================== 七、缺陷固定：403 不走统一信封 ====================
# 接口覆盖矩阵 #10 已记录这个缺陷：业务错误（400）走 {"code","message"} 信封，
# 而权限拒绝（403）走 Spring Security 的默认体 {"timestamp","status","error","path"}。
# 前端如果按统一信封解析，拿到 403 时会读到一个 undefined 的 message，弹窗是空白的。
#
# 为什么用 xfail 而不是 assert 它"就是 Spring 默认体"：
#   断言"必须是默认体"等于把缺陷当成正确答案钉死 —— 哪天修好了测试反而红。
#   xfail(strict=True) 的语义是"我知道它现在是坏的，修好了请提醒我"：
#     现在：断言失败 → 记为 xfailed（预期内）
#     修好：断言通过 → 变成 XPASS → strict 模式下报错，提醒你删掉这条

@pytest.mark.xfail(
    strict=True,
    reason="缺陷#10：403 返回 Spring 默认错误体，不走统一信封 {code,message}",
)
def test_forbidden_body_uses_unified_envelope(api, auth_headers):
    """403 也应该走 {"code":403, "message":"无权限"} 的统一信封。"""
    resp = api.admin.overview(headers=auth_headers)
    body = resp.json()

    assert "code" in body and "message" in body, (
        f"403 没有走统一信封，实际返回：{body}\n"
        f"→ 前端统一按 body.message 弹提示，这里会拿到 undefined。"
    )


# ==================== 八、发布通知：越权必须没真发出去 ====================

def test_publish_escalation_does_not_create_notification(api, auth_headers):
    """普通用户调"发布通知" → 403，而且用户的通知列表里**不能**出现这条。

    ══ 为什么这条必须单独测，不能靠第二节的 403 覆盖 ══
    publish 是 5 个管理接口里唯一有写副作用的。如果后端在权限判断之前就已经
    把通知写进了表（或者消息队列），响应是 403，但通知已经推给所有人了 ——
    这种"拦住了响应、没拦住副作用"的 bug，只看状态码永远发现不了。

    ══ 用唯一标记做证据 ══
    标题里带 RUN_MARKER（每次运行随机）。查自己的通知列表时如果命中这个标记，
    说明通知真的发出来了 —— 那不只是断言失败，还要顺手删掉，
    否则这条垃圾通知会一直躺在收件箱里。

    ⚠️ 覆盖范围有限：这里只查了**自己**的收件箱。如果 publish 的逻辑是
       "发给指定 userId"而探针没指定，可能发给了别人。要查全量得用 admin 视角，
       但后端没有"管理员查所有通知"的接口，所以只能到这一步。
    """
    resp = _publish(api, auth_headers, None)
    api.assert_forbidden(resp, "普通用户发布通知应被拒绝")

    # 被拒绝之后再查自己的收件箱
    body = api.assert_ok(
        api.notification.list_mine(headers=auth_headers), "读取通知列表应成功"
    )

    leaked = [n for n in (body.get("data") or []) if RUN_MARKER in (n.get("title") or "")]

    # 先清理再断言：如果真泄漏了，别让探针通知留在收件箱里
    for n in leaked:
        api.notification.delete(n["id"], headers=auth_headers)

    assert not leaked, (
        f"越权请求被 403 拒绝了，但通知**真的发出去了**（找到 {len(leaked)} 条）。\n"
        f"→ 这是「拦住了响应、没拦住副作用」，比单纯少一道鉴权更危险：\n"
        f"  攻击者看到 403 会以为失败了，实际上全站用户都收到了一条通知。\n"
        f"→ 已尝试删除这 {len(leaked)} 条探针通知（id={[n['id'] for n in leaked]}）。\n"
        f"→ 后端要检查：权限判断是否在写库之前。"
    )
