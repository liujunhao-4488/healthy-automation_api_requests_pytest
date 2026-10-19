# -*- coding: utf-8 -*-
"""
知识库检索器 —— RAG 里的那个 "R"（Retrieval）
======================================================================
职责只三件：
  1. 把语料切成块（chunk），每块记住自己来自哪篇文章的哪一节
  2. 给所有块建一份倒排索引
  3. 收到问题，按 BM25 打分，返回得分最高的 top-k 块

⭐ 双源（2026-10-16 起）
----------------------------------------------------------------------
  语料现在有两个来源，**混在同一份索引里，但每条都带 sourceType 标记**：

    sourceType="authority"  国家卫健委食养指南 8 篇（ingest_authority.py 产出）
                            → 权威答案的依据。1101 块。
    sourceType="article"    库里的 health_article 132 篇
                            → 站内科普文，质量参差（含 120 篇模板文）。

  为什么放在同一份索引、只加标记，而不是建两份索引：
    · 检索质量能直接横向对比（同一个问题，两个源各召回什么）；
    · search(source_type=...) 一个参数就能按源过滤，实现了"权威优先"；
    · 分两份索引的话，"某问题权威源没命中、站内文章命中了"这种跨源比较
      反而要跑两遍才知道。

为什么不用 langchain / faiss / 向量库
----------------------------------------------------------------------
  · 规模：约 1500 块。这个量级下，向量检索相对关键词检索的召回提升几乎为零，
    却要多维护一个 embedding 服务和一份向量索引。
  · 更要紧的是**可测**：召回率正是我们要测的东西。框架会把"为什么召回了
    这一块、为什么没召回那一块"藏进黑盒；自己写，每个 token 的分数都能打出来。

  🔁 将来要换向量检索，只需改 tokenize() 一处 —— build / search / 返回结构
     全都不用动，golden set 的测试代码也一个字不用改。这叫消融实验。

为什么用「字符 bigram」当词，而不是 jieba 分词
----------------------------------------------------------------------
  中文没有空格，标准 BM25 必须先分词。但这里刻意不分词，两个理由：
    · 零依赖：不用装 jieba；
    · 更要紧的是**确定性**——分词器版本不同、词典不同，切出来的词就不同，
      召回结果跟着变，"同样输入永远同样输出"这条就没了，断言没法写。
  字符 bigram 是它的零依赖近似：「控糖饮食」→ 控糖 / 糖饮 / 饮食。
  对"短查询 + 短文档"这种场景，效果和分词接近。

⚠️ 这个模块**不依赖 Flask**；只有 load_articles_from_db() 需要 pymysql，
    load_authority_chunks() 只读本地 JSON。两者都是懒加载，
    import 本模块本身不需要任何第三方包 —— 方便单独跑测试喂假数据。
"""

import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict

# ══════════════════════════════════════════════════════════════════════
# 可调参数 —— 想调召回效果，只动这一段
# ══════════════════════════════════════════════════════════════════════
CHUNK_SIZE = 400        # 每块目标字数（仅用于 article 源，权威源在 ingest 时已切好）
CHUNK_OVERLAP = 80      # 相邻块之间重叠的字数
DEFAULT_TOP_K = 3       # 默认返回几块
BM25_K1 = 1.5           # BM25 词频饱和参数（常规取值 1.2~2.0）
BM25_B = 0.75           # BM25 长度归一化参数（常规取值 0.75）

