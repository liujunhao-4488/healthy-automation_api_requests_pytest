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

from common.logger import log, short_url
from config.config import BASE_URL, TIMEOUT


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
        kwargs.setdefault("timeout", TIMEOUT)  # 没传超时就用统一值
        resp = self._session.get(self.base_url + path, **kwargs)
        self._log(resp)
        return resp

    def post(self, path, **kwargs):
        kwargs.setdefault("timeout", TIMEOUT)
        resp = self._session.post(self.base_url + path, **kwargs)
        self._log(resp)
        return resp

    def put(self, path, **kwargs):
        # 和 post 只差中间那一行（session.put / session.post）。
        # 这就是"请求能力集中在一处"的直接好处：加一种请求方式只要 4 行，
        # 所有接口类立刻都能用，用例那边一个字都不用动。
        kwargs.setdefault("timeout", TIMEOUT)
        resp = self._session.put(self.base_url + path, **kwargs)
        self._log(resp)
        return resp

    def delete(self, path, **kwargs):
        # 第四种动词。加它只花了 4 行 —— 这就是"请求能力集中在一处"的好处：
        # 加完所有接口类立刻都能用，用例那边一个字都不用改。
        kwargs.setdefault("timeout", TIMEOUT)
        resp = self._session.delete(self.base_url + path, **kwargs)
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
