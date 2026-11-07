# pages/knowledge_page.py
# 健康知识列表（front2/src/views/KnowledgeView.vue）
#
# 搜索是**服务端分页 + 前端 debounce**（@input 后 300ms 左右才发请求），
# 所以断言"列表里出现/不出现某条"之前，必须等列表真的刷新完 ——
# 直接 fill 完就 count() 会读到旧的 DOM，是这类搜索用例最常见的假失败。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT
from pages.base_page import BasePage


class KnowledgePage(BasePage):
    path = "/knowledge"

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        expect(self.page.get_by_role("heading", name="健康知识", exact=True)).to_be_visible(
            timeout=timeout
        )
        return self

    @property
    def search_input(self):
        return self.page.get_by_placeholder("搜索标题或摘要")

    def search(self, keyword, timeout=EXPECT_TIMEOUT):
        """搜索并等结果落定。

        等的判据用「列表内容不再变化」不现实，退而求其次：
        等"至少有一张卡"或"出现空态"——两者之一必现，
        能覆盖绝大多数情况；关键词搜不到时命中空态分支。
        """
        self.search_input.fill(keyword)
        expect(
            self.page.locator("article.article-card, .empty").first
        ).to_be_visible(timeout=timeout)
        return self

    def titles(self):
        return [el.inner_text().strip() for el in self.page.locator("article.article-card h3").all()]

    def expect_title(self, keyword, timeout=EXPECT_TIMEOUT):
        """等某条标题出现在列表里。

        为什么不用 has_title（瞬时快照）：搜索是 debounce + 服务端分页，
        fill 完那一瞬间列表还是上一次的结果，快照断言必然假失败。
        等它出现才是对的判据。
        """
        expect(
            self.page.locator("article.article-card h3").filter(has_text=keyword).first
        ).to_be_visible(timeout=timeout)
        return self

    def has_title(self, keyword):
        return any(keyword in t for t in self.titles())

    def open_article(self, title):
        """点卡片标题进详情。

        用链接的可访问名精确匹配：卡片标题里的文字可能带前后空白，
        但可访问名会做归一化，比 has_text 正则锚点稳（这个坑在登录页已经踩过）。
        """
        self.page.get_by_role("link", name=title, exact=True).first.click()
        expect(self.page).to_have_url(re.compile(r"/knowledge/\d+"), timeout=EXPECT_TIMEOUT)
        return self

    @property
    def publish_entry(self):
        return self.page.get_by_role("link", name=re.compile("发布文章"))
