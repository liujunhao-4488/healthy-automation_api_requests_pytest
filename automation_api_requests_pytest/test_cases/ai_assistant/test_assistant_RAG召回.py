# test_cases/ai_assistant/test_assistant_RAG召回.py
# 【任务：AI 助手 · RAG 检索召回（Retrieval）】
# ══ 这个文件的分工 ═════════════════════════════════════════════════
#
#   一、正样本召回   期望命中的文档，出现在 top-k 里了吗      （量命中率）
#   二、负样本边界   库里没有的东西，有没有硬凑一条出来
#   三、来源隔离     按来源过滤时，会不会串源
#   四、结果契约     每条结果带没带 docId / sourceType / 分数
#   五、确定性       同一个问题问两次，结果是否一个字不差
#
# 数据全部来自 data/kb_golden_cases.yaml，不写死在用例里。
#
# ══ 这份用例和别的那几份的关系（别搞混）══
#   别的 AI 助手用例都打 **Java 后端 8080 的 /assistant/chat**，测的是"助手怎么答"；
#   这一份打 **算法服务 5000 的 /api/kb/search**，测的是"资料找得对不对"。
#   前者要登录拿 token，后者不要 —— 这是**故意分开**的：
#   两件事混在一条链路上测，出错时你分不清是"检索没找到"还是"Java 没转发"。
#
# ⭐ 为什么"召回"值得单独测
#   RAG 的答案质量 = 召回质量 × 生成质量。这份用例只装**前半段**的仪表盘：
#   检索悄悄返回空、助手悄悄退化成裸模型回答，谁也不知道。
#
# ⚠️ 生成那半段（模型会不会照着资料说）**至今没有任何用例覆盖**（2026-10-18 核对）。
#   本文件写于 10-16 时以为"别处已经覆盖了"，那是错的：
#   越狱/注入/意图/上下文那几份判的是"该不该这么答"，没有一条判"这句依据来自召回资料"。
#   ⚠️ 更要紧的是**两条链路中间的盲区**：本文件直连 5000 打检索，
#   而聊天用例打 8080 —— "8080 到底有没有把检索结果用上"这一段，两边都不管：
#     RecipeServiceImpl:873  result.put("facts", searchKnowledgeBase(question))
#     searchKnowledgeBase 任何失败都 catch 成 log.warn + 返回空串（不抛异常）。
#   于是「召回 3 条」「召回 0 条」「5000 挂了」三种情况的响应**完全一致**
#   （knowledgeRoute 都是 article，它在检索**之前**就无条件写入了）。
#   也就是说：RAG 整段失效时，用户拿到一份没依据的回答、测试报告全绿。
#
# ══ 为什么判据是"文档级"而不是"段落级" ══
#   段落边界随切块参数变化；把期望值钉在段落上，一调 CHUNK_SIZE 全部失效，
#   那测的就是"切块参数"，不是"召回能力"。文档标题则是稳定的。

import pytest
import requests

from api.kb_api import KbApi
from common.data_loader import load_cases

KB_CASES = load_cases("kb_golden_cases.yaml")
POSITIVE_CASES = [c for c in KB_CASES if c["kind"] == "positive"]
NEGATIVE_CASES = [c for c in KB_CASES if c["kind"] == "negative"]


@pytest.fixture(scope="module", autouse=True)
def kb_service_up():
    """开跑前先确认算法服务（5000）在。

    ⚠️ 这份用例改打算法服务，而**别的 AI 用例只需要 Java 后端** ——
       于是"只起了 8080"的人跑全量时会撞上这里。
       所以给一句人话 + 怎么起，而不是让二十多条用例各抛一次 ConnectionError
       （那种满屏红会让人以为是代码坏了，其实是环境没起）。

    用 skip 而不是 fail：这是**环境依赖**，不是被测系统的缺陷 ——
       把环境问题算进失败率，评测数字就不可信了。

    ⚠️ 这里自己 new 一个 client，**没用 api 夹具** —— 因为 api 是 function 级、
       本夹具是 module 级，pytest 不允许"作用域小的夹具被作用域大的夹具依赖"。
       探活跟具体用例无关，本来也不该借用用例的夹具。
    """
    client = KbApi()
    try:
        resp = client.stats()
    except requests.exceptions.RequestException as exc:
        pytest.skip(
            f"算法服务未启动（{client.base_url}）—— "
            f"先跑 algorithm/.venv/Scripts/python.exe algorithm/app.py。原因：{exc}"
        )
    assert resp.status_code == 200, f"算法服务探活失败：HTTP {resp.status_code}"


