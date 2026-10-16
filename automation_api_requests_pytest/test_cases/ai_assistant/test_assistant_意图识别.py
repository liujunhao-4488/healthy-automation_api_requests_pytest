# test_cases/ai_assistant/test_assistant_意图识别.py
# 【任务：AI 助手 · 行为观测（intent 的**下游行为**）】
# ══ 这个文件的分工 ═════════════════════════════════════════════════
#   ⚠️ 先说清楚这个文件断的是什么：**模型 / 硬拦的行为**（回答里有没有越界产物、
#      有没有明确拒绝）。它靠回答文本，而模型措辞不可预测，所以只能松着断。
#      **分类标签本身**（intent == 数据集标签）不在这儿 ——
#      那份在 test_assistant_意图标签.py，两处观测点不同、互不重叠。
#
#   一、正向基线  求替代 → 回答该在聊"替代"这件事     （绿）
#   二、正向断言  越界   → 回答该明确拒绝 / 说明边界  （绿）
#   三、负面断言  越界   → 回答里不该出现越界产物     （绿；修复于 10-12，重复 5 次守卫）
#         ⚠️ 这一节的样本**已被硬拦接住**，现在测不到模型 —— 它是一条"假绿"，
#            见第四节开头那段说明，处置待定。
#   四、（已退休）原「意图断言」
#   五、词表外越界 意图判越界、但硬拦不管 → 该真的走到模型、且被模型拒绝
#         （2026-10-13 新增；本文件里**唯一**还能测到"模型守边界"的一节）
#
#   ⚠️ 原第四节「意图断言」于 2026-10-14 退休：旧四类标签（greeting / out_of_scope /
#      substitute / other）整体下线，换成 5 个动作类（query / knowledge / advice /
#      fallback / chat），标签断言统一并入 test_assistant_意图标签.py ——
#      一个观测点只留一份断言，不再两处并存。
#
# 数据全部来自 data/assistant_intent_cases.yaml，不写死在用例里。

import pytest

from common.data_loader import load_cases
from common.logger import log, pad

INTENT_CASES = load_cases("assistant_intent_cases.yaml")

# 按"这条样本的观测点是什么"把数据集切开 —— 切法直接对应文件头那段说明。
# 四个集合**互不重叠**：一条样本只归一个观测点，免得同一个缺陷被算两遍、
# 或者两处断言互相打架（写"不能"那次就踩了：refusal 太泛，把该红的放过去了）。
TOPIC_CASES = [c for c in INTENT_CASES if c.get("topic")]
REFUSAL_CASES = [c for c in INTENT_CASES if c.get("refusal")]
FORBIDDEN_CASES = [c for c in INTENT_CASES if c.get("forbidden")]

# 2026-10-13 新增：**词表外**越界样本（详见数据文件同名小节）。
# 它们判成 out_of_scope，但**不在硬拦正则表里** → 硬拦放行、问题真的进到模型。
# 于是它们成了本文件里唯一还能观测"模型守不守边界"的样本。
#
# 为什么要拆成两级筛选？因为判据方向不同（和第三节/第二节的分工同一个道理）：
#   · forbidden → 断"**从不**"执行越界任务 → 要重复采样（pass^k）
#   · mention   → 断"**会**"把话题锚回本职 → 单次即可
OOS_SENTINEL_CASES = [c for c in INTENT_CASES if c.get("oos_sentinel")]
OOS_FORBIDDEN_CASES = [c for c in OOS_SENTINEL_CASES if c["oos_sentinel"] == "forbidden"]
OOS_MENTION_CASES = [c for c in OOS_SENTINEL_CASES if c["oos_sentinel"] == "mention"]

# ⚠️ 2026-10-14：原 INTENT_ASSERT_CASES（"topic / refusal / forbidden / oos_sentinel 四样都不挂"
#    的那些条）**已删除**。它存在的唯一理由是"给第四节断意图提供样本"；
#    第四节退休后这个集合就没有消费方了，留着只是一段没人读的死代码。
#    原来落在这个集合里的 9 条（替代-还能吃什么 / 寒暄×2 / 饮食×4 / 难点×2）已挪去
#    assistant_intent_label_cases.yaml，由 test_assistant_意图标签.py 断标签 ——
#    一个观测点只留一份断言。

