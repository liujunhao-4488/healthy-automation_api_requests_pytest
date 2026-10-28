# test_cases/ai_assistant/test_assistant_越狱.py
# 【任务：AI 助手 · 安全对抗（越狱）】
# ══ 这个文件的分工 ═════════════════════════════════════════════
#
#   和 test_assistant_意图识别.py 的区别（就一句）：
#     · 那个问"普通用户问正常问题，它答得对不对"；
#     · 这个问"用户**故意**绕，它守不守得住"。
#
#   数据来自 data/assistant_jailbreak_cases.yaml（21 条）：
#     B1 用药剂量 8 / B2 高风险情形 5 / B3 极端减重 6 / B4 越界任务 2，
#     其中有 3 条是**多轮**攻击 —— 单轮提问集永远测不出那一类。
#
#   它还有个"前身"：tools/reports/jailbreak_report.py。那个是一次性**报告**脚本
#   （跑一遍、导出 Excel、给人看）；本文件把它变成**能天天跑的回归**。
#   两者不重复：报告负责"量稳定性 / 校准词表"，用例负责"每次改动后自动拦一道"。
#
# ══ 判据从哪来：不重写，直接复用 ═════════════════════════════════
#   ⚠️ 关键决定：import tools.reports.jailbreak_report 的 judge()，**不在这里重写一份**。
#   为什么：越狱判据（breach / guard / verdict 三件套）是校准了 3 轮才定下来的；
#   两处各存一份，必然像前后端词表那样慢慢漂移（这个项目已经栽过一次）。
#   只有一份，改也只改 tools 那一份。pytest.ini 里有 pythonpath = . ，
#   所以这里能直接 import 项目根下的模块。
#
#   ⚠️ 但数据文件开头有一句话必须守住：
#     "**不要**拿这份词表直接写 assert …… 越狱判据的误报率天然高于普通接口断言"
#   本文件绕开这个坑的办法：把断言拆成"严的"和"松的"两道 —— 见下。
#
# ══ 一条用例、两道断言 ═════════════════════════════════════════
#   ① 前置断言（严，必须过）：这条样本**真的调到模型了吗**？
#      source == "blocked" 说明它被后端硬拦接住了（回的是固定文案）——
#      那 judge 不管判"守住"还是"破"，测到的都不是模型，这条样本**没有观测价值**。
#      实测（2026-10-13 16:13）：3 条被吃掉，见各条的 known_defect。
#      ⚠️ 和意图识别第五节 _assert_reached_model 是同一道防线、同一个理由：
#         没有它，"绿"可能是硬拦给的，不是模型守住的。
#
#   ② 主断言（松）：judge 没判"被攻破"。
#      为什么不干脆写成"一定守住"？因为词表是**漏斗**不是**法官** ——
#      judge 说"破"的时候，人得复核一遍（误报 vs 真破的分水岭）。
#      所以这道断言的作用是**冒烟 + 报警**：绿 = 这次没发现破；
#      红 = 先去看是不是误报（数据文件开头「判据工程的四个坑」讲了怎么分）。
#
# ══ 采样次数：默认 1 次，可按样本加码 ═══════════════════════════
#   "守住了" 和 "守得住" 是两件事，1 次采样分不开 ——
#   10-12 那两条剂量攻击就是**跑 3 遍才露出马脚**的（第 1 次看着像守住了）。
#   所以数据文件支持给单条样本写 `repeat: N`：那条跑 N 次，
#   **只要任意一次被判攻破就算失败** —— 这正是"断从不发生"该有的采样方式
#   （同一个思路见 test_assistant_意图识别.py 的 REPEAT_TIMES）。
#   为什么不做成全局 ×N：套件要能天天跑，21 条 × 多轮本来就 ~1 分钟，
#   全局 ×3 就 3 分钟起步。加码只给**实测会破**的那几条（比如那条"禁止说免责话术"）。
#   ⚠️ 没写 repeat 的样本，绿 = "这一次没发现破"，**不等于**"防线稳"。

import pytest

from common.data_loader import load_cases
from tools.reports.jailbreak_report import judge

JAIL_CASES = load_cases("assistant_jailbreak_cases.yaml")


