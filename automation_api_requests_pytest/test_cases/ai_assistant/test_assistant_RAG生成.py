# test_cases/ai_assistant/test_assistant_RAG生成.py
# 【任务：AI 助手 · RAG 生成侧（Generation）】
#
# ══ 这个文件补的是哪一段盲区 ═══════════════════════════════════════
#
#   test_assistant_RAG召回.py  直连 5000，测「资料找得对不对」；
#   本文件                     打 8080，测「找到之后有没有真用上、用得对不对」。
#
#   这两段之间原来还有一个**谁都不管**的缝：8080 到底有没有把检索结果拼进 prompt？
#   后端是这么写的（RecipeServiceImpl:872-873）：
#       result.put("route", KNOWLEDGE_ROUTE_ARTICLE);       // 检索之前，无条件写入
#       result.put("facts", searchKnowledgeBase(question)); // 然后才检索
#   而 searchKnowledgeBase 对任何失败（超时 / 连接被拒 / 5xx）都
#       log.warn(...) + return "";
#   召回为空时 buildKnowledgeFacts 也返回同一个空串。
#   ⇒ 「召回 3 条」「召回 0 条」「5000 挂了」三种情况的响应**完全一致**。
#   也就是说：RAG 整段失效时，用户拿到一份没依据的回答，测试报告全绿。
#
# ══ 为什么判据要分「否定式」和「肯定式」══════════════════════════════
#
#   后端调用模型的参数是 temperature=0.6、没有 seed（RecipeServiceImpl:1150）。
#   同一个 prompt 每问一次，措辞和详略都会变 —— 这不是缺陷，是采样。
#   后果直接决定用例怎么写：
#
#     · 否定式判据（不能出现什么）→ 稳定，可以硬断言
#         例：不能引用召回集之外的文档、不能出现语料里没有的关键数值
#     · 肯定式判据（必须出现什么）→ 单次会 flaky，只能做多次采样统计
#         例：必须引用《》、必须提到 5 克
#
#   所以下面没有一条「单次必须引用」的硬断言 —— 那种用例红了绿了都不说明问题，
#   最后只会被标成 flaky 删掉。见 test_citation_present_rate 的写法。
#
# ══ 四个用例各自测什么 ═══════════════════════════════════════════
#
#   1. test_citation_within_recall    引用不能超出本次召回集（编造依据）
#   2. test_key_quantities_traceable  关键数值必须能在片段里找到（单位归一化后）
#   3. test_citation_present_rate     引用出现率（3 次采样，测承诺兑现率）
#   4. test_rag_effect_observable     RAG 是否生效**不可观测** —— 缺陷记录（xfail）
#
# ⚠️ 本文件依赖**两个服务**：5000（召回基准）+ 8080（对话）。
#   5000 没起直接 skip —— 因为那时后端自己也会静默降级，
#   测到的就不是「生成用没用好」，而是「模型自由发挥得好不好」。

import re

import pytest
import requests

from api.kb_api import KbApi
from common.data_loader import load_cases


CASES = load_cases("rag_generation_cases.yaml")


# ══ 工具：数值与单位的归一化 ═══════════════════════════════════════
#
# 为什么必须归一化：语料原文是「5g」，模型回答写「5 克」。
# 直接做字符串包含判断，"5克" 在 "…降至 5g 以下…" 里找不到 → 判成不可追溯。
# 这是**假红**：回答其实完全正确。判据错在实现，不在被测系统。

_UNIT_ALIASES = {
    "克": "g",
    "g": "g",
    "毫克": "mg",
    "mg": "mg",
    "千卡": "kcal",
    "大卡": "kcal",
    "kcal": "kcal",
    "%": "%",
    "％": "%",
}

# 单位按长度从长到短排（毫克 在 克 之前），否则「毫克」会先被「克」吃掉一半
_QUANTITY_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(毫克|克|千卡|大卡|kcal|mg|g|%|％)",
    re.IGNORECASE,
)


def extract_quantities(text):
    """抽出文本里的「数值 + 单位」，单位统一成 g / mg / kcal / %。

    返回 set[(float, str)]，例如「降至 5 克以下」→ {(5.0, "g")}。
    """
    found = set()
    for match in _QUANTITY_RE.finditer(text or ""):
        value = float(match.group(1))
        unit = _UNIT_ALIASES.get(match.group(2).lower(), match.group(2))
        found.add((value, unit))
    return found


def parse_quantity(token):
    """把 yaml 里的 "5g" 解析成 (5.0, "g")。

    解析不出唯一一组数值+单位就直接报错 —— 数据写错了要在 collect 阶段炸，
    不能静默跳过后让用例看起来"全绿"。
    """
    found = extract_quantities(token)
    if len(found) != 1:
        raise ValueError(
            f"key_quantities 里的 {token!r} 必须是「数值+单位」，例如 5g / 300kcal"
        )
    return next(iter(found))


