# api/__init__.py
# 接口层的**总入口**：用例里从此写 `api.auth.login(...)`，不再写 URL。
#
# 它只干一件事：把各个接口模块挂到自己身上。
#
# ⚠️ 关键决定：**Api 故意不继承 BaseApiClient。**
#   以前那版让 Api 继承了底座，结果 api.post("/随便什么路径") 也能跑通 ——
#   URL 就又多了一条偷偷漏回用例的路（而且不报错，很难发现）。
#   现在不继承：你在用例里写 api.post("/x") 会直接报 AttributeError，
#   路径想漏都漏不出去 —— 这条防线是"结构上不给"，比"约定上不写"硬。

from .assistant_api import AssistantApi
from .admin_api import AdminApi
from .auth_api import AuthApi
from .base_api_client import BaseApiClient
from .health_api import HealthApi
from .kb_api import KbApi
from .notification_api import NotificationApi
from .user_api import UserApi


class Api:
    def __init__(self):
        self.auth = AuthApi()            # 用例里：api.auth.login(...)
        self.user = UserApi()            # 用例里：api.user.get_profile(...)
        self.health = HealthApi()        # 用例里：api.health.get_info(...)
        self.assistant = AssistantApi()  # 用例里：api.assistant.chat(...)
        # ⚠️ 它打在算法服务（Flask 5000）上，不是 Java 后端 —— 见 kb_api.py 顶部说明
        self.kb = KbApi()                # 用例里：api.kb.search("高血压怎么吃")
        # 只有 ROLE_ADMIN 能调，普通用户一律 403 —— 见 admin_api.py 顶部说明
        self.admin = AdminApi()          # 用例里：api.admin.list_users(headers=...)
        # 只操作自己的通知，发通知在 admin 里 —— 见 notification_api.py 顶部说明
        self.notification = NotificationApi()  # 用例里：api.notification.list_mine(...)

    def assert_ok(self, resp, msg="接口应成功", schema=None):
        """把底座的判定器借过来（用例里 api.assert_ok(resp) 照旧能用）。

        判定器不属于任何一个具体接口，所以不挂在 self.auth 下面，而是放在总入口。

        schema 是可选参数：传了就顺带校验整份响应的结构（字段缺失 / 类型 / 枚举），
        不传行为和以前完全一致。schema 从 common/schemas.py 拿。
        """
        return BaseApiClient.assert_ok(resp, msg, schema=schema)

    def assert_error(self, resp, code, message=None, http=400, contains=False):
        """错误场景判定器 —— 替代手写的 HTTP / code / message 三层断言。

        用例里：api.assert_error(resp, 400, "手机号格式不正确")
        参数说明见 BaseApiClient.assert_error。
        """
        return BaseApiClient.assert_error(resp, code, message, http=http, contains=contains)

    def assert_forbidden(self, resp, msg="越权应被 403 拒绝"):
        """越权判定器 —— 专门断"权限拦住了"。

        用例里：api.assert_forbidden(resp)

        ⚠️ 它和 assert_error 是**两个东西**，不是重复：
           业务失败（400）走统一信封，有 code 和 message；
           权限拒绝（403）是 Spring Security 在业务层之前拦的，给的是框架默认错误体，
           **里面没有 code 也没有 message**。两套响应体系，得两把尺子。
           详细理由见 BaseApiClient.assert_forbidden 的注释。
        """
        return BaseApiClient.assert_forbidden(resp, msg)