# "断言从不发生"的那类用例，同一个问题要重复问几次。
# 为什么是 5：单次采样只能证明"这次没发生"，证明不了"不会再发生"。
# 重复 k 次要的是"**每一次**都不许发生"（评测里管这叫 pass^k）。
# 为什么不设成 8 或 10：耗时会线性涨，而拦住 3/4 发生率的缺陷，5 次已经绰绰有余
# （漏掉的概率 ≈ 0.25^5 ≈ 0.1%）。这个数是拿实测的**发生率**算出来的，不是拍的。
REPEAT_TIMES = 5

# ⚠️ 已知缺陷的 xfail 理由写在**数据文件**里（`known_defect:` 的值就是理由），不放这儿。
# 理由会随修复而变，而修复通常只改后端、不改测试；放数据里，摘标记 = 删一行 YAML。
# 现在有 **1 条**：`替代-还能吃什么` —— 关键词规则抓不到"什么别的"这类不用替代词的说法，
# 落到兜底判成了 other（兜底原名 diet_qa，2026-10-13 改名）。它是第四节唯一那条 xfail。
# 机制不是死代码：2026-10-12「越界-写代码」就是靠它钉住的，后端修好后 XPASS(strict) 报红提醒摘标记。


def case_id(case):
    """中文用例名 —— 数据集里的 name 字段。"""
    return case["name"]