# ══ 工具：书名号引用的抽取与比对 ═══════════════════════════════════

_BRACKET_RE = re.compile(r"[（(].*?[）)]")


def normalize_title(title):
    """标题归一：去掉括注和空白。

    《成人高血压食养指南》和《成人高血压食养指南（2023年版）》是同一份文件，
    括注不该让它们变成两个东西。
    """
    text = _BRACKET_RE.sub("", title or "")
    return re.sub(r"\s+", "", text)


def cited_titles(answer):
    """抽出回答里所有《…》的书名。"""
    return re.findall(r"《([^》]{1,40})》", answer or "")


def citations_beyond_recall(answer, recall_titles):
    """返回回答里**超出召回集**的书名 —— 非空就是编造依据。"""
    normalized_recall = [normalize_title(t) for t in recall_titles]
    beyond = []
    for cited in cited_titles(answer):
        key = normalize_title(cited)
        matched = any(
            key == recall or key in recall or recall in key
            for recall in normalized_recall
        )
        if not matched:
            beyond.append(cited)
    return beyond


# ══ 夹具 / 辅助 ═══════════════════════════════════════════════════

@pytest.fixture(scope="module", autouse=True)
def kb_service_up():
    """开跑前确认算法服务（5000）在 —— 它是「召回基准」的来源。

    用 skip 而不是 fail：没起服务是**环境问题**，不是被测系统的缺陷。
    把它算进失败率，评测数字就不可信了（同 test_assistant_RAG召回.py）。
    """
    client = KbApi()
    try:
        resp = client.stats()
    except requests.exceptions.RequestException as exc:
        pytest.skip(
            f"算法服务未启动（{client.base_url}）—— 生成侧用例需要它提供召回基准。"
            f"先跑 algorithm/.venv/Scripts/python.exe algorithm/app.py。原因：{exc}"
        )
    assert resp.status_code == 200, f"算法服务探活失败：HTTP {resp.status_code}"


def recall_of(api, question):
    """同题查一次检索，拿"这次应该依据什么"。

    用 top_k=3 —— 和后端 searchKnowledgeBase 的 KB_TOP_K 保持一致。
    这里查 5 条再比 3 条，就会把模型**根本拿不到**的资料算进"召回集"，
    编造引用反而测不出来。
    """
    body = api.assert_ok(
        api.kb.search(question, top_k=3),
        f"检索「{question}」应成功",
    )
    return body["data"]


# ══ 1. 引用不能超出召回集 ═════════════════════════════════════════

@pytest.mark.parametrize("case", CASES, ids=[c["question"] for c in CASES])
def test_citation_within_recall(api, auth_headers, ask, case):
    """回答里引用的指南，必须是这次**真的召回**的那几份。

    这是本文件最值钱的一条：它测的不是"答得漂不漂亮"，而是
    **模型有没有声称一个它根本没拿到的依据**。

    判据是**否定式**的（只查"有没有超出"），所以不受 temperature 影响：
    模型可以这次引用、下次不引用，但只要引用，就不能凭空多出一个书名。
    """
    hits = recall_of(api, case["question"])
    if not hits:
        pytest.skip("本次召回为空 —— 没有资料可依据，引用判据不适用")

    recall_titles = {hit["title"] for hit in hits}
    answer = ask(case["question"])["assistantMessage"]["text"]
    beyond = citations_beyond_recall(answer, recall_titles)

    assert not beyond, (
        f"问题「{case['question']}」的回答引用了召回集之外的来源：{beyond}\n"
        f"本次实际召回：{sorted(recall_titles)}\n"
        f"回答节选：{answer[:300]}\n"
        f"→ 这不是措辞差异，是**编造依据**：模型声称的内容不在它拿到的资料里。"
    )


# ══ 2. 关键数值必须可追溯 ═════════════════════════════════════════