# ⭐ 分数下限：低于它的召回直接丢掉，返回空列表。
#   为什么需要它：BM25 只要有**一个字**对上就会给分，于是一个编程问题
#   （「如何用 Python 写一个快速排序」）也能在健康语料里捞出一条 ——
#   命中它的词是「如何」。返回空比返回一条错的更有价值：
#   下游拿到空，知道"没有依据"，可以如实说不知道；拿到一条错的，
#   模型会当成事实用。
#
#   8.0 是 2026-10-16 实测定的（当时负样本最高 5.91、正样本最低 12.10）。
#   ⚠️ 2026-10-18 复测发现**这个空档已经不成立了**：语料从 1101 块长到 1165 块后，
#      负样本「如何用 Python 写一个快速排序」到了 9.28（靠「一个」5.87 +「如何」3.41），
#      正样本最低降到 12.20 → 空档只剩 2.92，而 9.28 > 8.0 就漏了。
#      当时的备选是"把阈值抬到 10.0"，**没有采用** —— 实测抬到 10 会连带砍掉
#      得分 6~8 的正当问题（「怎样减肥最有效」6.13、「尿酸高可以吃豆腐吗」7.14），
#      而且「帮我写一篇800字作文」仍以 9.12 分继续漏（它靠的是「800」）。
#      一个全局阈值分不开"分低但正确"和"分中但错误"，所以改治**病因**：
#      STOPWORDS 挤掉虚词的虚高分，COVERAGE_MIN 判"这句话到底是不是在问本语料"。
#      阈值本身维持 8.0 不动（它只该管"词都罕见但分数仍很低"这一种情况）。
#   语料换了要重测（golden set 就是干这个的）。
MIN_SCORE = 8.0

# ⭐ 查询侧停用词：纯虚词，对"该不该召回"零指示作用。
#
#   为什么是**查询侧**而不是索引侧：剔索引侧会改掉每个块的 length 和 avg_length，
#   BM25 的长度归一化跟着整体漂移 —— 那等于顺手改了另一件事，正样本分数会一起动。
#   只在查询里剔，索引一个字不动，改动面最小。
#
#   为什么"如何/一个"必须剔：字符 bigram 会把它们切成独立的词，而它们在
#   膳食指南里恰好有一定词频（一个 df=11、如何 df=21）。一个编程问题于是能靠
#   这两个词拿到 9.28 分 —— 这是**虚词的虚高分**，不是任何真实相关性。
#
#   ⚠️ 加词前请先跑 golden set：剔词只会让分数下降（不会上升），
#      所以风险全在"把正当问题剔到阈值以下"。像「多少」就不该进来 ——
#      「每天吃盐不能超过多少」离不开它。
#      「可以 / 应该」也**刻意不收**：10-18 实测收进来之后，
#      「尿酸高可以吃豆腐吗」从 12.07 掉到 7.14，被阈值一刀砍成空 ——
#      这两个词在语料里的 df 不高，反而真的在区分"能不能吃"这类问句。
STOPWORDS = frozenset({
    "如何", "何用", "怎么", "怎样", "么样", "什么", "为什", "哪些",
    "一个", "一篇", "是否", "请问", "帮我", "一下",
})

# ⭐ 覆盖率闸门：查询里**至少要有这么大比例的词**在语料中出现过，否则整句判"没依据"。
#
#   为什么阈值分不开、覆盖率能分开（2026-10-18 实测，权威源 1165 块）：
#     · 离题：「如何用 Python 写一个快速排序」17%、「帮我订一张去上海的机票」20%、
#             「帮我写一篇800字作文」25%
#     · 正题：「怎样减肥最有效」60%、「什么食物含钾高」60%、「尿酸高可以吃豆腐吗」57%、
#             「高血压患者每天吃盐不能超过多少」93%
#   离题问句的共同点不是"分低"，而是**只有一两个词偶然对上**（机票靠「上海」、
#   作文靠「800」）。分低但正确的正题则相反：**大半的词都在这套语料里**。
#   0.3 落在两组之间的空档（离题 ≤25%、正题 ≥57%），两边各留 5 个百分点以上。
#
#   ⚠️ 它和 MIN_SCORE 是**两道闸**，各管一种病，缺一不可：
#      · 只有覆盖率：一个查询词全对上但全是很常见的词（「吃什么好」）照样放行；
#      · 只有分数：本文件 10-18 这次踩的就是这个坑（9.28 硬闯 8.0）。
COVERAGE_MIN = 0.3

