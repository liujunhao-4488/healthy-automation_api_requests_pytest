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

    # ==================== 饮食偏好（2026-11-06 新增）====================
    #
    # 为什么它值得单独两个方法：这两个接口是**唯一能改饮食偏好的入口**，
    # 而饮食偏好直接影响推荐结果（/recommend/* 吃它）。改错了没有任何报错，
    # 只是推荐变得莫名其妙 —— 这种"静默错误"只能靠接口层钉住。

    def get_diet_preference(self, headers=None):
        """GET /user/diet-preference —— 读当前用户的饮食偏好。

        ⚠️ 新注册用户**没有**这行数据，但接口不报 404，而是返回一个"空壳"：
               {"id": null, "userId": ..., "dietType": null, ...,
                "mealFrequency": 3, "snackPreference": 1}
           id 为 null 说明库里还没这行；两个非空值是 DTO 的默认值。
           所以"有没有偏好"要看 id 是不是 null，不能看字段是否为 null。
        """
        return self.get("/user/diet-preference", headers=headers)

    def update_diet_preference(self, data, headers=None):
        """PUT /user/diet-preference —— 更新饮食偏好（局部更新：没写的字段不改）。

        🔴 **这个接口的响应体不能当"更新后的状态"用**（缺陷 #16）。
           实测：先存 allergies="海鲜"，再 PUT 只带 {"dietType":"低碳水"}，
           响应里 allergies 是 **null**，但库里、以及紧接着的 GET 里都还是"海鲜"。
           也就是说响应体是"请求 DTO 拼出来的回显"，不是查库后的真实值。
           前端如果拿它直接渲染，用户会看到过敏原被清空了。

           写用例时必须 **PUT 完再 GET 一次** 才看得到真值 ——
           这条不是洁癖，是这接口本身的行为决定的。
        """
        return self.put("/user/diet-preference", json=data, headers=headers)
