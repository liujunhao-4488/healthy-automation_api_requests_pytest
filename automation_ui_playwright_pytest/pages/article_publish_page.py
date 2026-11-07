# pages/article_publish_page.py
# 发布文章（front2/src/views/ArticlePublishView.vue）
#
# 这是**用户产生内容的入口**，和食谱库那套"自己可见"不同：
# 后端 /article/publish 发布即上架（status 强制 1），所以：
#   · 用例建的文章会出现在所有人的知识列表里 —— 必须清理（common/cleanup.py）
#   · 标题里带唯一后缀，方便断言"确实是我这篇"，也方便清理时识别
#
# 前端有两道闸：
#   ① 发布按钮的 disabled 绑定 canSubmit（标题 + 正文非空）
#   ② submit() 里再校验一次并弹 toast
# 两道闸都要测：disabled 是第一道（用户根本点不下去），
# toast 是第二道（万一 disabled 逻辑被改坏，还有兜底）。

import re

from playwright.sync_api import expect

from config.config import EXPECT_TIMEOUT
from pages.base_page import BasePage


class ArticlePublishPage(BasePage):
    path = "/knowledge/new"

    def expect_loaded(self, timeout=EXPECT_TIMEOUT):
        expect(self.page.get_by_role("heading", name="发布文章", exact=True)).to_be_visible(
            timeout=timeout
        )
        return self

    # ---------------- 表单 ----------------

    @property
    def title_input(self):
        return self.page.get_by_placeholder("例如：减脂期怎么吃主食才不容易饿")

    @property
    def content_input(self):
        return self.page.get_by_placeholder(
            "支持换行分段。建议先用一句话说结论，再展开原因和具体做法。"
        )

    @property
    def tag_input(self):
        # 第一个标签加进去后 placeholder 会变成「继续添加」，所以按类名取
        return self.page.locator(".tag-input")

    def fill_title(self, text):
        self.title_input.fill(text)
        return self

    def fill_content(self, text):
        self.content_input.fill(text)
        return self

    def pick_category(self, name):
        """选分类（chip）。分类卡片的 h3 是「分类与标签」，圈住它再找按钮。"""
        card = self.page.locator("article.card").filter(
            has=self.page.get_by_role("heading", name="分类与标签", exact=True)
        ).first
        card.get_by_role("button", name=name, exact=True).click()
        return self

    def add_tag(self, text):
        """加标签：输入 + 回车（前端 @keydown 里处理 Enter/逗号）。"""
        self.tag_input.fill(text)
        self.tag_input.press("Enter")
        return self

    def tags(self):
        return [el.inner_text().strip().replace("×", "").strip()
                for el in self.page.locator(".tag-pill").all()]

    # ---------------- 提交 ----------------

    @property
    def publish_button(self):
        """页头那颗「发布」（页脚还有一颗「发布文章」，用 exact 区分）。"""
        return self.page.locator(".page-actions").get_by_role(
            "button", name=re.compile(r"^发布$|^发布中$")
        ).first

    def publish_disabled(self):
        return self.publish_button.is_disabled()

    def publish(self):
        self.publish_button.click()
        return self

    def expect_published(self, timeout=EXPECT_TIMEOUT):
        """发布成功的判据：提示「文章已发布并上架」+ URL 跳到详情页。

        不写死跳转目标 id（服务端生成），只断言路径形状 /knowledge/<数字>。
        """
        self.toast("文章已发布并上架", timeout=timeout)
        expect(self.page).to_have_url(re.compile(r"/knowledge/\d+"), timeout=timeout)
        return self

    def published_article_id(self):
        """从当前 URL 里取文章 id（跳转后调用），给清理用。"""
        m = re.search(r"/knowledge/(\d+)", self.page.url)
        return int(m.group(1)) if m else None