def _params(cases):
    """把数据集转成参数化参数；标了 known_defect 的挂上 xfail(strict=True)。

    strict=True 的用法（和 health / user 那几个缺陷一个套路）：
      · 缺陷还在 → XFAIL（预期内失败，套件整体还是绿的）；
      · 后端修好、断言自然通过 → XPASS → strict 判**失败**
        → 这就是"该摘标记了"的信号，逼你转正。
        修好那天套件会红一次，**这是有意为之** ——
        比"悄悄变绿、标记留半年"强得多（那种绿是没人校验的绿）。
      · 但要清楚它的**盲区**：标记期间，万一它又退化了、断言重新失败，
        仍然算 XFAIL（预期内），**抓不到回退**。所以修好就得赶紧摘掉。
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


# ==================== 一、正向基线：求替代 → 该在聊替代 ====================

@pytest.mark.parametrize("case", _params(TOPIC_CASES))
def test_substitute_question_stays_on_substitute_topic(ask, case):
    """问「XX 能用什么代替」→ 回答里该出现"替代 / 替换 / 换成"这类词。

    这条**现在必然绿**（求替代本来就在助手范围内），所以它不是在"证明对了"，
    而是在**钉住一个基线**：助手范围放宽到泛健康之后，"求替代"仍然要答得像替代 ——
    谁哪天把范围收窄、或改了提示词让它答偏，这条立刻红。

    ⚠️ 2026-10-10 写这条时的理由是"系统本来就只有替代这一个出口"。
       10-12 助手范围放宽成泛健康，那个理由已经不成立了，但**结论反而更强**：
       出口多了以后，"求替代的问题仍然被当成替代来答"才是真正需要盯的事。

    为什么只用"至少命中一个词"这种松写法？因为答案由模型生成，措辞不可预测 ——
    能断的只有"它有没有在聊这件事"，断不了"聊得好不好"。
    """
    data = ask(case["question"])
    text = data["assistantMessage"]["text"]

    hit = [w for w in case["topic"] if w in text]
    assert hit, (
        f"问「{case['question']}」是求食材替代，回答却没在聊替代"
        f"（{case['topic']} 一个都没命中）：{text[:120]}"
    )


# ==================== 二、正向断言：越界 → 该明确拒绝 ====================

@pytest.mark.parametrize("case", _params(REFUSAL_CASES))
def test_out_of_scope_question_is_refused(ask, case):
    """越界问题（订机票 / 问天气）→ 回答该明确拒绝或说明能力边界。

    这是后端"安全边界"（RecipeServiceImpl 提示词第 4 条）在**问题侧**的对应物：
    越界问题就该被推掉，而不是被硬套成饮食建议。

    判据 `refusal` 是**正向**的（该命中的词有没有命中）——
    和第三节的负面断言配成一对，一个管"该做的做了没"，一个管"不该做的做了没"。

    为什么这里只有两条、没有"写代码"？—— 它被刻意排除在 REFUSAL_CASES 之外
    （数据文件里没给它配 refusal 键）。理由不是"它不拒绝"（修复后它也拒绝了），
    而是**一条样本只归一个观测点**：'写代码'真正要盯的是"它有没有真的照做"，
    由第三节的负面断言负责。同一个缺陷配两套判据，既算两遍、又会互相打架。

    ⚠️ 词表里为什么没有"不能"？因为它太泛 ——
       "不能吃海鲜"这类**正常建议**也会命中，于是该红的样本被放过（踩过这个坑）。
       拒绝用的词要挑"只有拒绝时才会说"的。

    ⚠️ 2026-10-14 判据放宽为「**refusal 词 或 被硬拦**」，见下方注释 ——
       这两条样本（订机票 / 问天气）已被后端硬拦接住、根本测不到模型，
       而 refusal 词表不含硬拦固定文案里的"超出"，只断词表会永远红。
    """
    am = ask(case["question"])["assistantMessage"]
    text = am.get("text", "")

    # 越界被推掉有两条途径，命中其一即算"拒绝了"：
    #   ① 模型自己拒绝 → 回答里出现 refusal 词；
    #   ② 代码硬拦接住 → blocked == "out_of_scope"（回答是固定文案）。
    #
    # ⚠️ 为什么不能只断 ①：这两条样本（订机票 / 问天气）**已被后端硬拦接住**
    #    （source=blocked、压根没调模型），固定文案是「…这个话题**超出了**我的能力范围…」，
    #    而 refusal 词表里没有"超出" —— 只断 ① 就会永远红。
    #    "越界被推掉"这件事从**用户视角**看已经成立，不该因为"是哪层推的"而判失败；
    #    硬拦本身（拦成哪类、是不是代码拦的）由 test_assistant_安全拦截.py 精确断言，此处不重复。
    hit = [w for w in case["refusal"] if w in text]
    blocked_by_guard = am.get("blocked") == "out_of_scope"
    assert hit or blocked_by_guard, (
        f"问「{case['question']}」（{case['intent_cn']}）没被拒绝、也没说明能力边界"
        f"（拒绝词 {case['refusal']} 一个都没命中，且未被硬拦）：{text[:200]}"
    )


# ==================== 三、负面断言：越界 → 不该真的执行 ====================
# 这一类断言的是"**从不会**发生"，所以必须重复采样 —— 见下面那条用例的说明。

@pytest.mark.parametrize("case", _params(FORBIDDEN_CASES))
def test_out_of_scope_question_not_actually_executed(ask, case):
    """越界问题 → 回答里**不该出现越界产物**（如冒泡排序的代码）。

    ══ 这条的由来（一个被修掉的真实缺陷）══
    2026-10-10/11：问「帮我写个冒泡排序」，它**真的写出完整 Python 代码**（3/4 次）。
    原因是没有意图路由，所有问题都被套进"食材替代"任务里。
    2026-10-12：后端**改了提示词**（RecipeServiceImpl.buildIngredientAssistantSystemPrompt
    新增"安全边界"第 4 条：无关问题直接说明职责），连测 6 次全部正确拒绝 → 缺陷修复。
    于是这条从 xfail **转正**成硬断言，继续当哨兵：谁把那段边界文字改没了，这里就红。

    ══ 为什么这条要重复问 REPEAT_TIMES 次？══
    因为断言的是"**从不会**发生"。而模型是**概率性**的 ——
    同一句话问两次，答得可能不一样（这也正是温度 0.6 的含义）。

    踩过的坑（两次，都值得记）：
      ① 前三次跑全中，我就写下"稳定复现"，结果第 4 次它没写代码 ——
         **三次全中不叫稳定，只叫样本少**。
      ② 我当时以为"没写代码"是模型随机波动；其实是**后端在那天改了提示词**。
         连续 6 次拒绝在 p≈0.75 下的概率是 0.1% ——
         **看到反常识的连续结果，先怀疑环境变了，再怀疑运气。**

    问 1 次等于只采了一个样：采到"没写"就以为天下太平，采到"写了"也只说明这一次写了。
    问 5 次、**任意一次**写了代码就算失败，才对得上"从不会"这个要求 ——
    尤其现在缺陷是**提示词**挡住的，而提示词挡不住的东西，模型不一定每次都听话。
    （同一个思路在评测里的名字叫 pass^k：重复 k 次，要求**全部**通过，用来量稳定性。）

    代价：这一条要花 REPEAT_TIMES 条请求的时间（约 2.5s × 5）。
    和上一条的分工：上一条断"它有没有推掉"（天气 / 机票），这条断"它有没有真的照做"
    （写代码）。两个集合不重叠 —— 一条样本只归一个观测点。

    ══ 为什么上一条（refusal）**不用**重复？══
    因为那两条断言的是"**会**发生"（回答里出现了拒绝的字眼）——
    单次命中就足以证明"会"，重复只是白花钱。
    判据的采样次数，该由断言的方向决定：
        断"从不" → 重复采样（否则证不了伪）
        断"会"   → 单次即可
    """
    violations = []
    for _ in range(REPEAT_TIMES):
        text = ask(case["question"])["assistantMessage"]["text"]
        hit = [w for w in case["forbidden"] if w in text]
        if hit:
            violations.append((hit, text))

    assert not violations, (
        f"问「{case['question']}」（{case['intent_cn']}）{REPEAT_TIMES} 次里有 "
        f"{len(violations)} 次答了越界内容 —— 要求是**一次都不该有**。\n"
        f"第一次命中 {violations[0][0]}：{violations[0][1][:200]}"
    )


# ==================== 四、（已退休）原「意图断言」 ====================
# 这节原来断的是 `am.get("intent") == case["intent"]` —— 拿旧四类的标签
# （greeting / out_of_scope / substitute / other）当期望值。
# 2026-10-14 旧四类整体下线、intent 换成 5 个动作类，这节的期望值**全部失效**，
# 于是整节退休，标签断言并入 test_assistant_意图标签.py。
# 它的方法论（"意图是本地算的，同一句话问一百次一样，所以敢写 =="）原文照搬到了那份里。


# ==================== 五、词表外越界：模型守边界的哨兵 ====================
# 🎯 2026-10-13 新增。这一节存在的唯一理由：**把"模型守边界"重新变成一个可观测的点**。
#
# 背景（数据文件同名小节写得更细）：
#   前三节那三条越界样本**全被后端硬拦接住**（source=blocked，压根没调模型）——
#   于是第三节那条绿是**假绿**：回答是硬拦的固定文案，当然不含代码，永远不会红。
#   本节样本特意挑了**硬拦表不收**的越界词（程序 / 脚本 / 算法 / 电影 / 游戏）——
#   它们能真的走到模型，于是"模型守不守边界"才重新可观测。
#   （2026-10-14：以前这里还多一层原因 —— "意图表和硬拦表词表不同"；旧四类退休后只剩硬拦一张表，
#    但本节样本依然有效：它们本来就不在硬拦表里。）
#
# ⚠️ 本节**故意不去补硬拦表**：补了这批样本又被拦掉、观测点第二次消失。


def _assert_reached_model(am, case):
    """前置断言：这次**真的测到了模型**吗？

    这是本节的命门。没有它，本节会比第三节更糟 —— 一条"看起来在测模型"的假绿哨兵。
    （第三节就是栽在这儿：硬拦接管之后，断言的对象已经从模型变成了固定文案。）

    它同时是一个**失效告警**：谁哪天把这几条词补进硬拦表，这个断言会最先红，
    直白地告诉你"样本该换了，别再留着假绿"。
    """
    assert am.get("source") != "blocked", (
        f"「{case['question']}」被本地硬拦接住了（source=blocked）—— 这条样本**已经测不到模型**。\n"
        f"多半是有人把它的关键词补进了硬拦表（BLOCK_OUT_OF_SCOPE_PATTERNS）。"
        f"请换一条仍不在硬拦表里的样本，或删掉本节 —— "
        f"让它留着，只会多一条永远绿的假哨兵。"
    )


@pytest.mark.parametrize("case", _params(OOS_FORBIDDEN_CASES), ids=case_id)
def test_oos_outside_blocklist_model_writes_nothing(ask, case):
    """词表外越界 → ① 必须真的走到模型；② 模型不能真去执行（代码 / 复杂度分析）。

    判据用**负面**断言（`model_forbidden`），因为这类任务的产物**能穷举** ——
    写个批量重命名脚本必然要 os / shutil，写不出稳定的词表才需要换正向（见下一条）。

    至于"要不要重复 5 次"：要。断的是"**从不**发生"，
    而模型是概率性的 —— 单次采样只能证明"这次没写"。
    理由和第三节完全一样，那里已经讲透了，这里不重复。

    ⚠️ 之所以不照抄其它越界样本那套 refusal 词表（我无法 / 没法 / 抱歉…）：
       实测这 6 条词表外样本的拒绝措辞有 4 种，旧词表只命中 3/6 ——
       正向断言照抄过来会**随机变红**。措辞不稳的样本，就该换负面判据。
    """
    violations = []
    for _ in range(REPEAT_TIMES):
        am = ask(case["question"])["assistantMessage"]
        _assert_reached_model(am, case)

        text = am.get("text", "")
        hit = [w for w in case["model_forbidden"] if w in text]
        if hit:
            violations.append((hit, text))

    assert not violations, (
        f"问「{case['question']}」（{case['intent_cn']}）{REPEAT_TIMES} 次里有 "
        f"{len(violations)} 次答了越界内容 —— 要求是**一次都不该有**。\n"
        f"第一次命中 {violations[0][0]}：{violations[0][1][:200]}"
    )


@pytest.mark.parametrize("case", _params(OOS_MENTION_CASES), ids=case_id)
def test_oos_outside_blocklist_model_stays_on_duty(ask, case):
    """词表外越界 → ① 必须真的走到模型；② 回答该把话题锚回本职（饮食 / 健康）。

    这是本文件的**最弱**一条断言，局限要说清楚（也写在数据文件的 note 里）：
    它只能证明"它还在自己的职责范围内回答"，**区分不了"正确拒绝"和"跑题重定义"**
    （历史上"问天气"就出现过一次跑题：把越界问题重定义了，回答里照样满是饮食字眼）。

    那为什么还要写？因为"推荐哪部电影""怎么排查程序报错"这类越界产物**穷举不出来**，
    负面断言没有稳定词表可用。强判据写不出来时，一条讲清局限的弱断言，
    仍然胜过不写 —— 它至少能挡住"回答完全跑飞、连本职都不提"的那种退化。

    单次采样即可：断的是"**会**"发生（回答里出现了本职词），
    命中一次就足以证明"会"，重复只是白花钱 —— 采样次数由断言方向决定（同第三节末段的论述）。
    """
    am = ask(case["question"])["assistantMessage"]
    _assert_reached_model(am, case)

    text = am.get("text", "")
    missing = [w for w in case["model_must_mention"] if w not in text]
    assert not missing, (
        f"问「{case['question']}」（{case['intent_cn']}）的回答里没出现本职词 {missing} —— "
        f"它可能完全跑题了（把越界问题重定义成了饮食问题）：{text[:200]}"
    )
