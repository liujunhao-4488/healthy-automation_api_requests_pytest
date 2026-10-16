# test_cases/ai_assistant/test_assistant_通用问题不追问档案.py
# 【任务：AI 助手 · 画像装配（通用问题不该追问档案）】
# ══════════════════════════════════════════════════════════════════════════
# 背景（2026-10-14 修复，见 RecipeServiceImpl.buildIngredientAssistantSystemPrompt）：
#   原来基础 system prompt 无条件写死「请结合用户当前健康档案、饮食目标、过敏/忌口
#   和慢性病信息」，但**非 advice 调用根本不把画像塞进消息**——
#   于是模型一边被要求"结合档案"、一边手里没数据、又被自然 prompt 禁止提档案，
#   自相矛盾。实测会让模型反问「请告诉我你的身高体重」或凭空编一段档案（串味/档案回吐）。
#   修复：system prompt 里的"结合档案"一句改成**随画像有无一起进退**（hasProfile 参数）。
#
# 本文件锁的就是这个修复：**通用知识**问题（knowledge 意图，不带画像）→
# 回答里**不该**出现"追问用户档案 / 凭空提档案"的话术。
#
# 为什么重复问：断言的是"**从不**发生"，而模型是概率性的，单次采样证不了伪 ——
# 同 test_assistant_意图识别.py 第三节的 pass^k 思路。这里取 3 次（该现象发生率低，足够）。
#
# ⚠️ 跑这条需要后端是**带上本次修复的新 jar**，且 DeepSeek 可用：
#   旧 jar 上"结合档案"那句仍在，模型可能偶发追问，会误红；
#   模型不可用时回答是固定报错文案，不含追问话术，会假绿（这种情况由 source 前置断言兜底提示）。

import pytest

# 通用知识类问题：命中 knowledge 意图，正常流程不带画像。
GENERAL_KNOWLEDGE_QUESTIONS = [
    "鸡胸肉每100克大概多少卡路里",
    "菠菜为什么要焯水",
    "什么是食物的升糖指数",
]

# 回答里**不该出现**的"追问 / 编造档案"话术。
PROFILE_PROBING_PHRASES = [
    "请告诉我你的身高",
    "请告诉我你的体重",
    "方便告诉我你的",
    "请提供你的身高",
    "请提供你的体重",
    "请填写你的健康档案",
    "你目前还没有填写",
    "你还没有填写健康档案",
    "需要了解你的身高",
    "根据你目前的身高体重",
]

REPEAT_TIMES = 3


@pytest.mark.parametrize("question", GENERAL_KNOWLEDGE_QUESTIONS, ids=lambda q: q)
def test_general_question_does_not_probe_profile(ask, question):
    """通用知识问题 → 回答不该追问/编造用户档案，且真的在回答问题。"""
    violations = []
    last_text = ""
    for _ in range(REPEAT_TIMES):
        am = ask(question)["assistantMessage"]

        # 前置：这次得真的走到模型（不是被硬拦接走），否则断言对象错了，
        # 等于在测固定文案、永远绿。
        assert am.get("source") != "blocked", (
            f"「{question}」被本地硬拦接住了（source=blocked）—— 这条样本测不到模型行为了，"
            f"多半是关键词进了硬拦表，请换一条仍不在硬拦表里的通用问题。"
        )

        text = am.get("text", "")
        last_text = text
        hit = [w for w in PROFILE_PROBING_PHRASES if w in text]
        if hit:
            violations.append((hit, text))

    assert not violations, (
        f"问「{question}」（通用知识，本不该带画像）{REPEAT_TIMES} 次里有 "
        f"{len(violations)} 次出现了追问/编造档案的话术 —— 要求一次都不该有。\n"
        f"首次命中 {violations[0][0]}：{violations[0][1][:200]}"
    )

    # 顺带确认它真的在作答（不是空回 / 跑题），否则上面"没追问"可能只是因为模型啥也没说。
    assert len(last_text.strip()) >= 10, (
        f"问「{question}」的回答过短，疑似没正常作答：{last_text!r}"
    )
