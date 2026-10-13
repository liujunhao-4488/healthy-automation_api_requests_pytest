# test_cases/ai_assistant/test_assistant_安全拦截.py
# 【任务：AI 助手 · 输入安全拦截（代码硬拦）】
#
# ── 这个文件在测什么？──────────────────────────────────────────────
# 2026-10-12 后端新增了一道**代码硬拦**：命中安全规则就**不调模型**，
# 直接返回固定文案。它和同目录另外两个文件的分工 ——
#
#   · 结构 / 鉴权 / 参数校验        → test_assistant_结构鉴权.py
#   · 问什么该答什么（模型行为）     → test_assistant_意图识别.py
#   · **这句话压根不递到模型**       → 本文件
#
# 按"被测的关注点"切文件，不按"接口"切 —— 三个文件打的是同一个 URL，
# 但失败原因和要改的地方完全不同（改响应结构 / 改提示词 / 改正则）。
#
# ── 为什么这一类能"精确断言"？───────────────────────────────────────
# 因为它**不依赖模型**：同一句话问一百次，blocked 都一样，
# 于是可以写 `am["blocked"] == case["blocked"]`，精确相等、不留余地。
#
# 这正是 test_assistant_意图识别.py 那 8 条 skip（"意图观测不到、断不了"）的解法之一：
# 把"模型嘴里问不出来的东西"，搬到"代码里读得出来"。
#
# ⚠️ 代价要有意识：这道拦一生效，test_assistant_意图识别.py 里
#    「越界-写代码」那条 pass^5 哨兵，盯的就不再是"模型守不守规矩"，
#    而是"这几条正则对不对"了。模型行为那部分从此测不到 —— 换来的是确定性。
#    **两层是叠加的，不是替代的**：这里断"没递给模型"，那边断"递过去了它也不照做"。
#
# ── 数据从哪来？──────────────────────────────────────────────────
# data/assistant_guard_cases.yaml，**期望值全部来自实测**，不是照抄规则：
# 先在 2026-10-12 拿探针把同一份规则（当时写在前端）跑了一遍 24 条，
# 名字里带「误伤回归-*」的那批就是当时"期望放过、实际被拦"的样本。
# 规则修好后它们转正成回归用例 —— 以后谁把正则改松/改紧，这里立刻红。

import pytest

from common.data_loader import load_cases

GUARD_CASES = load_cases("assistant_guard_cases.yaml")

# 按"期望被拦 / 期望放过"切开。两类的观测点不同，断言方向也不同：
# 上者断"拦得对不对、是谁拦的"，下者断"**绝不该**被拦"。
BLOCK_CASES = [c for c in GUARD_CASES if c.get("blocked")]
PASS_CASES = [c for c in GUARD_CASES if not c.get("blocked")]

# 和后端 RecipeServiceImpl.MAX_PROMPT_LENGTH 对应。改一边要改两边 ——
# 这行故意写出来，就是为了让"两边对不上"看得见。
MAX_PROMPT_LENGTH = 1000


def case_id(case):
    """中文用例名 —— YAML 里的 name 字段。"""
    return case["name"]


# ==================== 一、该拦：命中规则就该本地拦下 ====================

@pytest.mark.parametrize("case", BLOCK_CASES, ids=case_id)
def test_harmful_or_offtopic_input_is_blocked(ask, case):
    """命中安全规则 → 该被**本地拦下**，而不是递给模型。

    两个断言要合起来看才立得住：

      · `blocked` == 预期的规则类型   → 拦得对不对（是 medical 还是 out_of_scope）
      · `source`  == "blocked"        → **是代码拦的，还是模型自己拒绝的**

    为什么第二个不能省：这两件事长得像、修法完全不同 ——
    "代码拦住了"要改正则（改 Java），"模型恰好也拒绝了"要改提示词（改字符串）。
    只断 blocked 字段的话，哪天有人把拦截挪回模型侧，用例照样绿。

    这一类**不花 token、也不等模型**（拦下来就返回了），所以可以放心多铺几条。
    """
    am = ask(case["question"])["assistantMessage"]

    assert am.get("blocked") == case["blocked"], (
        f"问「{case['question']}」期望拦成 {case['blocked']}，"
        f"实际 {am.get('blocked')!r}；回答开头：{am['text'][:120]}"
    )
    assert am.get("source") == "blocked", (
        f"「{case['question']}」被拦了，但 source 是 {am.get('source')!r} 而不是 'blocked' —— "
        f"分不清这句是代码拦下的，还是模型自己拒绝的"
    )


# ==================== 二、不该拦：正常饮食问题必须放行 ====================
# ⚠️ 这一类是真正容易出事的方向。拦住一句越界问题，最多算"没答好"；
#    拦住「早餐吃几片全麦面包合适」并把「请以医生的诊断和处方为准」甩给用户，
#    是**把正常用户挡在门外** —— 而且拦截是 100% 生效的，没有模型兜底。

@pytest.mark.parametrize("case", PASS_CASES, ids=case_id)
def test_normal_diet_question_is_not_blocked(ask, case):
    """正常饮食问题 → **绝不该**出现 blocked 字段。

    这里只断"没被拦"，不断回答内容 —— 回答好不好是
    test_assistant_意图识别.py 那边的事，一个观测点只归一个文件。

    ⚠️ 代价：没被拦就会**真的调模型**（每条约 2-5s、且花 token）。这类贵，
       所以数据文件里只留了必要的样本，别顺手往里加无关的话。
    """
    am = ask(case["question"])["assistantMessage"]

    assert am.get("blocked") is None, (
        f"「{case['question']}」是正常饮食问题，却被拦成 {am.get('blocked')}，"
        f"用户看到的是固定文案：{am['text'][:120]}"
    )


# ==================== 三、超长输入 ====================
# 单独写、不塞进 YAML：1001 个「营」放进数据文件里没人看得懂，
# 这里一行构造反而把意图说清楚了。

def test_overlong_input_is_blocked(ask):
    """超过 1000 字的输入 → 拦成 too_long（防刷接口）。"""
    am = ask("营" * (MAX_PROMPT_LENGTH + 1))["assistantMessage"]

    assert am.get("blocked") == "too_long", (
        f"{MAX_PROMPT_LENGTH + 1} 字的输入没被拦，实际 blocked={am.get('blocked')!r}"
    )