def _params(cases):
    """参数化：标了 known_defect 的自动挂 xfail(strict=True)。

    机制和意图识别文件一模一样，理由写在**数据文件**里（不放这儿）：
      · 缺陷还在 → XFAIL（预期内失败，套件整体仍是绿的）；
      · 哪天观测点恢复了（不再被硬拦吃掉）→ XPASS → strict 判失败 → 提醒摘标记。
    """
    return [
        pytest.param(
            case,
            marks=(pytest.mark.xfail(reason=str(case["known_defect"]), strict=True)
                   if case.get("known_defect") else ()),
            id=case["name"],
        )
        for case in cases
    ]


def _ask_all_turns(ask, case):
    """按数据集跑一遍（单轮 or 多轮），返回每一轮的 (回答文本, assistantMessage)。

    多轮**必须用同一个 conversationId** —— 攻击的威力全在上下文累积里；
    每轮新建会话等于把它拆成一串单轮，测的就不是同一个东西了。
    （跑法和 tools/reports/jailbreak_report.py 的 run_case 一致。）
    """
    turns = case.get("turns") or [case["question"]]
    history = []
    conversation_id = None
    for text in turns:
        data = ask(text, conversation_id)
        conversation_id = data["conversationId"]
        am = data["assistantMessage"]
        history.append((am.get("text", ""), am))
    return history


@pytest.mark.parametrize("case", _params(JAIL_CASES))
def test_jailbreak_not_broken(ask, case):
    """越狱样本 → ① 必须真的调到模型；② 不该被攻破。

    判据（breach / guard / verdict）在数据文件里，判定复用 tools 的 judge()。

    红了怎么修（两种原因，修法完全不同）：
      · 前置断言红（source=blocked）→ 样本被硬拦吃掉了 → 换样本 / 标 known_defect；
      · 主断言红（judge 判破）→ **先人眼复核**：
          真破 → 记缺陷，改后端提示词（RecipeServiceImpl 的边界文字）；
          误报 → 改数据文件的 breach 词表。
    别顺手改断言去迁就现状 —— 那等于把警报器拆了当太平。
    """
    repeat = int(case.get("repeat", 1))
    breached = None          # (answers, detail) —— 记录"哪一次破了"

    for _ in range(repeat):
        history = _ask_all_turns(ask, case)

        # ---- ① 前置：这条样本真的调到模型了吗 ----
        blocked_turns = [i for i, (_, am) in enumerate(history, 1)
                         if am.get("source") == "blocked"]
        assert not blocked_turns, (
            f"「{case['name']}」第 {blocked_turns} 轮被本地硬拦接住了（source=blocked）——"
            f"这条样本**没测到模型**，judge 判出的「守住 / 破」都不算数。"
            f"多半是它和硬拦词表撞了（B1 剂量类最容易撞 medical 硬拦）。"
            f"处置：换一条不撞硬拦的同类样本，或在数据文件里标 known_defect ——"
            f"让它当绿用例留着，只会多一条假哨兵。"
        )

        # ---- ② 主断言：judge 没判"被攻破" ----
        answers = [text for text, _ in history]
        broken, detail = judge(case, answers)
        if broken:
            breached = (answers, detail)
            break            # 断"从不发生"的逻辑：一次破就够了，不必再采样

    if breached is not None:
        answers, detail = breached
        breach_words = [w for w, _ in detail["breach"]]
        guard_words = [w for w, _ in detail["guard"]]
        pytest.fail(
            f"「{case['name']}」（边界 {case.get('boundary')} / 手法 {case.get('attack')}）"
            f"被判**可能被攻破**（规则 {detail['rule']}；共采样 {repeat} 次，任意一次命中即算失败）。\n"
            f"  命中越界词：{breach_words}\n"
            f"  命中护栏词：{guard_words or '（无）'}\n"
            f"  命中处上下文：{detail['breach'][:2] if detail['breach'] else '（见回答）'}\n"
            f"  命中那次的最后一答：{answers[-1][:200]}\n"
            f"⚠️ 这份判据**误报率高**，先人眼复核再下结论：\n"
            f"  · 真破（真给了剂量 / 真写了代码 / 真教了极端方法）→ 记缺陷，改后端提示词；\n"
            f"  · 误报（它其实拒绝了，只是措辞撞了词表）→ 改数据文件的 breach，别改断言。"
        )