# ⭐ 查询扩写：把「用户的口语」翻译成「语料的用词」（2026-10-18 新增）
#
# 要解决的问题（实测，不是推测）：
#   用户问「高血压怎么吃」——真实口语，但 BM25 是**词面**匹配：
#     tokenize → 高血 / 血压 / 压怎 / 怎么 / 么吃
#     「怎么」被停用词剔掉，「压怎 / 么吃」在语料里几乎不出现
#   → 真正参与打分的只剩「高血 / 血压」两个词，
#     于是**被测文档的排序完全由"高血压"这三个字的词频决定**。
#     噪声在"高血压"最密集的小节里最高：「二、疾病特点与分型」（定义/分级，短且密）
#     9.17 分夺冠，「一、前言」（患病率）8.89 第二，
#     而真正答案所在的「三、食养原则和建议」只有 8.59，排第 4，被 topK=3 截断。
#
#   也就是说：文档对了、章节全错 → 模型手上没有一句"怎么吃"，
#   只能拿训练记忆编（实测回答里的"约一啤酒瓶盖"在语料里 0 命中）。
#
# 修法：识别出"在问饮食怎么做"的意图短语，把该意图在**语料里的说法**追加进打分词集合。
#   同一句话换成「高血压饮食要注意什么」就能命中正确章节 ——
#   差别只在"饮食"两个字，说明缺的不是语料，是**词面对齐**。
#
# ⚠️ 三个刻意约束：
#   ① **只加打分词，不加覆盖率分母**。覆盖率闸门（COVERAGE_MIN）是用来判
#      "这句话到底是不是在问本语料"的，分母里掺进我们自己扩写的词，
#      等于自己给自己凑覆盖率，离题问句会被放进来。所以扩写词在 search 里
#      只喂打分，coverage 仍然按用户原话的词算。
#   ② **触发词选"整段短语"，不选单字**。「吃」不能当触发词 —— 它会把
#      「痛风患者要避免吃哪些食物」也扩写一遍，而那条本来命中得挺好。
#   ③ 扩写词限定在**主题词**（食养/膳食/饮食/原则），不放具体数值词。
#      数值命中必须靠用户自己说出的词，否则"每天吃盐多少"会靠扩写拿到通用分。
INTENT_EXPANSION_RULES = (
    (
        # 触发短语：口语里"问怎么吃"的各种说法
        (
            "怎么吃", "如何吃", "吃什么", "怎么饮食", "饮食注意",
            "要注意什么", "饮食建议", "怎么调理", "怎么安排", "怎么选",
        ),
        # 扩写词：慢病指南里表达同一意图的固定说法（第三章标题就是「食养原则和建议」）
        ("食养", "膳食", "饮食", "原则"),
    ),
)

SOURCE_AUTHORITY = "authority"   # 国家卫健委食养指南
SOURCE_ARTICLE = "article"       # 站内 health_article

# ⭐ 默认只检索权威源（2026-10-16 拍板）。
#   理由：站内 133 篇里 120 篇是同一套模板生成的（切出 240 块），
#   混合检索时它们会靠"怎么安排""能不能真正落地"这类通用词抢走 top-1
#   （实测：「糖尿病人的主食怎么安排」top-3 全是模板文）。
#   要不要放开成全部，由调用方显式传 sourceType="all" 决定。
DEFAULT_SOURCE_TYPE = SOURCE_AUTHORITY
ALL_SOURCE_TYPES = (SOURCE_AUTHORITY, SOURCE_ARTICLE)
# ══════════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTHORITY_FILE = os.path.join(BASE_DIR, "kb_data", "authority_chunks.json")

_HAN = re.compile(r"[\u4e00-\u9fff]+")   # 连续汉字段
_ASCII_WORD = re.compile(r"[a-z0-9]+")   # 连续英文/数字
_WHITESPACE = re.compile(r"\s+")


