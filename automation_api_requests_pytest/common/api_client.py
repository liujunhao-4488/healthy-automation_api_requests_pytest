# common/api_client.py
# 这是一个"请求客户端"——对 requests 的薄封装。
#
# 为什么需要它？看你现在每个用例都在重复三件事：
#   1) 拼完整地址：BASE_URL + "/recipe/list"
#   2) 发请求后自己 resp.json() 解析
#   3) 判断业务成功：body["code"] == 200
# 重复代码越多，越容易写错、越难改。把它们收进一个类，用例就清爽了。
#
# 类比：以前你每次做菜都要"生火+热锅+倒油"，现在把这些变成一口"自动锅"，
#       你只管"放食材、按开关"。

import requests

from config import BASE_URL, TIMEOUT


class ApiClient:
    """封装好的接口测试客户端。"""

    def __init__(self):
        # Session 复用连接，比每条用例新建连接快
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    # ---- 下面是"发请求"的方法，path 只写相对路径（不含 BASE_URL）----

    def get(self, path, **kwargs):
        kwargs.setdefault("timeout", TIMEOUT)  # 没传超时就用工地统一的超时
        return self._session.get(BASE_URL + path, **kwargs)

    def post(self, path, **kwargs):
        kwargs.setdefault("timeout", TIMEOUT)
        return self._session.post(BASE_URL + path, **kwargs)

    def put(self, path, **kwargs):
        kwargs.setdefault("timeout", TIMEOUT)
        return self._session.put(BASE_URL + path, **kwargs)

    def delete(self, path, **kwargs):
        kwargs.setdefault("timeout", TIMEOUT)
        return self._session.delete(BASE_URL + path, **kwargs)

    # ---- 下面是"判结果"的方法 ----

    def assert_ok(self, resp, msg="接口应成功"):
        """一行断定"接口成功"：HTTP 200 且 业务 code==200。

        返回解析好的 body，方便你接着断言 data 里的内容。
        用法：body = api.assert_ok(resp)
        """
        assert resp.status_code == 200, f"{msg}：HTTP 状态码是 {resp.status_code}"
        body = resp.json()
        assert body["code"] == 200, (
            f"{msg}：业务 code={body.get('code')}，消息={body.get('message')}"
        )
        return body