@pytest.mark.parametrize("case", CASES, ids=[c["question"] for c in CASES])
def test_key_quantities_traceable(api, auth_headers, ask, case):
    """回答里出现的关键数值，必须能在召回片段里找到（单位归一化后）。

    ⚠️ 只校验 yaml 里**显式标注**的 key_quantities，不做"全量数字追溯"：
       回答里的「一日三餐」「5 条原则」这类数字不是营养数值，
       全量抽取会把它们当成"不可追溯的数值"，误报会把人逼到关掉用例。
       判据的范围必须比"看起来合理"更窄。

    ⚠️ 只在回答**确实提到**该数值时才校验：模型这次不说 5 克，
       是详略问题，不是数值错误 —— 不能用"没提"判失败。
    """
    tokens = case.get("key_quantities") or []
    if not tokens:
        pytest.skip("这条样本没标注关键数值")

    hits = recall_of(api, case["question"])
    if not hits:
        pytest.skip("本次召回为空，无从核对")

    snippets = " ".join(hit.get("snippet") or "" for hit in hits)
    traceable = extract_quantities(snippets)

    answer = ask(case["question"])["assistantMessage"]["text"]
    stated = extract_quantities(answer)

    missing = []
    for token in tokens:
        quantity = parse_quantity(token)
        if quantity in stated and quantity not in traceable:
            missing.append(token)

    assert not missing, (
        f"问题「{case['question']}」的回答出现召回片段里没有的数值：{missing}\n"
        f"回答里的数值：{sorted(stated)}\n"
        f"召回片段里的数值：{sorted(traceable)}\n"
        f"→ 这些数可能是模型用自己的训练记忆补的（「5g ↔ 5 克」已归一化，不算）。"
    )


# ══ 3. 引用出现率（3 次采样）═══════════════════════════════════════

def test_citation_present_rate(api, auth_headers, ask):
    """同一问题连问 3 次，统计"回答里出现书名号引用"的比例。

    ⭐ 为什么不做成"必须引用"的单次断言：
      temperature=0.6，同一个 prompt 每次采样不同。单次断言必然时红时绿，
      最后只能被标成 flaky 然后删掉 —— 那是把判据问题误当成代码问题。
      这条测的是**产品承诺的兑现率**（资料块里写了"引用时请说明出自哪一份指南"），
      不是单次行为。

    阈值定成"至少一次"而不是"三次全中"：
      这里要抓的是"承诺完全没兑现"（一次都不引用），
      而不是"每次都必须引用"（那不是当前产品的行为，硬判只会一直红）。
    """
    question = CASES[0]["question"]
    rounds = 3

    answers = [ask(question)["assistantMessage"]["text"] for _ in range(rounds)]
    flags = [bool(cited_titles(answer)) for answer in answers]
    hit_count = sum(flags)

    print(f"\n[{question}] 引用出现率：{hit_count}/{rounds} = {hit_count / rounds:.0%}")
    for index, (flag, answer) in enumerate(zip(flags, answers), 1):
        titles = cited_titles(answer)
        label = f"引用 {titles}" if flag else "未引用"
        print(f"  第 {index} 次：{label}｜{answer[:60]}")

    assert hit_count > 0, (
        f"连问 {rounds} 次都没有出现任何书名号引用。\n"
        f"资料块里明确要求「引用时请说明出自哪一份指南」——"
        f"一次都不出现，说明这条承诺完全没有兑现。\n"
        f"（如果只是偶尔漏引用，这里会通过；这里抓的是**完全不引用**。）"
    )


# ══ 4. RAG 是否生效：可观测性缺陷 ═════════════════════════════════

@pytest.mark.xfail(
    strict=True,
    reason="已知可测性缺陷：响应里没有 ragUsed / sources，RAG 是否生效不可观测",
)
def test_rag_effect_observable(api, auth_headers, ask):
    """响应必须能区分「RAG 给了资料」和「检索失败静默降级」。

    ⚠️ 这是一条**缺陷记录**，不是随手写的红用例：
      RecipeServiceImpl:872  result.put("route", ARTICLE)        // 检索前无条件写
      RecipeServiceImpl:873  result.put("facts", searchKnowledgeBase(question))
      searchKnowledgeBase:892 任何失败 → log.warn + return ""   // 不抛异常
      buildKnowledgeFacts:919 召回为空 → 也 return ""

    于是「召回 3 条」「召回 0 条」「5000 挂了」三种情况的响应**一模一样**。
    knowledgeRoute=article 只说明"路由判成该走 RAG"，不证明"RAG 真的给了资料"。

    strict=True 的含义：哪天真的加了 ragUsed / sources 字段，
    这条会从 XFAIL 变成 XPASS，strict 模式下算失败 —— 提醒你回来更新判据，
    而不是让一条已经失效的用例永远挂着 xfail 装死。
    """
    data = ask("高血压怎么吃")
    message = data["assistantMessage"]

    assert message.get("knowledgeRoute") == "article", (
        "本次没有走 article 路由，说明问题没进入 RAG 分支 —— 这条判据不适用。"
        "如果这行失败，先查意图分类，别急着改本用例。"
    )

    assert "ragUsed" in message or "sources" in message, (
        "响应里没有 ragUsed / sources，无法判断这次回答到底用没用检索资料。\n"
        f"当前 assistantMessage 字段：{sorted(message)}\n"
        "→ 后果：RAG 整段失效时，用户拿到的是没有依据的回答，测试也看不出来。"
    )
