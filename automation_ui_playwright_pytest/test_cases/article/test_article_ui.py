# test_cases/article/test_article_ui.py
# 健康知识 / 发布文章 / 文章详情 —— UGC 发布与互动
#
# 为什么这组必须存在：
#   发布是**用户可见的公开内容**（后端 publish 强制 status=1 直接上架），
#   它坏掉的后果比"我的食谱"严重得多 —— 全站用户都能看到一篇坏文章。
#   而接口层验不了这几件事：
#     · 发布按钮的 disabled 态（前端第一道闸）
#     · 发布成功后是不是真的跳到详情页、详情页读到的是不是刚发的内容
#     · 列表搜索能不能搜到新发的（写库成功但索引/列表没刷新）
#
# 数据卫生：
#   发出来的文章会真上架，用例结束必须删（cleanup.article，走 /article/delete）。
#   标题带唯一后缀，既保证"搜到的确实是我这篇"，也让清理能精确认领。

import re

from playwright.sync_api import expect

from common.cleanup import api
from common.seed import seed_article
from pages.article_detail_page import ArticleDetailPage
from pages.article_publish_page import ArticlePublishPage
from pages.knowledge_page import KnowledgePage


class TestPublish:
    def test_发布文章_跳详情页且列表可搜到(self, user_page, cleanup, unique):
        """主流程：填 → 发布 → 跳详情 → 详情标题正确 → 列表搜索能命中。

        为什么发布后要回头去列表搜一次：
          publish 成功只代表写库成功。分类/标签/状态这些字段如果映射错，
          文章会"存在但不上架"，详情页能打开（id 直查）、列表里搜不到 ——
          这是内容类系统最典型的一种半成功，只看详情页永远发现不了。
        """
        title = unique("自动化文章")

        pub = ArticlePublishPage(user_page).open()
        pub.expect_loaded()
        pub.fill_title(title)
        pub.fill_content(
            "这是一篇由 UI 自动化创建的文章，用于验证发布链路。\n"
            "核心结论：发布后应当立即上架，并且能在知识列表里被搜索到。"
        )
        pub.pick_category("营养知识")
        pub.add_tag("自动化")
        pub.publish()
        pub.expect_published()

        aid = pub.published_article_id()
        assert aid, "发布后 URL 里没有文章 id，跳转可能没发生"
        cleanup.article(aid)

        detail = ArticleDetailPage(user_page)
        detail.expect_loaded()
        assert detail.title() == title, "详情页标题和刚发布的不一致"

        knowledge = KnowledgePage(user_page).open()
        knowledge.expect_loaded()
        knowledge.search(title)
        knowledge.expect_title(title)

    def test_标题或正文为空_发布按钮不可点(self, user_page):
        """前端第一道闸：标题和正文都非空才允许点发布。

        三道断言对应 canSubmit 的三个状态：全空 → 只有标题 → 标题 + 正文。
        只测最后一步会漏掉"只有一个字段也放行"的回归。
        """
        pub = ArticlePublishPage(user_page).open()
        pub.expect_loaded()

        assert pub.publish_disabled(), "什么都没填，「发布」居然可点"

        pub.fill_title("只有标题没有正文")
        assert pub.publish_disabled(), "只有标题时不该放行"

        pub.fill_content("补上正文之后就应该可以发布了。")
        assert not pub.publish_disabled(), "标题和正文都填了，「发布」还是灰的"

    def test_标签超过8个_拦截提示且只保留8个(self, user_page):
        """标签上限 8 个，超出要明确提示、且列表不能真的多出第 9 个。

        这条是"限制类规则"的标准写法：既要提示，也要验结果。
        只验提示的话，提示弹了但标签照样进去了，用户会以为没加上。
        """
        pub = ArticlePublishPage(user_page).open()
        pub.expect_loaded()
        pub.fill_title("标签上限验证")
        pub.fill_content("用于验证标签数量上限的正文内容。")

        for i in range(8):
            pub.add_tag(f"标签{i}")

        pub.add_tag("第九个")
        pub.expect_rejected("最多添加 8 个标签")
        assert len(pub.tags()) == 8, f"超出上限后标签数变成 {len(pub.tags())} 个"


class TestArticleInteraction:
    def test_文章详情点赞_计数与状态同时变化(self, user_page, account, cleanup, unique):
        """点赞：按钮语义（点赞 ↔ 已点赞）和计数必须**同时**变。

        前端是乐观更新（先改本地再发请求），所以"状态翻了但计数没动"
        是真实存在的半更新缺陷。两个断言缺一不可。

        ⚠️ 文章是**用例自己发的**，不从知识列表里挑现成的：
          CI 的库是 schema + seed_test.sql 重建的，没有任何业务文章，
          列表为空 → "挑第一条"必然崩。自己造数据，用例就与环境解耦。

        跑完复位：点赞数会被所有人看到，不能因为跑了一次用例就 +1。
        复位走接口而不是再点一次（避免用例失败时点上没复位）。
        """
        title = unique("互动测试文章")
        aid = seed_article(account, title)
        cleanup.article(aid)

        detail = ArticleDetailPage(user_page).open(aid)
        detail.expect_loaded()
        assert detail.title() == title, "详情页打开的不是刚发的那篇"

        was_liked = detail.liked()
        before = detail.like_count()
        cleanup.task(
            lambda: api(
                "DELETE" if was_liked else "POST", f"/article/like/{aid}", account["token"]
            )
        )

        detail.toggle_like()
        detail.toast(re.compile("感谢点赞|已取消点赞"))

        if was_liked:
            assert not detail.liked(), "再点一次应该取消点赞"
            assert detail.like_count() == before - 1, "取消点赞后计数没减"
        else:
            assert detail.liked(), "点赞后按钮没变成「已点赞」"
            assert detail.like_count() == before + 1, "点赞后计数没加 1"
