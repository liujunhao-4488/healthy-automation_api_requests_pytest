# test_cases/ai_assistant/test_assistant_意图标签.py
# 【任务：AI 助手 · 意图标签准确率（intent）】
# ══ 这个文件的分工 ═════════════════════════════════════════════════
#
#   一、标签断言   判出来的 intent == 数据集标签        （主断言，量准确率）
#   二、不变量     intent=fallback ⟺ source=blocked    （防"标签算了但没接上"）
#
# 数据全部来自 data/assistant_intent_label_cases.yaml，不写死在用例里。
#
# ══ 命名来历（别被文件名绕） ══
#   intent 就是**全项目唯一的分类器**（RecipeServiceImpl.classifyIntent），
#   取值 query / knowledge / advice / fallback / chat。
#   本文件 2026-10-14 之前叫 test_assistant_路由.py —— 那时新分类器挂在一个叫 route 的
#   临时字段上，为的是不弄红已有的意图用例。那个名字和"意图识别"撞车，
#   已统一回 intent，本文件随之改名。旧名 route 从此不再出现。
#
# ══ 和 test_assistant_意图识别.py 是什么关系 ══
#   那份断的是**模型行为**（回答里有没有越界产物、有没有拒绝、兜底字段一致），
#   靠的是回答文本，措辞不可预测，只能松着断；
#   这份断的是**分类标签本身**（本地关键词算的，同一句话问一百次结果一样，敢写 ==）。
#   两者观测点不同、互不重叠 —— 一条样本只归一个观测点。

import pytest

from common.data_loader import load_cases

INTENT_CASES = load_cases("assistant_intent_label_cases.yaml")

# 第二节用：只有"该被硬拦"的样本才配做不变量校验。
FALLBACK_CASES = [c for c in INTENT_CASES if c["intent"] == "fallback"]


def case_id(case):
    """中文用例名 —— 数据集里的 name 字段。"""
    return case["name"]


def _params(cases):
    """把数据集转成参数化参数；标了 known_defect 的挂上 xfail(strict=True)。

    机制和 test_assistant_意图识别.py._params 完全一样（那里讲透了，这里不重复）：
      · 缺陷还在 → XFAIL（套件整体仍绿）；
      · 后端补好了 → 断言自然通过 → XPASS → strict 判**失败** → 这就是"该摘标记了"的信号。
    strict 的盲区也一样：标记期间万一又退化，仍然算 XFAIL，**抓不到回退**。所以修好就要赶紧摘。
    """
    return [
        pytest.param(
            case,
            marks=(pytest.mark.xfail(reason=str(case["known_defect"]), strict=True)
                   if case.get("known_defect") else ()),
            id=case_id(case),
        )
        for case in cases
    ]


# ==================== 一、标签断言：判出来的 intent == 数据集标签 ====================

@pytest.mark.parametrize("case", _params(INTENT_CASES), ids=case_id)
def test_intent_matches_dataset_label(ask, case):
    """判出来的 intent 必须等于数据集里标注的**该走的那条路**。

    intent 由本地关键词算出来（RecipeServiceImpl.classifyIntent），
    同一句话问一百次结果一样 —— 所以才敢写 ==；
    换成断模型回答的措辞就不敢了（温度 0.6，两次不一样）。

    准确率就藏在这行参数化里：**通过数 ÷ 用例总数**，不用另写统计脚本。

    ══ 红了怎么修（两种原因，修法完全不同）══
      · 判错了     → 改后端词表（RecipeServiceImpl 的 INTENT_QUERY_/KNOWLEDGE_/ADVICE_）—— 改 Java
      · 标签标错了 → 改数据文件里的 intent —— 改 YAML
    别顺手改断言去迁就现状 —— 那等于把体温计砸了当退烧。

    ══ ⚠️ 这条绿了**不等于**"系统真的会去查库" ══
    intent 现在**只算不派**：5 个值都只跟着响应回出去，还没有任何下游 if。
    它绿只说明"分派标签算对了"。真正的接线（读 diet_record、查 ingredient）
    是另一件事，得另写断言（那时该断的是"响应里有没有真的带上聚合数字"）。
    """
    am = ask(case["question"])["assistantMessage"]

    assert am.get("intent") == case["intent"], (
        f"问「{case['question']}」（该走：{case['intent_cn']} = {case['intent']}）"
        f"却被判成 {am.get('intent')!r}；"
        f"若这是关键词规则的已知盲区，请在数据文件里给它标 known_defect"
    )


# ==================== 二、不变量：intent=fallback ⟺ source=blocked ====================
# 为什么值得单独写一条：第一节只断 `intent` 字段的值，
# 万一哪天 plumbing 断了（intent 算出来了、却没挂到响应上），
# am.get("intent") 会返回 None，第一节会红 —— 但它红得**说不清是哪一段坏的**。
# 这条把"兜底类"单独拎出来，直接盯住两个字段的**一致性**：
#   intent=fallback 的定义就是"命中 detectBlockedType"（classifyIntent 里就是复用它），
#   而命中 detectBlockedType 的唯一后果就是 source=blocked。
#   所以这两个值**在实现上是同一个判断的两面** —— 它们不一致，一定是代码被改坏了。

@pytest.mark.parametrize("case", _params(FALLBACK_CASES), ids=case_id)
def test_fallback_intent_means_blocked(ask, case):
    """兜底路 → 必须真的是被硬拦接住的那条路（source=blocked），且拦对类型。

    这条同时是**哨兵**：谁哪天把 classifyIntent 里的 detectBlockedType 换成别的判断，
    或者把 intent 的写入漏掉，它立刻红。

    ⚠️ 它**不是**在测"该拦的拦住了" ——
       "该不该拦"由 data/assistant_guard_cases.yaml 那份安全用例负责。
       这条只管"两个字段说的是不是同一件事"。
    """
    am = ask(case["question"])["assistantMessage"]

    assert am.get("intent") == "fallback", "数据文件里这一节只该放 intent=fallback 的样本"
    assert am.get("source") == "blocked", (
        f"「{case['question']}」判成了 fallback，但 source={am.get('source')!r} 不是 blocked —— "
        f"两个字段说的不是同一件事，多半是 classifyIntent / 响应写入被改坏了"
    )
    if case.get("blocked"):
        assert am.get("blocked") == case["blocked"], (
            f"「{case['question']}」该被拦成 {case['blocked']}，实际是 {am.get('blocked')!r}"
        )