def case_id(case):
    """中文用例名 —— 直接用问题本身，失败时一眼看出是哪道题。"""
    return case["question"]


def _params(cases):
    """把数据集转成参数化参数；标了 known_defect 的挂上 xfail(strict=True)。

    机制和 test_assistant_意图标签.py._params 完全一样：
      · 缺陷还在 → XFAIL（套件整体仍绿）；
      · 检索修好了 → 断言自然通过 → XPASS → strict 判**失败** → 这就是"该摘标记了"的信号。
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


def _search(api, query, **kwargs):
    """发一次检索，返回 data 列表（顺带把"接口成功"判掉，用例不重复写）。"""
    body = api.assert_ok(api.kb.search(query, **kwargs), "知识库检索应成功")
    assert isinstance(body["data"], list), "data 必须是列表（没命中时是空列表，不能是 null）"
    return body["data"]


# ==================== 一、正样本召回：该命中的文档进了 top-k 吗 ====================

@pytest.mark.parametrize("case", _params(POSITIVE_CASES), ids=case_id)
def test_question_hits_expected_doc(api, case):
    """问一个库里确实有答案的问题，期望的那篇指南要出现在 top-k 里。

    命中率 = 通过数 ÷ 用例总数，藏在参数化里，不用另写统计脚本。

    ══ 红了怎么修（三种原因，修法完全不同）══
      · 检索没找到   → 改检索（algorithm/kb_retriever.py 的 tokenize / MIN_SCORE），
                       或看是不是语料切坏了
      · 语料里没有   → 该补语料（往「权威文件/」加 PDF，重跑 ingest_authority.py）
      · 期望标错了   → 改数据文件里的 expect_doc —— 但**要先确认是前两种之外的**
    别顺手改断言去迁就现状 —— 那等于把体温计砸了当退烧。

    ⚠️ 这里断了 top-k 命中，**不等于**"用户能拿到正确答案"。
       命中了只说明资料递到了模型面前；模型会不会照着说，是另一件事（另一份用例管）。
    """
    hits = _search(api, case["question"])

    docs = [hit["title"] for hit in hits]
    assert case["expect_doc"] in docs, (
        f"问「{case['question']}」应该命中《{case['expect_doc']}》，"
        f"实际 top-{len(docs)} 是：{docs or '（空）'}；"
        f"若这是检索规则的已知盲区，请在数据文件里给它标 known_defect"
    )


# ==================== 一之二、章节级召回：文档对了，章节对吗 ====================
#
# ⭐ 这一节是 2026-10-18 新加的，起因是一次**用户实测**：
#   问「高血压怎么吃」，助手答得头头是道，但内容其实是模型自己的训练记忆。
#   查下来 —— 检索确实跑了（后端日志 route=article, facts 832 字），
#   但 top-3 召回的是：
#       [9.17] 二、疾病特点与分型（高血压定义/分级）
#       [8.89] 一、前言（患病率统计）
#       [8.86] 七、冲任失调证（当归羊肉萝卜汤）
#   正确的「三、食养原则和建议」排第 4（8.59），被 topK=3 截断。
#
#   ⚠️ 关键点：这三条的 title **全是《成人高血压食养指南》**——
#      也就是说只判文档级的话，这条用例是**绿的**，
#      而用户拿到的回答里一条"怎么吃"的资料都没有。
#      文档级判据测的是"有没有找到这本书"，不是"有没有找到那一段"。
#
#   所以章节级判据不是锦上添花，是补一个**会红的观测点**。

SECTION_CASES = [c for c in POSITIVE_CASES if c.get("expect_section")]


@pytest.mark.parametrize("case", _params(SECTION_CASES), ids=case_id)
def test_question_hits_expected_section(api, case):
    """命中的那几条里，必须有**同文档且落在期望章节**的。

    判据用关键词子串（如「食养原则」）而不是完整标题「三、食养原则和建议」：
    序号和措辞会随 PDF 版本变，子串对重排版不敏感，但仍然是章节级定位。

    ══ 红了怎么看 ══
      · 文档对、章节错  → 检索的**排序**问题，不是语料问题。典型是查询词面
                         与语料用词对不上（口语问法最明显），见 kb_retriever.py
                         的 INTENT_EXPANSION_RULES。
      · 文档都不对      → 先看第一节那条文档级用例，可能根因在召回而非排序。

    ⚠️ 这条比文档级**更严**，但不重复：文档级守的是"书找没找对"，
       章节级守的是"页翻没翻对"。两级都绿，资料才算真的递到了模型面前。
    """
    hits = _search(api, case["question"])

    matched = [
        hit for hit in hits
        if hit["title"] == case["expect_doc"]
        and case["expect_section"] in (hit.get("section") or "")
    ]
    if not matched:
        actual = [(h["title"], h.get("section", ""), h["score"]) for h in hits]
        pytest.fail(
            f"问「{case['question']}」应命中《{case['expect_doc']}》的"
            f"「{case['expect_section']}」一节，实际 top-{len(hits)} 是：{actual}；"
            f"文档对但章节错 = 排序问题（看 INTENT_EXPANSION_RULES），不是语料缺失"
        )


# ==================== 二、负样本边界：库里没有的，别硬凑 ====================

@pytest.mark.parametrize("case", _params(NEGATIVE_CASES), ids=case_id)
def test_irrelevant_question_returns_nothing(api, case):
    """库里没有对应内容的问题，必须返回**空列表**，不能硬凑一条低分噪声。

    ⭐ 这条测的是"边界守护"能力线，也是 MIN_SCORE 阈值和查询覆盖率闸门的看门人：
       BM25 只要有**一个字**对上就会给分，于是
       「如何用 Python 写一个快速排序」能靠一个"如何"在健康语料里捞出东西来。
       返回空比返回一条错的更有价值 —— 下游拿到空，知道"没有依据"，
       可以如实说不知道；拿到一条错的，模型会当成事实用。

    ⚠️ 阈值调高会误伤低分但正确的召回，调低会放过噪声。
       所以这条红了**不要直接改阈值**，先看第一节（正样本）有没有被一起改坏 ——
       两边一起看才叫调参，只看一边叫拆东墙补西墙。

    2026-10-18 这次红的就是这条思路的反例：语料变长后负样本分数涨到 9.28，
    而正样本最低只有 12.20 —— 空档只剩 2.9，把阈值抬到 10 会连带砍掉
    「尿酸高可以吃豆腐吗」这类 6~8 分的正当问题。最后改的是**病因**
    （查询侧停用词 + COVERAGE_MIN 覆盖率闸门），阈值 8.0 没动。
    """
    hits = _search(api, case["question"])

    assert hits == [], (
        f"「{case['question']}」与营养健康无关，库里也没有对应内容，"
        f"却召回了 {len(hits)} 条："
        f"{[(h['title'], h['score']) for h in hits]} —— "
        f"按顺序查三处：① STOPWORDS 里漏了这句的虚词（虚词会垫出虚高分）；"
        f"② COVERAGE_MIN 太松（离题问句的特征是「只有一两个词偶然对上」）；"
        f"③ MIN_SCORE 太低"
    )


# ==================== 三、来源隔离：按来源过滤时不能串源 ====================

def test_authority_filter_returns_only_authority(api):
    """sourceType=authority 时，结果里不许混进站内文章。

    ⚠️ 这条防的是"过滤参数写着好看、实际上没生效"——
       传了参数却返回全部，是最难查的那种错（接口不报错、结果看着也像对的）。
    """
    hits = _search(api, "高血压怎么吃", top_k=5, source_type="authority")

    bad = [h for h in hits if h["sourceType"] != "authority"]
    assert hits, "权威源应当能召回「高血压怎么吃」，返回空说明过滤把好结果也滤掉了"
    assert not bad, f"过滤 authority 却返回了别的来源：{[(h['title'], h['sourceType']) for h in bad]}"


def test_article_filter_returns_only_article(api):
    """sourceType=article 时，结果里不许混进权威指南（反向也要成立）。"""
    hits = _search(api, "高血压怎么吃", top_k=5, source_type="article")

    bad = [h for h in hits if h["sourceType"] != "article"]
    assert not bad, f"过滤 article 却返回了别的来源：{[(h['title'], h['sourceType']) for h in bad]}"


def test_default_scope_is_authority(api):
    """**不传 sourceType** 时，走的是默认范围 —— 当前定为只查权威源。

    ⚠️ 这条是**哨兵**：它盯的是"默认值"这个决定本身。
       哪天有人把默认改成全部（或改了配置文件），它会红，
       提醒你"默认范围变了，这件事得是有意为之，不能是顺手改的"——
       因为默认范围直接决定用户拿到的是权威建议还是模板文。
    """
    hits = _search(api, "高血压怎么吃", top_k=5)

    bad = [h for h in hits if h["sourceType"] != "authority"]
    assert not bad, (
        f"不传 sourceType 时应只查权威源，实际混进了："
        f"{[(h['title'], h['sourceType']) for h in bad]} —— "
        f"若确实要有意改成默认查全部，请同时更新这条用例和 kb_retriever 的注释"
    )


def test_all_scope_covers_both_sources(api):
    """sourceType=all 能同时覆盖两个源 —— 证明文章索引确实还在（没被删掉）。

    它和上面那条配对：一个证明"默认只用权威源"，
    一个证明"站内文章的路还留着，随时能调出来"。
    """
    body = api.assert_ok(api.kb.stats(), "看索引构成应成功")
    kinds = {h["sourceType"] for h in _search(api, "高血压怎么吃", top_k=20, source_type="all")}

    assert body["data"]["articleChunks"] > 0, "站内文章索引不该是空的"
    assert kinds <= {"authority", "article"}, f"出现了未知来源：{kinds}"


# ==================== 四、结果契约：每条结果必须能追溯 ====================

def test_each_hit_carries_traceable_fields(api):
    """每条召回都要带 docId / title / section / sourceType / score / snippet。

    ⭐ 为什么这不算"测字段这种小事"：
       **没有 docId 就无法断言"问 X 应该命中文档 Y"** —— 召回率根本测不了。
       没有 sourceType 就无法判断"这条答案该不该标权威来源"。
       没有 section 就无法在回答里标注"依据《XX指南》第三章"。
       这几个字段是**为测试和溯源而加的，不是可选项**。
    """
    hits = _search(api, "高血压怎么吃", top_k=3)
    assert hits, "这条用例需要至少一条召回结果，空的话先看第一节"

    for hit in hits:
        assert hit.get("docId"), f"缺 docId，召回无法回溯到原文：{hit}"
        assert hit.get("title"), f"缺 title：{hit}"
        assert hit.get("section"), f"缺 section，回答里没法标注依据出自哪一章：{hit}"
        assert hit.get("sourceType") in ("authority", "article"), f"sourceType 非法：{hit}"
        assert isinstance(hit.get("score"), (int, float)) and hit["score"] > 0, f"score 非法：{hit}"
        assert hit.get("snippet"), f"缺 snippet，没法给用户看依据原文：{hit}"


def test_scores_are_sorted_desc(api):
    """返回结果必须按分数降序 —— 拿第一条当"最相关"是下游默认假设。

    这条红了说明排序逻辑坏了；上游（Java 侧拼 prompt）会以为 top-1 最相关，
    实际可能是随机的 —— 而且**不会报任何错**，是典型的静默失效。
    """
    hits = _search(api, "高血压怎么吃", top_k=5)
    scores = [h["score"] for h in hits]

    assert scores == sorted(scores, reverse=True), f"分数没有降序：{scores}"


def test_topk_limits_result_count(api):
    """topK 真的生效：要几条给几条（不超过）。"""
    one = _search(api, "高血压怎么吃", top_k=1)
    five = _search(api, "高血压怎么吃", top_k=5)

    assert len(one) <= 1, f"topK=1 却返回 {len(one)} 条"
    assert len(five) <= 5, f"topK=5 却返回 {len(five)} 条"
    assert len(one) <= len(five), "要得多反而返回得少，topK 多半没生效"


# ==================== 五、确定性：可测性的基石 ====================

def test_same_question_same_result(api):
    """同一个问题问两次，结果必须**一个字不差**。

    ⭐ 这是"能写 == 断言"的前提。检索用的是本地 BM25 + 字符 bigram，
    没有随机性；一旦哪天引入了向量检索或随机采样而忘了固定种子，
    这条会红 —— 它守的是"这份用例集还能不能继续用 == 断言"这件事本身。
    """
    first = _search(api, "痛风患者要避免吃哪些食物", top_k=3)
    second = _search(api, "痛风患者要避免吃哪些食物", top_k=3)

    assert first == second, "同一问题两次检索结果不一致 —— 检索引入了随机性？"


def test_unknown_source_type_is_rejected(api):
    """非法的 sourceType 要**明确报错**，不能当成"没传"悄悄走默认。

    静默降级是最难查的错：传错了参数、结果看着正常，你以为过滤生效了。
    """
    resp = api.kb.search("高血压怎么吃", source_type="bogus")

    assert resp.status_code == 200, "契约错误应当用业务 code 表达，不是 HTTP 5xx"
    assert resp.json().get("code") == 400, (
        f"非法 sourceType 应返回业务 code=400，实际 {resp.json().get('code')}"
    )


def test_blank_query_is_rejected(api):
    """空 query 要报错，不能拿空串去检索（空串检索出的东西毫无意义）。"""
    resp = api.kb.search("   ")

    assert resp.status_code == 200
    assert resp.json().get("code") == 400
    assert resp.json().get("data") == []
