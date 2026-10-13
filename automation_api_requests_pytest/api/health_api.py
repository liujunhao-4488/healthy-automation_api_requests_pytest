# api/health_api.py
# 【接口层】健康类接口：健康档案（info）与饮食目标（goal），各有 GET 读 / POST 存，
#   外加一个 GET /health/history 读历史。
#
# 跟 auth_api.py / user_api.py 一样的规矩：**URL 只写在这个文件里**。
#
# 这个模块有个新东西：**POST 是 upsert（有则更新、无则新增）**。
#   · 第一次 POST → 库里插一条新记录；
#   · 再 POST → 更新同一条（id 不变），不是插第二条。
#   所以 POST 是**写操作**，用例要拿临时靶子账号跑，别污染测试账号。
#
# 另一个要记住的点：**GET /health/info 的 analysis 在信封顶层**，
#   不在 data 里 —— 即 body["analysis"]，不是 body["data"]["analysis"]。
#   这是后端 controller 直接 response.put("analysis", ...) 造成的（见 HealthInfoController）。

from .base_api_client import BaseApiClient


class HealthApi(BaseApiClient):

    # ---- 健康档案 ----

    def get_info(self, headers=None):
        """GET /health/info —— 读当前用户的健康档案（需要 token）。

        没建档时 data 为 null；无论有没有档案，信封顶层都有 analysis。
        """
        return self.get("/health/info", headers=headers)

    def save_info(self, data, headers=None):
        """POST /health/info —— 新增或更新健康档案（upsert，需要 token）。

        data 必填：age / gender / height / weight（其余字段可选）。
        """
        return self.post("/health/info", json=data, headers=headers)

    def get_history(self, headers=None):
        """GET /health/history —— 读健康档案历史（每次 POST /health/info 追加一条）。"""
        return self.get("/health/history", headers=headers)

    # ---- 饮食目标 ----

    def get_goal(self, headers=None):
        """GET /health/goal —— 读当前用户的饮食目标（需要 token）。未设置时 data 为 null。"""
        return self.get("/health/goal", headers=headers)

    def save_goal(self, data, headers=None):
        """POST /health/goal —— 新增或更新饮食目标（upsert，需要 token）。

        data 必填：goalType / targetCalories / startDate（endDate 可选）。
        """
        return self.post("/health/goal", json=data, headers=headers)
