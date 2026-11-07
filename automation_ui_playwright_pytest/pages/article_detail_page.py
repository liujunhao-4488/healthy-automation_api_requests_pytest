# pages/article_detail_page.py
# 文章详情（front2/src/views/ArticleDetailView.vue）
#
# 互动三件事：收藏 / 点赞 / 评论。共同点都是"乐观更新 + 失败回滚"：
# 前端先改本地 store 和计数，接口失败才弹错误提示。
# 所以断言必须同时看**按钮语义**（点赞 → 已点赞）和**计数**（+1），
# 只看其中一个，遇到"状态翻了但计数没动"这种半更新缺陷会漏。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT
from pages.base_page import BasePage


class ArticleDetailPage(BasePage):
    path = "/knowledge"

    def open(self, article_id, wait_until="domcontentloaded"):
        return super().open(f"/knowledge/{article_id}", wait_until=wait_until)

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        expect(self.page.locator("h1.page-title")).to_be_visible(timeout=timeout)
        return self

    def title(self):
        return self.page.locator("h1.page-title").inner_text().strip()

    def article_id(self):
        """从 URL 取文章 id（/knowledge/123 → 123），给清理和互动复位用。"""
        m = re.search(r"/knowledge/(\d+)", self.page.url)
        return int(m.group(1)) if m else None

    # ---------------- 点赞 ----------------

    @property
    def like_button(self):
        """点赞按钮。文案是「点赞 1,234」/「已点赞 1,235」，计数藏在可访问名里。"""
        return self.page.locator(".page-actions").get_by_role(
            "button", name=re.compile(r"^(已点赞|点赞)\s*[\d,]+$")
        ).first

    def like_count(self):
        text = self.like_button.inner_text()
        digits = re.search(r"([\d,]+)", text)
        return int(digits.group(1).replace(",", "")) if digits else 0

    def liked(self):
        return "已点赞" in self.like_button.inner_text()

    def toggle_like(self):
        self.like_button.click()
        return self

    # ---------------- 收藏 ----------------

    @property
    def collect_button(self):
        return self.page.locator(".page-actions").get_by_role(
            "button", name=re.compile(r"^(已收藏|收藏)$")
        ).first

    def collected(self):
        return "已收藏" in self.collect_button.inner_text()

    def toggle_collect(self):
        self.collect_button.click()
        return self

    # ---------------- 评论 ----------------

    def comment(self, text):
        self.page.get_by_placeholder("说说你的看法或想了解的问题…").fill(text)
        self.page.get_by_role("button", name=re.compile("发布评论|发布中")).click()
        return self

    def comment_count(self):
        """标题里那个数字：「评论 3」。"""
        text = self.page.locator("h3").filter(has_text="评论").first.inner_text()
        m = re.search(r"(\d+)", text.replace("评论", ""))
        return int(m.group(1)) if m else 0

    def comment_texts(self):
        return [el.inner_text().strip() for el in self.page.locator(".comment-bd").all()]
