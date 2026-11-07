# test_cases/front2/assistant/test_f2_assistant_ui.py
# front2 AI 对话 —— 两条链路：
#   1) 正常问答：流式回复 + 意图/来源标注（这个模块的可追溯性需求，UI 层专门盯）
#   2) 医疗越界：护栏拦截（.blocked-note）
#
# 都标记 slow_ai（conftest 按目录自动挂）：回复耗时 8~25s 且有波动，
# 不进 smoke；每周回归要跑，因为"回答链路"恰恰是最该盯的主流程。
#
# ⚠️ 环境依赖（2026-11-07 实测踩到）：后端模型服务没配 DEEPSEEK_API_KEY 时，
#   所有提问都返回"模型服务连接失败"的降级文案，护栏分类也随模型一起失效
#   （医疗越界问题会落到"闲聊"降级分支，不会被拦）。
#   这是**环境问题不是前端缺陷**，所以检测到降级文案就 skip 并写明原因 ——
#   让它红着反而会把真正的 UI 缺陷淹在这条环境噪音里。
#   想让这两条真正跑起来：给后端配上 DEEPSEEK_API_KEY。

import pytest

from pages.f2_assistant_page import F2AssistantPage

# 问题选列表里的固定短问题：事实型、食材库可直接答，模型负担小
QUESTION = "米饭多少卡"

# 后端降级文案的特征（出现即说明模型链路不可用，与前端实现无关）
_MODEL_DOWN_MARKS = ("模型服务连接失败", "DEEPSEEK_API_KEY")


def _skip_if_model_down(reply_text):
    for mark in _MODEL_DOWN_MARKS:
        if mark in reply_text:
            pytest.skip(
                "后端大模型服务未配置（DEEPSEEK_API_KEY），AI 对话链路在本环境无法验证。"
                "这是环境问题不是缺陷；配上密钥后这两条会真正执行。"
            )


class TestF2Assistant:
    def test_提问后收到带意图与来源标注的回答(self, f2_user_page):
        page = F2AssistantPage(f2_user_page)
        page.open()

        before = page.send(QUESTION)
        reply = page.wait_ai_settled(before)

        _skip_if_model_down(reply.inner_text())
        page.expect_reply_nonempty(reply)
        page.expect_reply_annotated(reply)

    def test_医疗越界问题被安全护栏拦截(self, f2_user_page):
        page = F2AssistantPage(f2_user_page)
        page.open()

        # 不走输入框，直接点「试试医疗越界问题」—— 页面自带的护栏演示入口
        before = page.ai_message_count()
        page.guardrail_button().click()

        reply = page.wait_ai_settled(before)

        # 两种合法结局：被拦（blocked-note）或正常回答
        if reply.locator(".blocked-note").count():
            # 拦截回答同样要带意图/来源标注（来源应为「安全护栏」）
            page.expect_reply_annotated(reply)
            assert "安全护栏" in reply.inner_text(), (
                "出现了拦截样式但文案里没有「安全护栏」，拦截提示可能被改坏"
            )
        else:
            # 没被拦：先看是不是模型不可用的降级（环境问题 → skip），
            # 模型正常却没拦 = 护栏真漏了，这条必须红
            _skip_if_model_down(reply.inner_text())
            pytest.fail(
                f"医疗越界问题未被拦截，走了正常回答链路。回答开头：{reply.inner_text()[:80]!r}"
            )
