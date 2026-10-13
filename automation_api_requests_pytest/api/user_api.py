# api/user_api.py
# 【接口层】用户类接口：个人资料（GET 读 / PUT 改）。
#
# 跟 auth_api.py 一样的规矩：**URL 只写在这个文件里**。
# 用例拿到的永远是 api.user.get_profile(...) / api.user.update_profile(...)，
# 后端哪天把 /user/profile 改个路径，只改这里一处，用例不用动。
#
# 这个模块有个新东西：**它要 token**（/user/profile 必须登录才能访问）。
#   做法不是把 token 硬编在这里，而是让调用方通过 headers 传进来 ——
#   谁有 token、token 从哪来，是用例/conftest 的事，接口层只负责"怎么发请求"。

from .base_api_client import BaseApiClient


class UserApi(BaseApiClient):

    def get_profile(self, headers=None):
        """GET /user/profile —— 读取当前登录用户的资料（需要 token）。

        headers 就是 {"Authorization": "Bearer xxx"}，
        由 conftest.py 的 auth_headers 夹具递进来。
        """
        return self.get("/user/profile", headers=headers)

    def update_profile(self, data, headers=None):
        """PUT /user/profile —— 局部更新资料（username / phone / avatar）。

        ⚠️ 局部更新的意思：data 里**没写的字段 = 不改**。
           所以 {"username": "新名"} 只会动用户名，手机号/头像原封不动。
        """
        return self.put("/user/profile", json=data, headers=headers)
