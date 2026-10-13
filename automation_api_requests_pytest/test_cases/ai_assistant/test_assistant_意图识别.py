# test_cases/ai_assistant/test_assistant_意图识别.py
# 【任务：AI 助手 · 意图识别（意图路由）】
# ══ 这个文件的分工 ═════════════════════════════════════════════════
#
#   一、正向基线  求替代 → 回答该在聊"替代"这件事     （绿）
#   二、正向断言  越界   → 回答该明确拒绝 / 说明边界  （绿）
#   三、负面断言  越界   → 回答里不该出现越界产物     （绿；修复于 10-12，重复 5 次守卫）
#         ⚠️ 这一节的样本**已被硬拦接住**，现在测不到模型 —— 它是一条"假绿"，
#            见第五节开头那段说明，处置待定。
#   四、意图断言  判出来的 intent == 数据集标签        （绿；2026-10-13 由 skip 转正）
#   五、词表外越界 意图判越界、但硬拦不管 → 该真的走到模型、且被模型拒绝
#         （2026-10-13 新增；本文件里**唯一**还能测到"模型守边界"的一节）
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

# ⚠️ 2026-10-13 改名：原名 BLIND_CASES（"没有观测点"）。后端补上 intent 透传之后
#    这个集合**不盲了** —— 改叫 INTENT_ASSERT_CASES，交给第四节断意图。
#    筛选条件**一个字没动**：还是"topic / refusal / forbidden 三样都不挂"的那些条。
#    （数据集里给「替代-还能吃什么」撤掉了 topic，它就自然落进这个集合了 ——
#      这是有意的：它的缺陷是"判成了什么意图"，不该再由 topic 断言重复盯。）
# ⚠️ 2026-10-13 补了一个排除项：带 `oos_sentinel` 的样本**不进**这个集合。
#    它们的观测点是"模型守不守边界"（第五节），不是"规则判得对不对"（本节）——
#    一条样本只归一个观测点。不然哪天硬拦表一改，两处断言会同时红，
#    分不清到底是"哨兵失效"还是"意图判错"。
INTENT_ASSERT_CASES = [c for c in INTENT_CASES
                       if not c.get("topic") and not c.get("refusal")
                       and not c.get("forbidden") and not c.get("oos_sentinel")]

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
    """
    text = ask(case["question"])["assistantMessage"]["text"]

    hit = [w for w in case["refusal"] if w in text]
    assert hit, (
        f"问「{case['question']}」（{case['intent_cn']}）却没被拒绝、也没说明能力边界"
        f"（{case['refusal']} 一个都没命中）：{text[:200]}"
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


# ==================== 四、意图断言：判出来的标签 == 数据集的标签 ====================
# 🎯 2026-10-13 转正：这一节原来是 8 条 pytest.skip（理由保留在下面用例的 docstring 里）。
#    后端把 intent 透传出来之后，观测点出现了 ——
#    于是这 8 条从"测不了"变成"**唯一能直接算准确率**的断言"。
#
# 为什么它比前三节都硬？
#   前三节断的是"回答里有没有某类词"—— 模型措辞不可预测（温度 0.6），只能松着断；
#   这一节断的是 intent 字段**精确相等**—— 意图是本地关键词算的，
#   同一句话问一百次结果一样，所以才敢写 ==。
#
# 准确率就藏在这行参数化里：**通过数 ÷ 用例总数**，不用另写统计脚本。
# ⚠️ 口径要说清，别把两个数搞混：
#   · 数据集 15 条**全部**逐条真打过（2026-10-13）→ 14/15 = 93.3%；
#   · 但**用例层面**只有本节这 9 条在断意图（其余 6 条各有各的观测点 ——
#     一条样本只归一个观测点，不重复断）→ 8 通过 + 1 xfail。
# 留一条误判不修是刻意的：全绿分不清"规则真好"还是"样本太容易"。

@pytest.mark.parametrize("case", _params(INTENT_ASSERT_CASES), ids=case_id)
def test_intent_matches_dataset_label(ask, case):
    """判出来的 intent 必须等于数据集里标注的**真实**意图。

    case["intent"] 写的是真实意图（人工标的），不是"系统会判成什么"——
    两者的差就是误判，而这条用例量的正是那个差。

    ══ 为什么把原来的 skip 换掉了（这段是历史，值得留着）══
    当时的判据是"断不了就不写"：
      ① 硬凑一个"看起来在测"的断言，比不写更糟（它会在该红的时候绿）；
      ② 也不能装作不存在 —— 用 skip 让缺口每次跑测试都**看得见**。
    这两条**没变**，变的是前提：intent 现在可观测了，
    于是"不能写假断言"的执行方式就从"标注缺口"变成"**能断就必须断**"——
    继续 skip 同样是假的绿（数据集里的标签就白标了一场）。

    ══ 红了怎么修（两种原因，修法完全不同）══
      · 判错了     → 改后端词表（RecipeServiceImpl 的 SUBSTITUTE_/OUT_OF_SCOPE_ 等）—— 改 Java
      · 标签标错了 → 改数据文件里的 intent —— 改 YAML
    别顺手改断言去迁就现状 —— 那等于把体温计砸了当退烧。

    ══ 已知误判怎么处理 ══
    如果是**规则天然抓不到**（不是写错了），在数据文件里给它标 `known_defect`，
    会自动挂上 xfail(strict)（见本文件 _params）：缺陷还在时算预期内失败，
    后端修好后变 XPASS → strict 判失败，逼你摘标记。
    """
    am = ask(case["question"])["assistantMessage"]

    assert am.get("intent") == case["intent"], (
        f"问「{case['question']}」（真实意图：{case['intent_cn']} = {case['intent']}）"
        f"却被判成 {am.get('intent')!r}；"
        f"若这是规则的已知盲区，请在数据文件里给它标 known_defect"
    )


# ==================== 五、词表外越界：模型守边界的哨兵 ====================
# 🎯 2026-10-13 新增。这一节存在的唯一理由：**把"模型守边界"重新变成一个可观测的点**。
#
# 背景（数据文件同名小节写得更细）：
#   前三节那三条越界样本**全被后端硬拦接住**（source=blocked，压根没调模型）——
#   于是第三节那条绿是**假绿**：回答是硬拦的固定文案，当然不含代码，永远不会红。
#   根因是意图分类与硬拦用了两套词表，差集（程序/脚本/算法/排序/电影/游戏）里的话
#   判成越界却**不被拦**。本节样本特意挑在这个差集里 —— 它们能真的走到模型。
#
# ⚠️ 本节**故意不去补硬拦表**：补了这批样本又被拦掉、观测点第二次消失。


def _assert_reached_model(am, case):
    """前置断言：这次**真的测到了模型**吗？

    这是本节的命门。没有它，本节会比第三节更糟 —— 一条"看起来在测模型"的假绿哨兵。
    （第三节就是栽在这儿：硬拦接管之后，断言的对象已经从模型变成了固定文案。）

    它同时是一个**失效告警**：谁哪天把硬拦词表补齐（两表差集变空），
    这个断言会最先红，直白地告诉你"样本该换了，别再留着假绿"。
    """
    assert am.get("source") != "blocked", (
        f"「{case['question']}」被本地硬拦接住了（source=blocked）—— 这条样本**已经测不到模型**。\n"
        f"多半是有人把硬拦词表补齐了（OUT_OF_SCOPE_KEYWORDS 与 BLOCK_OUT_OF_SCOPE_PATTERNS "
        f"的差集变了）。请换一条仍在差集里的样本，或删掉本节 —— "
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
