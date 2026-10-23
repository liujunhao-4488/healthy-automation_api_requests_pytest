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
            98 条用例一行都不用改，报告里天然带完整现场。
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
    def assert_ok(resp, msg="接口应成功"):
        """一行断定"接口成功"：HTTP 200 且业务 code==200，返回解析好的 body。

        只用于"期望成功"的调用；期望失败的用例要自己写断言。

        为什么是 staticmethod？因为它只做一件事 —— 检查传进来的这个响应，
        跟"谁发的请求、用哪个 client 发的"毫无关系。不写 self 反而更诚实，
        也让 api/__init__.py 的总入口能直接把它借过去用。
        """
        assert resp.status_code == 200, f"{msg}：HTTP {resp.status_code}"
        body = resp.json()
        assert body["code"] == 200, f"{msg}：code={body.get('code')}，message={body.get('message')}"
        return body
