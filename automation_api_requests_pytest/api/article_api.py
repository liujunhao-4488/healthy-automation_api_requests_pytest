# api/article_api.py
# 【接口层】健康文章的**读类**接口。
#
# 只收 5 个读接口，写类（点赞/收藏/评论/发布）刻意没进来 ——
# 它们在覆盖矩阵里是 P1/P2，且需要"文章存在"这个前提，
# 而测试库的 health_article 是空表（实测 0 篇）。没有靶子就写不了有意义的断言，
# 硬写只能写"返回 200 就算过"，那种用例的价值是负的（占着绿灯不说，还让人以为测过）。
# 详见覆盖矩阵 §三 C 档。
#
# ⭐ 这个模块的价值在于它和 /record/list **风格不统一**，值得用契约用例钉住：
#       /article/list  → data = {total, pageSize, page, list, tags}   ← 标准分页对象
#       /record/list   → data = [ ... ]                                ← 裸数组
#   以后谁要统一响应格式，就有据可依；不统一也没关系，但要**知道**它不统一。

from .base_api_client import BaseApiClient


class ArticleApi(BaseApiClient):

    def list_articles(self, page=1, page_size=10, headers=None):
        """GET /article/list —— 分页文章列表。

        data 是分页对象：{"total": 0, "pageSize": 10, "page": 1, "list": [], "tags": []}
        注意它和 /record/list 不一样（那边是裸数组），解析函数不能混用。
        """
        return self.get("/article/list", params={"page": page, "pageSize": page_size},
                        headers=headers)

    def tags(self, headers=None):
        """GET /article/tags —— 全部标签。测试库空表时返回 []。"""
        return self.get("/article/tags", headers=headers)

    def detail(self, article_id, headers=None):
        """GET /article/detail/{articleId} —— 文章详情。

        文章不存在时是**业务 400「文章不存在」**（统一信封），
        不是 404 —— 写断言别按 REST 直觉写 404。
        """
        return self.get(f"/article/detail/{article_id}", headers=headers)

    def search(self, keyword, headers=None):
        """GET /article/search?keyword= —— 搜索。

        ⚠️ 返回结构和 /article/list **完全一样**（分页对象），
           不是"搜索结果数组"。所以这两个接口可以共用一个解析函数。
        """
        return self.get("/article/search", params={"keyword": keyword}, headers=headers)

    def comments(self, article_id, headers=None):
        """GET /article/comment/list/{articleId} —— 评论（实测是扁平数组，不是嵌套树）。

        ⚠️ API.md 说"评论树"，实测返回的是平铺列表 —— 说明父评论关系
           要么在字段里（parentId），要么后端没做嵌套。测试库空表，
           暂时无法确认是哪种。这里先按"数组"断，等有数据再补。
        """
        return self.get(f"/article/comment/list/{article_id}", headers=headers)

    def search_without_keyword(self, headers=None):
        """GET /article/search 且**不带** keyword —— 专为验证缺陷 #21 留的入口。

        同 /recipe/search（缺陷 #2）、/ingredient/search：期望统一信封，
        实测是 Spring 默认错误体。三个接口一个毛病。
        """
        return self.get("/article/search", headers=headers)
