# test_cases/ai_assistant/test_assistant_RAG生成.py
# 【任务：AI 助手 · RAG 生成侧（Generation）】
#
# ══ 这个文件补的是哪一段盲区 ═══════════════════════════════════════
#
#   test_assistant_RAG召回.py  直连 5000，测「资料找得对不对」；
#   本文件                     打 8080，测「找到之后有没有真用上、用得对不对」。
#
#   这两段之间原来还有一个**谁都不管**的缝：8080 到底有没有把检索结果拼进 prompt？
#   以前后端在检索**之前**就写死 knowledgeRoute=article，而检索失败、召回为空
#   都返回同一个空串 ⇒ 「召回 3 条」「召回 0 条」「5000 挂了」三种情况的响应完全一致。
#   也就是说：RAG 整段失效时，用户拿到一份没依据的回答，测试报告全绿。
#
#   2026-10-22 已补观测字段：assistantMessage 增加
#       ragUsed（检索结果是否真的进了 prompt）
#       sources（实际交给模型的资料清单）
#       retrievalStatus（hit / empty / error / ingredient / not_attempted）
#   下面第 4、5 条直接断言这三样，不再靠答案反推。
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
# ══ 六个用例各自测什么 ═══════════════════════════════════════════
#
#   1. test_citation_within_recall       引用不能超出本次召回集（编造依据）
#   2. test_key_quantities_traceable     关键数值必须能在片段里找到（单位归一化后）
#   3. test_citation_present_rate        引用出现率（3 次采样，测承诺兑现率）
#   4. test_rag_effect_observable        正常命中：ragUsed/sources 与独立召回基准一致
#   5. test_rag_empty_recall_is_observable  空召回：ragUsed=false + status=empty
#   6. test_non_rag_routes_are_labeled   查表 / 未尝试：与 RAG 失败可区分
#
# ⚠️ 本文件依赖**两个服务**：5000（召回基准）+ 8080（对话）。
#   5000 没起直接 skip —— 因为那时后端自己也会静默降级，
#   测到的就不是「生成用没用好」，而是「模型自由发挥得好不好」。

import re

import pytest
import requests

from api.kb_api import KbApi
from common.data_loader import load_cases


CASES = load_cases("rag_生成评测_cases.yaml")


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


# ══ 4. RAG 是否生效：可观测字段 ═══════════════════════════════════
#
# 2026-10-22 起后端在 assistantMessage 里回传：
#   knowledgeRoute   ingredient / article（原有）
#   ragUsed          这次检索结果有没有真的拼进 prompt
#   sources          实际交给模型的资料清单（title / section / docId / score / docType）
#   retrievalStatus  hit / empty / error / ingredient / not_attempted
#
# 这三样把下面三种以前**长得一模一样**的情况拆开了：
#   召回 3 条       → ragUsed=true,  status=hit
#   召回 0 条       → ragUsed=false, status=empty
#   5000 挂了/超时  → ragUsed=false, status=error

def test_rag_effect_observable(api, auth_headers, ask):
    """正常命中：ragUsed=true，sources 必须与独立召回基准一致。

    ⭐ 判据同时跨了两个调用：
      · ask() 打 8080 —— 被测系统这次到底把什么资料交给了模型；
      · recall_of() 直连 5000 —— 同题独立查一次 top3，作为基准。
    两者必须一致。如果 8080 检索失败而基准成功，sources 会是空 / 对不上，
    这条就会红 —— 这正是以前生成侧用例抓不到的那个缝。
    """
    question = "高血压怎么吃"
    baseline = recall_of(api, question)
    assert baseline, "独立召回基准为空，无法判断本条判据（先查 5000 的语料/阈值）"

    message = ask(question)["assistantMessage"]
    assert message.get("knowledgeRoute") == "article", (
        "本次没有走 article 路由，说明问题没进入 RAG 分支 —— 先查意图分类。"
    )
    assert message.get("ragUsed") is True, (
        "knowledgeRoute=article 只说明路由判成该走检索；"
        "ragUsed=false 说明检索结果没有真的进 prompt。\n"
        f"retrievalStatus={message.get('retrievalStatus')!r}, sources={message.get('sources')!r}"
    )
    assert message.get("retrievalStatus") == "hit"

    sources = message.get("sources")
    assert isinstance(sources, list) and sources, (
        f"ragUsed=true 但 sources 为空：响应字段 {sorted(message)}"
    )
    assert all(source.get("title") for source in sources), (
        f"sources 里有条目缺 title，模型无法据此标注出处：{sources}"
    )
    assert {source["title"] for source in sources} == {hit["title"] for hit in baseline}, (
        "8080 实际使用的资料与同题直连 5000 的召回基准不一致。\n"
        f"8080 sources : {sorted({s['title'] for s in sources})}\n"
        f"5000 baseline: {sorted({h['title'] for h in baseline})}\n"
        "两条路必须查同一份知识库、同一个 topK。"
    )


def test_rag_empty_recall_is_observable(api, auth_headers, ask):
    """空召回：ragUsed=false + status=empty，不能和「检索挂了」混为一谈。

    样本选「生酮饮食是什么」：它含知识词「生酮」，会进 article 路由，
    但当前权威语料里没有对应章节，5000 稳定返回空列表。
    """
    question = "生酮饮食是什么"
    baseline = recall_of(api, question)
    if baseline:
        pytest.skip(f"语料已覆盖「{question}」，空召回样本失效，请换一个未覆盖的问题")

    message = ask(question)["assistantMessage"]
    assert message.get("knowledgeRoute") == "article", (
        "样本没有进 article 路由，空召回判据不适用 —— 先查意图分类。"
    )
    assert message.get("ragUsed") is False, (
        "没有召回资料，ragUsed 却是 true —— 可观测字段与事实不符。"
    )
    assert message.get("retrievalStatus") == "empty", (
        f"空召回的状态应为 empty，实际 {message.get('retrievalStatus')!r}；"
        "如果为 error，说明 5000 调用失败，不是「没命中」。"
    )
    assert message.get("sources") == [], (
        f"空召回时 sources 必须为空列表，实际 {message.get('sources')!r}"
    )


@pytest.mark.parametrize(
    "question, expected_route, expected_status",
    [
        ("鸡胸肉每100克多少卡", "ingredient", "ingredient"),
        ("减肥期间能吃主食吗", None, "not_attempted"),
    ],
    ids=["精确查表", "意图未进-knowledge"],
)
def test_non_rag_routes_are_labeled(api, auth_headers, ask, question, expected_route, expected_status):
    """没走 RAG 的两种路也要能看出来，不能和「RAG 失败了」混在一起。

    · ingredient    → 走了查表，本来就不该有 RAG 资料；
    · not_attempted → 意图根本没进 knowledge（本例是 advice），RAG 压根没跑。
    两种都必须 ragUsed=false、sources=[]，且 route/status 各自可区分。
    """
    message = ask(question)["assistantMessage"]

    assert message.get("knowledgeRoute") == expected_route, (
        f"「{question}」的 knowledgeRoute 应为 {expected_route!r}，"
        f"实际 {message.get('knowledgeRoute')!r}（intent={message.get('intent')!r}）"
    )
    assert message.get("retrievalStatus") == expected_status, (
        f"「{question}」的 retrievalStatus 应为 {expected_status!r}，"
        f"实际 {message.get('retrievalStatus')!r}"
    )
    assert message.get("ragUsed") is False
    assert message.get("sources") == []
