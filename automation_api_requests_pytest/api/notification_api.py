# api/notification_api.py
# 【接口层】通知类接口：查自己的收件箱、标记已读、删除。
#
# 只有 3 个接口，而且全是"操作自己的通知"：
#   GET /notification/list
#   PUT /notification/read/{id}
#   PUT /notification/delete/{id}
# 发通知的 /notification/admin/publish 不在这个文件里 —— 那是管理接口，
# 放在 admin_api.py。为什么分开：一个普通用户能调，一个只有管理员能调，
# 混在一个类里会让"这个模块需不需要 admin"变得说不清。
#
# 本文件目前只服务于鉴权矩阵：越权发通知之后，用 list 去确认"真的没发出去"。

from .base_api_client import BaseApiClient


class NotificationApi(BaseApiClient):

    def list_mine(self, headers=None):
        """GET /notification/list —— 当前登录用户的通知列表（实测按时间倒序）。"""
        return self.get("/notification/list", headers=headers)

    def mark_read(self, notification_id, headers=None):
        """PUT /notification/read/{id} —— 标记某条通知已读。"""
        return self.put(f"/notification/read/{notification_id}", headers=headers)

    def delete(self, notification_id, headers=None):
        """PUT /notification/delete/{id} —— 删除某条通知。

        ⚠️ 是 PUT 不是 DELETE（后端签名就是 @PutMapping），别按 REST 直觉写。
           用 DELETE 方法打过去会得到 405。
        """
        return self.put(f"/notification/delete/{notification_id}", headers=headers)