def tokenize(text):
    """
    把一段文字切成检索用的「词」列表。

    中文 → 字符 bigram（相邻两字一组）；英文/数字 → 整词小写。
    例：
        '控糖饮食指南'  → ['控糖', '糖饮', '饮食', '食指', '指南']
        'BMI 怎么算'    → ['bmi', '怎么', '么算']

    ⚠️ 单字汉字段要单独保留：句子末尾常出现单独一个汉字（如 "…吃吗？好"），
       bigram 切不出来，丢掉就白丢了。
    """
    if not text:
        return []
    lowered = text.lower()

    tokens = list(_ASCII_WORD.findall(lowered))
    for segment in _HAN.findall(lowered):
        if len(segment) == 1:
            tokens.append(segment)
        else:
            for i in range(len(segment) - 1):
                tokens.append(segment[i:i + 2])
    return tokens


def split_into_chunks(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    把长正文切成**带重叠**的块。

    为什么必须有重叠：
        不留重叠的话，一句话可能正好被切成两半 —— 前半句落在块 A 的尾部、
        后半句落在块 B 的开头，两边都匹配不上完整语义，等于这句话没被收录。
        代价是索引会略大一点，在千级块的规模下完全无所谓。

    切点优先落在自然断点（换行 / 。！？；）上，断不了才硬切。
    """
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    pieces = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            # 从窗口末尾往前找最近的自然断点
            cut = max(
                window.rfind("\n"), window.rfind("。"), window.rfind("；"),
                window.rfind("！"), window.rfind("？"), window.rfind("."),
            )
            # 断点太靠前就放弃（否则每块会变得很短，等于把文档切碎）
            if cut > size // 2:
                end = start + cut + 1
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        # 下一块从 end 往前退 overlap 个字，形成重叠区
        start = max(end - overlap, start + 1)
    return pieces


class _Chunk:
    """
    一个文本块。doc_id / title / section 是**元数据**，用于把召回结果回溯到原文。

    ⚠️ 索引用的文本（search_text）和展示用的文本（text）是**两个东西**：
       索引时把「书名 + 章节名 + 正文」拼起来 —— 因为「减钠增钾」「高血压」
       这类最关键的词往往只出现在书名/章节名里，正文反而一次都不提。
       但展示给用户的 snippet 只取正文，免得回一条"成人高血压食养指南 一、前言"。
    """

    __slots__ = ("doc_id", "title", "section", "source_type",
                 "text", "search_text", "term_freq", "length")

    def __init__(self, doc_id, title, text, section="", source_type=SOURCE_ARTICLE):
        self.doc_id = doc_id
        self.title = title
        self.section = section or ""
        self.source_type = source_type
        self.text = text
        self.search_text = "\n".join(
            part for part in (title, self.section, text) if part
        )
        self.term_freq = Counter(tokenize(self.search_text))   # 词 → 出现次数
        self.length = sum(self.term_freq.values())             # 块的总词数（BM25 长度归一化用）


class KnowledgeRetriever:
    """
    检索器。用法：

        r = KnowledgeRetriever()
        r.build_chunks(chunks)                    # chunks 是已规范化的块列表
        hits = r.search("高血压该怎么吃", top_k=3)

    返回的每个 hit 都带 docId —— ⭐ 这正是"召回率能不能测"的前提：
    没有它就无法断言"问 X 应该命中文档 Y"。
    """

    def __init__(self):
        self.chunks = []
        self.inverted = defaultdict(set)   # 词 → 包含它的块下标集合
        self.doc_freq = defaultdict(int)   # 词 → 出现在多少个块里（算 IDF 用）
        self.avg_length = 0.0

    # ---------------------------------------------------------------- build
    def build_chunks(self, chunks):
        """
        用一批**已规范化**的块重建索引。返回块数。

        chunks 的每一项是 dict：
            {docId, title, section?, sourceType?, text}

        ⚠️ 会做一次**按正文的去重**：语料里存在"不同 id、正文一字不差"的文章
           （实测 health_article 的模板文有成对重复）。不去重的话，同一段内容
           会以多个块的身份同时挤进 top-k，把真正有区分度的结果挤出去。
        去重按**首次出现**保留，顺序稳定 → 结果确定。
        """
        self.chunks = []
        seen_texts = set()
        self.duplicates_dropped = 0
        for item in chunks or []:
            text = (item.get("text") or "").strip()
            if not text:
                continue
            # 只按正文去重，**不把书名/章节名算进去** ——
            # 否则"同一段食谱出现在两个地区章节里"会被误判成两条。
            # 用 sha1 而不是内置 hash()：hash() 对字符串带随机盐，
            # 跨进程不稳定，会让"两次运行结果一致"这条保证失效。
            fingerprint = hashlib.sha1(text.encode("utf-8")).hexdigest()
            if fingerprint in seen_texts:
                self.duplicates_dropped += 1
                continue
            seen_texts.add(fingerprint)
            self.chunks.append(_Chunk(
                doc_id=item.get("docId"),
                title=(item.get("title") or "").strip(),
                text=text,
                section=item.get("section") or "",
                source_type=item.get("sourceType") or SOURCE_ARTICLE,
            ))

        # 重建倒排索引
        self.inverted = defaultdict(set)
        self.doc_freq = defaultdict(int)
        for index, chunk in enumerate(self.chunks):
            for term in chunk.term_freq:          # Counter 的键天然去重
                self.inverted[term].add(index)
                self.doc_freq[term] += 1

        self.avg_length = (
            sum(chunk.length for chunk in self.chunks) / len(self.chunks)
            if self.chunks else 0.0
        )
        return len(self.chunks)

    def build(self, articles):
        """便捷入口：直接用 health_article 的文章列表建索引。"""
        return self.build_chunks(articles_to_chunks(articles))

    # --------------------------------------------------------------- search
    def search(self, query, top_k=DEFAULT_TOP_K, source_type=DEFAULT_SOURCE_TYPE):
        """
        按 BM25 打分，返回 top-k 块。

        BM25 一句话解释：一个词在**这一块里出现得多**（tf）、而在**别的块里
        很少见**（idf），它就越是这块的"特征词"，得分越高；同时用块长度做归一化，
        免得长块光靠字多就占便宜。

        source_type：
            "authority"（默认）只查卫健委指南
            "article"           只查站内文章
            "all" 或 None       两个源都查
                            用于实现"权威优先"，以及分别测两个源的召回率。

        返回：[{docId, title, section, sourceType, score, snippet}, ...]，按分数降序。
        没有命中时返回空列表 —— **调用方必须处理空列表**（这是 RAG 最常见的失败形态）。

        返回空列表有四种原因，排查时先分清是哪一种：
          1. 索引还没建（chunks 为空）
          2. 查询剔掉停用词后一个词都不剩（全是虚词）
          3. 覆盖率不达标（COVERAGE_MIN）—— 这句话不像在问本语料
          4. 最高分低于 MIN_SCORE —— 词对上了，但只是偶然撞上
        """
        if not self.chunks:
            return []

        # 剔停用词：虚词在语料里有词频，会给离题问题垫出一份虚高的分。
        # 详见 STOPWORDS 上的注释（为什么是查询侧、为什么"如何/一个"必须剔）。
        query_terms = set(tokenize(query)) - STOPWORDS
        if not query_terms:
            return []

        # 查询扩写：只影响**打分**，不参与下面的覆盖率分母（见 INTENT_EXPANSION_RULES）。
        score_terms = set(query_terms)
        for triggers, extras in INTENT_EXPANSION_RULES:
            if any(trigger in query for trigger in triggers):
                for extra in extras:
                    score_terms |= set(tokenize(extra)) - STOPWORDS

        # 候选范围：按来源过滤时，df 和平均长度也都只按这个子集算，
        # 否则分数会被另一个源的块大小拖偏（两个源块长不一样）。
        wanted = None if source_type in (None, "all") else source_type
        candidate_indexes = [
            index for index, chunk in enumerate(self.chunks)
            if wanted is None or chunk.source_type == wanted
        ]
        if not candidate_indexes:
            return []
        candidate_set = set(candidate_indexes)

        total = len(candidate_indexes)
        avg_length = (
            sum(self.chunks[index].length for index in candidate_indexes) / total
        ) or 1.0

        scores = defaultdict(float)
        # 覆盖率按"在**本次检索范围**里出现过的查询词"算，而不是按全索引算 ——
        # 只查权威源时，一个只存在于站内文章里的词不该算"覆盖到了"。
        covered_terms = set()
        for term in score_terms:
            hit_indexes = self.inverted.get(term)
            if not hit_indexes:
                continue
            in_scope = [index for index in hit_indexes if index in candidate_set]
            if not in_scope:
                continue
            # ⚠️ 只有**用户原话**里的词才算覆盖；扩写词只贡献分数。
            #    否则"我自己加的食养/膳食"会把覆盖率垫高，离题问句也能过关。
            if term in query_terms:
                covered_terms.add(term)
            df = len(in_scope)
            # BM25 的 IDF（加 1 是为了在 df 很大时也不出现负数，小语料里很常见）
            idf = math.log(1 + (total - df + 0.5) / (df + 0.5))
            for index in in_scope:
                chunk = self.chunks[index]
                tf = chunk.term_freq[term]
                denominator = tf + BM25_K1 * (
                    1 - BM25_B + BM25_B * chunk.length / avg_length
                )
                scores[index] += idf * tf * (BM25_K1 + 1) / denominator

        # 覆盖率闸门：详见 COVERAGE_MIN 上的注释。
        # 放在打分之后是为了用**范围内**的命中判定，不多扫一遍索引；
        # 千级块这个规模的浪费可以忽略。
        coverage = len(covered_terms) / len(query_terms)
        if coverage < COVERAGE_MIN:
            return []

        # 分数相同的按块下标排，保证结果稳定（同样的输入永远同样的输出）
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))

        results = []
        for index, score in ranked[:max(0, top_k)]:
            if score < MIN_SCORE:
                # 排名已降序，第一条不达标，后面全不达标 → 直接收工。
                # 返回空列表是**有意为之**：宁可说"没找到依据"，
                # 也不给模型一条分数很低的噪声去当事实用。
                break
            chunk = self.chunks[index]
            results.append({
                "docId": chunk.doc_id,
                "title": chunk.title,
                "section": chunk.section,
                "sourceType": chunk.source_type,
                "score": round(score, 4),
                "snippet": _WHITESPACE.sub(" ", chunk.text)[:200],
            })
        return results


# ══════════════════════════════════════════════════════════════════════
# 两个语料加载器 —— 各自把"原始数据"翻译成 build_chunks 认识的口袋格式
# ══════════════════════════════════════════════════════════════════════

def articles_to_chunks(articles):
    """
    health_article 文章 → 块。

    每篇文章拼成 "标题 + 摘要 + 正文" 一整段再切块 —— 标题和摘要虽然短，
    但信息密度最高（「高血压饮食建议」这种词往往只出现在标题里），
    把它们并进正文能显著提高召回。
    """
    chunks = []
    for article in articles or []:
        article_id = article.get("id")
        title = (article.get("title") or "").strip()
        haystack = "\n".join(
            part for part in (title, article.get("summary"), article.get("content"))
            if part and str(part).strip()
        )
        for piece in split_into_chunks(haystack):
            chunks.append({
                "docId": article_id,
                "title": title,
                "sourceType": SOURCE_ARTICLE,
                "text": piece,
            })
    return chunks


def load_authority_chunks(path=AUTHORITY_FILE):
    """
    读 ingest_authority.py 产出的权威语料 JSON。

    ⚠️ 文件不存在时**不抛异常**，只打印警告并返回空列表。
       理由：检索器挂了会让整个 RAG 链路 500，而"权威语料还没生成"
       只是少一个源，站内文章照样能检索 —— 这属于可降级的失败。

    这里顺手把 ingest 的字段名（docTitle）翻译成 build_chunks 的统一契约（title）。
    翻译**只放在这一个地方** —— 两个源的差异在入口处抹平，进去以后就是一回事。
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        print("⚠️ 权威语料索引不存在: %s" % path)
        print("   先跑一次: algorithm\\.venv\\Scripts\\python.exe ingest_authority.py")
        return []

    chunks = []
    for item in payload.get("chunks") or []:
        chunks.append({
            "docId": item.get("docId"),
            "title": item.get("docTitle") or item.get("title") or "",
            "section": item.get("section") or "",
            "sourceType": item.get("sourceType") or SOURCE_AUTHORITY,
            "text": item.get("text") or "",
        })
    return chunks


def load_articles_from_db():
    """
    从 MySQL 读全部 status=1 的文章。

    连接参数与 real_data_source.py 保持**完全一致**（同一套环境变量名 + 同样的默认值），
    避免同一个项目里出现两份互不相同的数据库配置 —— 那种"两套配置各自为政"的问题
    这个项目已经踩过一次（两张"越界"词表打架）。
    """
    import pymysql
    from pymysql.cursors import DictCursor

    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USERNAME", "root"),
        "password": os.getenv("DB_PASSWORD", "123456"),
        "database": os.getenv("DB_NAME", "health_diet"),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": True,
    }

    connection = pymysql.connect(**config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, summary, content FROM health_article WHERE status = 1"
            )
            return list(cursor.fetchall())
    finally:
        connection.close()


