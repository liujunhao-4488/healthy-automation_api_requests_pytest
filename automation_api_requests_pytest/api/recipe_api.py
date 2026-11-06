# api/recipe_api.py
# 【接口层】食谱类接口：读类 6 个 + 收藏四件套。
#
# 收藏四件套是这一批的重点，单独说明为什么值得放这儿：
#   它不是四个独立接口，而是**一个状态机**：
#       collect → status(collected=true) → list(在列表里) → uncollect → status(false)
#   单看任何一个接口都"返回 200 就对了"，串起来才能发现问题（比如收藏成功但列表看不到）。
#   所以接口层把这四个方法放在一起，用例那边就能一眼看出它们是一组。
#
# ⚠️ 读类接口 API.md 写"无需认证"，**实测全是 401**（缺陷 #1）。
#    这里仍然保留 headers 参数，因为实测要 token —— 文档是错的，以实测为准。

from .base_api_client import BaseApiClient


class RecipeApi(BaseApiClient):

    # ==================== 读类 ====================

    def list_all(self, headers=None):
        """GET /recipe/list —— 全部食谱。

        方法名不叫 list：那会遮住内置的 list()，在同一个类里
        `list(xxx)` 就会突然报 TypeError，很隐蔽。
        """
        return self.get("/recipe/list", headers=headers)

    def detail(self, recipe_id, headers=None):
        """GET /recipe/detail/{id} —— 食谱详情。

        ⚠️ data 是**嵌套对象**，不是扁平食谱：
               {"recipe": {...}, "ingredients": [...]}
           所以别写 body["data"]["name"]，要写 body["data"]["recipe"]["name"]。
           ingredients 是 recipe_ingredient 关联出来的食材行（含用量/单位）。

        ⚠️ id 不存在时**不报错**：200 + {"recipe": null, "ingredients": []}。
           前端必须自己判 recipe 是否为 null，光看 code=200 会以为拿到了详情。
           （对照：/article/detail 不存在时是 400「文章不存在」—— 同类接口两种风格。）
        """
        return self.get(f"/recipe/detail/{recipe_id}", headers=headers)

    def search(self, keyword, headers=None):
        """GET /recipe/search?keyword= —— 按关键字搜索。

        ⚠️ keyword 为空时不要传 None：后端要的是**参数存在**，
           传 None 会拼成 `keyword=`（空串），后端仍拒绝；
           而完全不传这个参数会得到 Spring 默认错误体（缺陷 #2）。
        """
        return self.get("/recipe/search", params={"keyword": keyword}, headers=headers)

    def search_without_keyword(self, headers=None):
        """GET /recipe/search 且**不带** keyword —— 专为验证缺陷 #2 留的入口。

        正常业务不会这么调，但"参数漏传时后端返回什么"是个真实的健壮性问题：
        API.md 承诺统一信封，实测这里给的是 Spring 默认错误体。
        """
        return self.get("/recipe/search", headers=headers)

    def nutrition(self, recipe_id, headers=None):
        """GET /recipe/nutrition/{id} —— 食谱营养分析。"""
        return self.get(f"/recipe/nutrition/{recipe_id}", headers=headers)

    def custom(self, headers=None):
        """GET /recipe/custom —— 当前用户的自定义食谱。"""
        return self.get("/recipe/custom", headers=headers)

    # ==================== 收藏四件套 ====================

    def collect(self, recipe_id, headers=None):
        """POST /recipe/collect/{recipeId} —— 收藏。

        实测**幂等**：重复收藏仍 200，collectCount 不会累加（靠 uk_user_recipe 唯一键兜住）。
        这一点值得钉住 —— 前端双击收藏按钮是很常见的操作。
        """
        return self.post(f"/recipe/collect/{recipe_id}", headers=headers)

    def uncollect(self, recipe_id, headers=None):
        """DELETE /recipe/collect/{recipeId} —— 取消收藏。实测同样幂等。"""
        return self.delete(f"/recipe/collect/{recipe_id}", headers=headers)

    def collect_status(self, recipe_id, headers=None):
        """GET /recipe/collect/status/{recipeId} —— 收藏状态。

        返回 data 是**两个字段的组合**，别只取一个：
            {"collectCount": 3, "collected": true}
        ⚠️ 两者语义不同，写断言时最容易搞混：
           collected    = **我**有没有收藏（跟 token 走，因人而异）
           collectCount = **全站**有多少人收藏（所有人看到的是同一个数）
        实测证据：A 收藏后，B 查同一个 recipeId 得到 {"collectCount":1,"collected":false}。
        """
        return self.get(f"/recipe/collect/status/{recipe_id}", headers=headers)

    def collect_list(self, headers=None):
        """GET /recipe/collect/list —— 我的收藏列表（实测是完整食谱对象数组，不是 id 数组）。"""
        return self.get("/recipe/collect/list", headers=headers)
