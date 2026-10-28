# api/base_api_client.py
# 【底座】所有"发请求"的动作都从这里长出来。
#
# 类比：它是一台"自动收银机"——
#   你只告诉它"买什么"（路径 path），它自己知道去哪个店（BASE_URL）、
#   最多等多久（TIMEOUT），并替你结账。
#
# 最小版只给了三样：get、post、assert_ok。
# 以后要用 put / delete，照着 get/post 的样子往下加就行。

import requests

from common import allure_helper
from common.logger import log, short_url
from config.config import BASE_URL, TIMEOUT

# 401 重登钩子：由 conftest 的会话夹具安装。
# 放在模块级而不是实例上，是因为 Api 聚合了 auth/user/health/assistant/kb 五个 client，
# 逐个挂钩子既啰嗦、又容易漏掉新加的接口类。
_on_unauthorized = None


def set_unauthorized_handler(handler):
    """handler(used_authorization) -> 新 Authorization | None。

    入参是这次请求实际带出去的 Authorization —— 钩子据此判断
    "是会话 token 过期了"还是"用例故意用错 token 测 401"。
    """
    global _on_unauthorized
    _on_unauthorized = handler


class BaseApiClient:
    # 这个 client 打到哪台机器。默认是 Java 后端；
    # 子类可以覆盖它去连别的服务（例如算法服务的 Flask，端口不一样）。
    # 之所以做成**类属性**而不是构造参数：绝大多数 client 都用默认值，
    # 只有极少数要改，改一行类属性比每个用例都传一遍参数省事得多。
    base_url = BASE_URL

    def __init__(self):
        # Session 会复用同一条 TCP 连接，比每次新建连接快。
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    # ---- 发请求 ----
    # path 只写相对路径（不带 BASE_URL），前缀在这里统一拼。
    # 每次请求都自动记一行日志（见 _log），用例里不用自己打印请求过程。

    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self._request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)

    def _request(self, method, path, **kwargs):
        """所有动词的唯一出口：统一超时 + 401 自动重登一次。

        ⚠️ 401 **不能无脑重登**：用例里"不带 token / 伪 token → 401"是**预期结果**，
        重登会把这类负向用例变成 200。所以只问钩子一句：
        "这次请求用的 Authorization 是不是当前会话 token？"
          · 是 → 重登、换新 token 重发一次；
          · 不是（没带 / 伪造 / 别人的 token）→ 原样返回 401。
        """
        kwargs.setdefault("timeout", TIMEOUT)
        url = self.base_url + path

        resp = self._session.request(method, url, **kwargs)
        if resp.status_code == 401 and _on_unauthorized is not None:
            used = (kwargs.get("headers") or {}).get("Authorization")
            fresh = _on_unauthorized(used)
            if fresh:
                # 直接在原 headers 上改，不复制：auth_headers 是**每条用例一份**的字典，
                # 同一条用例后面还会拿它发好几次请求 —— 只改副本的话，
                # 第二次请求又带着旧 token，钩子会以为"这不是当前 token"而不再重登。
                headers = kwargs.get("headers")
                if headers is None:
                    headers = {}
                    kwargs["headers"] = headers
                headers["Authorization"] = fresh
                resp = self._session.request(method, url, **kwargs)

        self._log(resp)
        return resp

    # ---- 记日志 ----

    def _log(self, resp):
        """记一行：`→ POST /auth/login   200   141ms`。

        排版约定（和 logger.py 里那三条原则一致）：
          · 用短路径（砍掉 BASE_URL 前缀），固定宽度对齐，方便竖着扫；
          · 4xx 的响应体跟着记 —— 失败原因（message）就藏在里面；
          · **只有 5xx 才是 WARNING**。400 是我们主动测出来的正常剧情，
            全标成警告的话，警告就泛滥成噪音、失去"一眼挑出问题"的作用。
        · 顺手把这次交互贴进 Allure 报告（见 common/allure_helper.py）。
            放在这儿同样是"一处埋点、全覆盖"：所有业务请求都过 _log，
            所有用例一行都不用改，报告里天然带完整现场。
        """
        ms = resp.elapsed.total_seconds() * 1000
        line = "→ %-4s %-18s %3d %6.0fms" % (
            resp.request.method,
            short_url(resp.request.url),
            resp.status_code,
            ms,
        )
        if resp.status_code >= 400:
            body = resp.text.strip().replace("\n", " ")[:160]
            if body:
                line += "  " + body

        if resp.status_code >= 500:
            log.warning(line)
        else:
            log.info(line)

        # 报告是**旁路**：它内部已经把异常吞干净了，不会影响这条请求的结果。
        allure_helper.attach_http(resp)

    # ---- 判结果 ----

    @staticmethod
    def assert_ok(resp, msg="接口应成功", schema=None):
        """一行断定"接口成功"：HTTP 200 且业务 code==200，返回解析好的 body。

        只用于"期望成功"的调用；期望失败的用 assert_error。

        ══ schema 参数（可选）══
        传了就把整份响应的**结构和字段类型**也验掉，而不只是 code：

            body = api.assert_ok(resp, "登录应成功", schema=schemas.LOGIN_SCHEMA)

        schema 从 common/schemas.py 拿（普通 JSON Schema 字典）。
        不传时行为和以前完全一样 —— 老调用一行都不用改。

        为什么是 staticmethod？因为它只做一件事 —— 检查传进来的这个响应，
        跟"谁发的请求、用哪个 client 发的"毫无关系。不写 self 反而更诚实，
        也让 api/__init__.py 的总入口能直接把它借过去用。

        ⚠️ 2026-10-26 顺手改掉两处会**混淆病因**的写法：
          · `body["code"]` → `body.get("code")`：原来 code 字段一缺就抛 KeyError，
            报错是一行 `KeyError: 'code'`，看不出是"契约坏了"还是"用例写错了"；
            现在走断言，错误信息里带完整响应体。
          · 补了"响应体必须是 JSON 对象"的检查：HTTP 200 但 body 是 HTML（打错地址、
            被登录页接走）时，原来会在 resp.json() 抛一句看不懂的 JSONDecodeError。
        """
        assert resp.status_code == 200, (
            f"{msg}：HTTP {resp.status_code}，响应体 {(resp.text or '')[:400]}"
        )

        try:
            body = resp.json()
        except ValueError:
            raise AssertionError(
                f"{msg}：HTTP 200 但响应体不是 JSON：{(resp.text or '')[:400]}\n"
                f"→ 多半是打错了地址 / 被网关或登录页接走了，不是接口逻辑问题。"
            )

        assert isinstance(body, dict), (
            f"{msg}：期望统一信封（JSON 对象），实际 {type(body).__name__}："
            f"{str(body)[:300]}"
        )
        assert body.get("code") == 200, (
            f"{msg}：code={body.get('code')}，message={body.get('message')}"
        )

        # 形状校验放最后：code 都不对的时候，先报"失败原因"比报"字段漂了"有用。
        if schema is not None:
            from common.schemas import check

            check(body, schema, label=f"{msg}的响应")
        return body

    @staticmethod
    def assert_error(resp, code, message=None, http=400, contains=False):
        """一行断定"接口该失败"：HTTP 状态 + 业务 code + 错误文案，全部验掉。

        以前每个失败用例都要手写三层：

            assert resp.status_code == case["want_http"], "..."
            body = resp.json()
            assert body["code"] == case["want_code"], "..."
            assert case["want_msg"] in body["message"], "..."

        现在一行：

            api.assert_error(resp, 400, "手机号格式不正确")

        参数怎么给：
          code      业务 code（后端约定和 HTTP 状态码一致，都是 400）
          message   错误文案。三种给法：
                      "手机号格式不正确"        → **完全相等**（默认，跟老的 == 一致）
                      ["文案 A", "文案 B"]     → 属于其中之一（一个字段挂了两个约束时用）
                      None                     → 这条不验文案
          http      HTTP 状态码，默认 400（实测所有业务校验失败都是 400）。
                    401（没带 token）这种要显式传 http=401。
          contains  设 True 时改成"包含"比对 —— 只在文案很长、只关心关键词时用。
                    ⚠️ 默认是精确相等，别随手打开：那会让断言变弱，
                       "手机号格式不正确" 和 "手机号格式不正确，请重填" 都会被放过。

        ⚠️ 401 的响应体是**空的**，不是 JSON 信封（实测）。
           所以先看体是不是空的：空的就只验 HTTP 状态，不去 resp.json()。
           这种情况必须把 message 传 None，否则会冤枉后端。
        """
        assert resp.status_code == http, (
            f"期望失败（code={code}）：HTTP 实际 {resp.status_code}，"
            f"响应体 {(resp.text or '')[:300]}"
        )

        # 空响应体（实测 401 就是这种）没东西可验，到此为止。
        if not (resp.text or "").strip():
            assert message is None, (
                f"HTTP {http} 的响应体是空的，没有 message 可比 —— "
                f"要么把期望的文案去掉（传 None），要么这条不该验文案。"
            )
            return None

        try:
            body = resp.json()
        except ValueError:
            raise AssertionError(
                f"期望失败响应是 JSON，实际不是：{(resp.text or '')[:300]}"
            )

        assert body.get("code") == code, (
            f"业务 code 不符：期望 {code}，实际 {body.get('code')}，"
            f"message={body.get('message')!r}"
        )

        if message is None:
            return body

        actual = body.get("message") or ""
        # 候选集合：一个字段挂了两个约束时，后端报哪条由校验器顺序决定（实测会翻），
        # 这种情况只能接受"属于其中之一"。
        if isinstance(message, (list, tuple)):
            assert actual in message, (
                f"错误文案不符：期望属于 {list(message)} 之一，实际 {actual!r}"
            )
        elif contains:
            assert message in actual, (
                f"错误文案不符：期望包含 {message!r}，实际 {actual!r}"
            )
        else:
            assert actual == message, (
                f"错误文案不符：期望 {message!r}，实际 {actual!r}\n"
                f"→ 文案变了是**用户能看到的**输出变了。确认是有意改的，"
                f"就来改这里的期望值；否则是后端回归。"
            )
        return body

    # ==================== 鉴权专用 ====================
    @staticmethod
    def assert_forbidden(resp, msg="越权应被 403 拒绝"):
        """一行断定"这个请求被权限拦住了"，返回解析好的 body。

        ══ 为什么不能直接用 assert_error ══
        403 走的是**另一套响应体系**。业务错误（400）是统一信封：

            {"code": 400, "message": "手机号格式不正确"}

        而 403 是 Spring Security 在**进业务层之前**拦下的，给的是框架默认错误体：

            {"timestamp": "...", "status": 403, "error": "Forbidden", "path": "..."}

        里面**没有 code 也没有 message**。硬套 assert_error 只能两个参数都传 None，
        那这条断言就什么都没验 —— 名义上"统一了"，实际是空壳。

        ══ 那这里验什么才不是空壳 ══
        不验"格式对不对"（格式是缺陷，见下面的说明），验**安全上必须成立的三件事**：

          ① HTTP 必须是 403 —— 不是 200、不是 500。500 说明"崩了"而不是"拦住了"。
          ② 响应体里**不能有 data** —— 有 data 就是业务数据泄露。
             这条是真正有杀伤力的：哪天有人把权限判断从 Security 挪进业务层却写漏了
             返回分支，很可能返回 `{"code":403,"data":[用户列表]}`，只断 403 会放过。
          ③ 不能是 `code == 200` —— 那是越权**成功**了。

        ⚠️ 已知缺陷（接口覆盖矩阵 #10）：403 不走统一信封。
           这是**后端的问题，不是测试的问题**。所以这里不去断言"必须是 Spring 默认体"
           —— 那等于把缺陷当正确答案钉住。缺陷单独用一条 xfail 用例标记，
           修好那天会变 XPASS 提醒你（见 test_admin_authz.py 最后一节）。
        """
        assert resp.status_code == 403, (
            f"{msg}：期望 HTTP 403，实际 {resp.status_code}，"
            f"响应体 {(resp.text or '')[:400]}\n"
            f"→ 200 = 越权成功了（严重）；500/502 = 后端崩了或没起来；"
            f"404 = 路径写错，或后端先查存在性再查权限（会泄露 id 是否存在）。"
        )

        try:
            body = resp.json()
        except ValueError:
            raise AssertionError(
                f"{msg}：HTTP 403 但响应体不是 JSON：{(resp.text or '')[:300]}"
            )

        # ② 不泄露业务数据
        assert "data" not in body, (
            f"{msg}：被拒绝的响应里带了 data 字段，可能泄露了业务数据："
            f"{str(body.get('data'))[:300]}"
        )

        # ③ 不是"越权成功"
        assert body.get("code") != 200, (
            f"{msg}：HTTP 403 但业务 code=200，自相矛盾：{str(body)[:300]}"
        )
        return body
