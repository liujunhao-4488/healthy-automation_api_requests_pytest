# api/auth_api.py
# 【接口层】认证类接口：登录 / 注册。
#
# 规矩就一条：**URL 只写在这个文件里**。
#   以后后端把 /auth/login 改成 /auth/signin，你只改下面那一行，用例一个字都不用动。
#   用例里再出现 "/auth/login" 这种字符串，就算违规（改路径时一定会漏改）。
#
# 为什么继承 BaseApiClient？
#   继承之后 `self.post(...)` 就能用 —— 发请求的能力（拼 BASE_URL、加超时）来自底座，
#   这个类只负责"记住有哪些接口、路径是什么"。

from .base_api_client import BaseApiClient


class AuthApi(BaseApiClient):
    # 这里故意没写 __init__：直接用底座继承来的那个（它会建 Session）。

    def login(self, data):
        """POST /auth/login —— 登录，成功时返回的 body 里带 token。

        data 是个字典，例如 {"email": "123456@qq.com", "password": "123456"}。
        """
        return self.post("/auth/login", json=data)

    def register(self, data):
        """POST /auth/register —— 注册。注册即登录，成功也直接返回 token。"""
        return self.post("/auth/register", json=data)
