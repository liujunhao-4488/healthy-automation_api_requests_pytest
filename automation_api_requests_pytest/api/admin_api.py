# api/admin_api.py
# 【接口层】管理端接口：5 个，全部只有 ROLE_ADMIN 能调。
#
# 跟别的 api 模块一样：**URL 只写在这个文件里**。
# 用例写 api.admin.list_users(headers=...) ，不出现任何路径。
#
# ============ 这 5 个接口是怎么来的 ============
# 不是从文档抄的，是从后端 Controller 里 grep 出来的（2026-10-28 实测）：
#   AdminOverviewController  @GetMapping("/overview")            → /admin/overview
#   UserController           @GetMapping("/admin/list")          → /user/admin/list
#   UserController           @PutMapping("/admin/{userId}/status")→ /user/admin/{id}/status
#   HealthArticleController  @GetMapping("/admin/collect-stats") → /article/admin/collect-stats
#   NotificationController   @PostMapping("/admin/publish")      → /notification/admin/publish
#
# ⚠️ 注意这几个接口**散落在 4 个不同的 Controller 里**，路径前缀都不一样
#    （/admin、/user/admin、/article/admin、/notification/admin）。
#    "管理接口"不是一个统一的模块，而是"分散在各处、靠注解限制角色"的一组接口 ——
#    所以鉴权测试只能一个个列出来，没法扫一个前缀搞定。


from .base_api_client import BaseApiClient


class AdminApi(BaseApiClient):

    def overview(self, headers=None):
        """GET /admin/overview —— 后台总览（用户数、今日活跃、热门食谱等）。

        响应结构很大（summary 14 个字段 + changes 5 个 + topRecipes 数组），
        **本次不给它写 schema**：鉴权矩阵关心的是"能不能进"，不是"进去后数据长什么样"。
        真要写，得先看后端是实时算的还是缓存的 —— 字段可能每次都不一样。
        """
        return self.get("/admin/overview", headers=headers)

    def list_users(self, headers=None):
        """GET /user/admin/list —— 全量用户列表（实测 258 条，**不分页，一次全给**）。

        ⚠️ 返回的是完整用户对象，**带 email 和 phone**。
           这正是它值得做越权测试的原因：一旦拦不住，整库用户的邮箱手机号就出去了。
        """
        return self.get("/user/admin/list", headers=headers)

    def set_user_status(self, user_id, status, headers=None):
        """PUT /user/admin/{userId}/status?status=0|1 —— 禁用(0)/启用(1) 某个用户。

        ⚠️ status 是 **URL 查询参数**，不是 JSON body（后端签名是 @RequestParam）。
           写成 json={"status": 0} 的话参数是 null，虽然权限测试仍然 403（拦在前面），
           但真拿 admin 去调会 400 —— 那就会让人误以为"权限有问题"。
        """
        return self.put(
            f"/user/admin/{user_id}/status",
            params={"status": status},
            headers=headers,
        )

    def collect_stats(self, headers=None):
        """GET /article/admin/collect-stats —— 文章收藏热度排行（实测返回数组）。"""
        return self.get("/article/admin/collect-stats", headers=headers)

    def publish_notification(self, data, headers=None):
        """POST /notification/admin/publish —— 向用户发布通知。

        ⚠️ 这是 5 个接口里唯一有**写副作用**的（会插一条通知）。
           越权测试用它必须确认"没插进去"，否则每跑一次测试就给所有用户
           推一条垃圾通知。
        """
        return self.post("/notification/admin/publish", json=data, headers=headers)