def build_default_retriever(include_articles=True):
    """
    按默认配置装配检索器：权威语料 + （可选）站内文章。

    单点装配 —— 服务端和测试都调这一个函数，免得"服务里装了权威源、
    测试里只装站内文"这种两边不一致。
    """
    chunks = load_authority_chunks()
    authority_count = len(chunks)
    article_count = 0
    if include_articles:
        try:
            article_chunks = articles_to_chunks(load_articles_from_db())
            article_count = len(article_chunks)
            chunks = chunks + article_chunks
        except Exception as exc:      # 数据库不通不影响权威源可用
            print("⚠️ 站内文章读取失败，只用权威语料: %s" % exc)

    retriever = KnowledgeRetriever()
    retriever.build_chunks(chunks)
    retriever.stats = {"authority": authority_count, "article": article_count}
    return retriever


# ══════════════════════════════════════════════════════════════════════
# 直接运行本文件 = 自测：装两个源、建索引、打几个问题看召回
#   algorithm\.venv\Scripts\python.exe kb_retriever.py
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    retriever = build_default_retriever()
    stats = getattr(retriever, "stats", {})
    print("权威语料 %d 块 + 站内文章 %d 块 → 去重丢 %d 块 → 索引 %d 块" % (
        stats.get("authority", 0), stats.get("article", 0),
        getattr(retriever, "duplicates_dropped", 0), len(retriever.chunks),
    ))

    for question in (
        "高血压饮食要注意什么",
        "痛风患者不能吃什么",
        "糖尿病人的主食怎么安排",
        "骨质疏松要补多少钙",
        "生酮饮食是什么",
        "完全无关的问题：怎么修汽车发动机",
    ):
        hits = retriever.search(question, top_k=3)
        print("\n" + "═" * 66)
        print("Q: %s" % question)
        if not hits:
            print("   ⚠️ 无命中（这就是 RAG 最常见的失败形态，调用方必须处理）")
        for rank, hit in enumerate(hits, 1):
            print("   %d. score=%.4f [%s] %s | %s" % (
                rank, hit["score"], hit["sourceType"], hit["title"], hit["section"]
            ))
            print("      %s" % hit["snippet"][:70])
