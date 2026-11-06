# api/ingredient_api.py
# 【接口层】食材类读接口：列表 / 详情 / 按分类 / 搜索。
#
# 只有读，没有写：/ingredient/save|update|delete 是**管理员**接口，
# 但它们不挂在 /admin 路径下（同一个 Controller 里的角色判断），
# 所以扫 /admin 扫不到 —— 这三个的鉴权在 test_cases/admin 里统一处理，
# 不放这个文件，避免"这个模块要不要 admin"说不清（同 notification_api 的划分理由）。
#
# ⚠️ API.md 写"无需认证"，实测**要 token**（缺陷 #1，和 /recipe/* 一回事）。

from .base_api_client import BaseApiClient


class IngredientApi(BaseApiClient):

    def list_all(self, headers=None):
        """GET /ingredient/list —— 全部食材。实测测试库 125 条，无分页。"""
        return self.get("/ingredient/list", headers=headers)

    def detail(self, ingredient_id, headers=None):
        """GET /ingredient/detail/{id} —— 单个食材的营养成分（每 100g）。"""
        return self.get(f"/ingredient/detail/{ingredient_id}", headers=headers)

    def by_category(self, category, headers=None):
        """GET /ingredient/category/{category} —— 按分类取，分类值用中文（如「蔬菜」「肉类」）。

        ⚠️ 分类是**路径参数**，中文要 URL 编码。requests 的 params 不管路径，
           所以这里交给 requests 自己处理 —— 实测传中文能正常返回，
           不用手动 quote（这行注释是给"想手动 urllib.parse.quote 的人"看的：
           手动编一次会被再编一次，变成 %25E8%2594%25AC... 然后查不到）。
        """
        return self.get(f"/ingredient/category/{category}", headers=headers)

    def search(self, keyword, headers=None):
        """GET /ingredient/search?keyword= —— 按关键字搜索（中英文都行）。"""
        return self.get("/ingredient/search", params={"keyword": keyword}, headers=headers)

    def search_without_keyword(self, headers=None):
        """GET /ingredient/search 且**不带** keyword —— 专为验证缺陷 #21 留的入口。

        正常业务不会这么调，但"缺必填 query param 时返回什么"是真实的健壮性问题：
        期望统一信封 {code,message}，实测是 Spring 默认错误体 {timestamp,status,error,path}。
        同 /recipe/search（缺陷 #2）、/article/search 一模一样。
        """
        return self.get("/ingredient/search", headers=headers)
