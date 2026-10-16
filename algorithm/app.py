# -*- coding: utf-8 -*-
"""
Flask API 入口 —— 算法服务的 HTTP 接口层
======================================================================
职责：
  1. 对外暴露 POST /api/recommend/recipes 推荐接口
  2. 管理两个推荐引擎（V1 规则引擎 + V2 混合ML引擎）
  3. 实现自动降级策略：V2 质量不足时自动切换 V1
  4. 对外暴露 POST /api/kb/search 知识库检索接口（RAG 的检索端）

调用链路：
  前端 → Spring Boot 后端 → 此 Flask API → RecommendEngineV2
                                              ↓ 失败时回退
                                          RecommendEngine (V1)
  助手问答 → Spring Boot 后端 → POST /api/kb/search → 双源检索器
                                                     ├─ authority（卫健委食养指南）
                                                     └─ article  （站内 health_article）

环境变量控制：
  RECOMMEND_ENGINE_MODE      : auto / v2 / legacy（引擎选择策略）
  RECOMMEND_V2_MIN_MATCH_SCORE : V2 最低平均匹配分阈值（默认55）
"""

import math
import os
import threading

from flask import Flask, request, jsonify
from flask_cors import CORS

from kb_retriever import (DEFAULT_SOURCE_TYPE, DEFAULT_TOP_K,
                          build_default_retriever)
from recommend_engine import RecommendEngine
from recommend_engine_v2 import RecommendEngineV2

app = Flask(__name__)
CORS(app)  # 允许跨域请求，让 Spring Boot 后端可以调用

# 全局单例：启动时分别创建 V1 和 V2 引擎实例
# V1 = 纯规则引擎（硬编码8个用户种子数据）
# V2 = 混合引擎（SVD协同过滤 + GBDT + 规则护栏，读取数据库真实数据）
legacy_engine = RecommendEngine()
v2_engine = RecommendEngineV2()


# =========================================================================
# 工具函数
# =========================================================================

def _safe_int(value, default_value):
    """安全整数转换：解析失败或负数时返回默认值"""
    try:
        parsed = int(value)
        return parsed if parsed >= 0 else default_value
    except (TypeError, ValueError):
        return default_value


def _safe_float(value, default_value):
    """安全浮点转换：解析失败时返回默认值"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default_value


def _normalize_mode(raw_mode):
    """规范化引擎模式参数：只接受 auto / v2 / legacy，其余一律视为 auto"""
    mode = str(raw_mode or "auto").strip().lower()
    if mode in {"legacy", "v2", "auto"}:
        return mode
    return "auto"


def _is_valid_structure(payload):
    """
    检查 V2 返回结果的结构是否合法。
    合法的推荐结果必须是一个字典，包含 breakfast / lunch / dinner 三个列表。
    """
    if not isinstance(payload, dict):
        return False
    for meal_type in ("breakfast", "lunch", "dinner"):
        if not isinstance(payload.get(meal_type), list):
            return False
    return True


def _coverage_is_ok(payload, requested_counts):
    """
    检查 V2 返回的覆盖率是否足够。
    每餐返回数至少要达到请求数的 60%（最少1道）。
    例如请求午餐3道，V2只返回了1道 → 覆盖率不足 → 退化到 V1。
    设计原因：有数据可用比无数据返回更重要。
    """
    for meal_type, requested in requested_counts.items():
        if requested <= 0:
            continue
        returned = len(payload.get(meal_type, []))
        # 60% 最低覆盖率阈值
        min_expected = max(1, int(math.ceil(requested * 0.6)))
        if returned < min_expected:
            return False
    return True


def _quality_is_ok(payload, min_match_score):
    """
    检查 V2 返回结果的平均匹配分是否达标。
    遍历三餐所有推荐食谱，计算 matchScore 平均值。
    如果平均值低于阈值（默认55分），说明推荐质量不足，退化到 V1。
    设计原因：宁可退回稳定的规则引擎，也不给用户展示低质量推荐。
    """
    scores = []
    for meal_type in ("breakfast", "lunch", "dinner"):
        for recipe in payload.get(meal_type, []):
            if not isinstance(recipe, dict):
                continue
            score = _safe_float(recipe.get("matchScore"), 0.0)
            if score > 0:
                scores.append(score)

    if not scores:
        return False

    average_score = sum(scores) / len(scores)
    return average_score >= min_match_score


def _run_engine(engine, user_id, requested_counts, health_info, diet_goal, candidate_recipes):
    """
    通用的引擎调用封装。
    所有引擎实例都遵循相同的 get_recommended_recipes 接口签名。
    """
    return engine.get_recommended_recipes(
        user_id,
        requested_counts["breakfast"],
        requested_counts["lunch"],
        requested_counts["dinner"],
        health_info,
        diet_goal,
        candidate_recipes
    )


# =========================================================================
# API 路由 —— 唯一的对外接口
# =========================================================================

@app.route('/api/recommend/recipes', methods=['POST'])
def recommend_recipes():
    """
    食谱推荐接口（POST）。
    被 Spring Boot 后端通过 HTTP 调用。

    请求 JSON 参数：
      - userId            : 用户ID（可选，用于协同过滤）
      - breakfastCount    : 早餐需要的推荐数（默认3）
      - lunchCount        : 午餐需要的推荐数（默认3）
      - dinnerCount       : 晚餐需要的推荐数（默认3）
      - healthInfo        : 用户健康档案（年龄/BMI/活动量/慢性病/过敏等）
      - dietGoal          : 饮食目标（目标类型/目标热量/宏量营养素配比等）
      - candidateRecipes  : 待筛选的候选食谱列表（前端传来的原始食谱数据）

    响应格式：
      { code: 200, message: "success", data: { breakfast: [...], lunch: [...], dinner: [...] } }

    引擎选择逻辑（auto 模式）：
      1. 先跑 V2 混合引擎（SVD + GBDT + 规则护栏）
      2. 检查 V2 结果质量：结构合法 → 覆盖率 ≥ 60% → 平均匹配分 ≥ 阈值
      3. 任何一项不达标 → 自动退化到 V1 纯规则引擎
      4. V2 抛出异常 → 也退化到 V1
    """
    try:
        # ---- 解析请求参数 ----
        data = request.json or {}
        requested_counts = {
            "breakfast": _safe_int(data.get('breakfastCount', 3), 3),
            "lunch": _safe_int(data.get('lunchCount', 3), 3),
            "dinner": _safe_int(data.get('dinnerCount', 3), 3)
        }

        health_info = data.get('healthInfo', {}) or {}
        diet_goal = data.get('dietGoal', {}) or {}
        candidate_recipes = data.get('candidateRecipes', []) or []
        user_id = data.get('userId')

        # ---- 读取运行配置 ----
        engine_mode = _normalize_mode(os.getenv('RECOMMEND_ENGINE_MODE', 'auto'))
        min_match_score = _safe_float(os.getenv('RECOMMEND_V2_MIN_MATCH_SCORE', '55'), 55.0)

        # ---- 根据模式选择引擎 ----
        if engine_mode == 'legacy':
            # 强制使用 V1（用于调试或生产回退）
            recommended_recipes = _run_engine(
                legacy_engine, user_id, requested_counts,
                health_info, diet_goal, candidate_recipes
            )
        elif engine_mode == 'v2':
            # 强制使用 V2（用于测试 ML 效果）
            recommended_recipes = _run_engine(
                v2_engine, user_id, requested_counts,
                health_info, diet_goal, candidate_recipes
            )
        else:
            # auto 模式：V2 优先 + 自动退化
            fallback_to_legacy = False
            try:
                v2_result = _run_engine(
                    v2_engine, user_id, requested_counts,
                    health_info, diet_goal, candidate_recipes
                )

                # 三层校验：结构 → 覆盖率 → 质量
                if not _is_valid_structure(v2_result):
                    fallback_to_legacy = True
                elif not _coverage_is_ok(v2_result, requested_counts):
                    fallback_to_legacy = True
                elif not _quality_is_ok(v2_result, min_match_score):
                    fallback_to_legacy = True
            except Exception:
                # V2 异常也不影响用户使用
                fallback_to_legacy = True
                v2_result = None

            if fallback_to_legacy:
                # 退化：用 V1 引擎重新推荐
                recommended_recipes = _run_engine(
                    legacy_engine, user_id, requested_counts,
                    health_info, diet_goal, candidate_recipes
                )
            else:
                recommended_recipes = v2_result

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': recommended_recipes
        })
    except Exception as error:
        # 最外层兜底：即使 V1 也崩了，也返回可读的错误信息
        return jsonify({
            'code': 500,
            'message': str(error),
            'data': None
        })


# =========================================================================
# 知识库检索接口 —— RAG 的「检索段」
#
# 和数据源的分工：
#   ingredient 表  → 精确数值（"米饭多少卡"）→ 走 Java 侧的精确查表，不进这里
#   权威指南(8篇)  → 概念/建议/注意事项 → 走这里，sourceType="authority"
#   health_article → 站内科普文          → 走这里，sourceType="article"
#                    （⚠️ 其中 120 篇是同一套模板生成的，质量参差）
# 也就是说：**有唯一正确答案的东西不查这里，没有唯一答案的才查这里。**
#
# 语料重建：改了 权威文件/ 里的 PDF，或新抓了文章，都要重跑
#   algorithm\.venv\Scripts\python.exe ingest_authority.py
# 然后重启本服务（索引是进程内存里懒加载的，不会自动感知文件变化）。
# =========================================================================

_kb_retriever = None
_kb_retriever_lock = threading.Lock()


def _get_kb_retriever():
    """
    懒加载知识库索引（第一次真有人调检索时才构建，之后复用）。

    为什么不放在模块顶层构建：
      Flask 开发服务器开着 debug=True，改一行代码就重启进程。
      放顶层 → 每改一次代码都要重读全库、重建索引，调试体验很差。
    为什么要加锁：
      开发服务器是多线程的，两个请求同时到达可能同时触发构建。
      双重检查 + 锁，保证只建一次。
    """
    global _kb_retriever
    if _kb_retriever is None:
        with _kb_retriever_lock:
            if _kb_retriever is None:
                retriever = build_default_retriever()
                stats = getattr(retriever, "stats", {})
                app.logger.info(
                    "知识库索引构建完成：权威语料 %d 块 + 站内文章 %d 块 → 索引 %d 块（去重丢 %d）",
                    stats.get("authority", 0), stats.get("article", 0),
                    len(retriever.chunks), getattr(retriever, "duplicates_dropped", 0),
                )
                _kb_retriever = retriever
    return _kb_retriever


@app.route('/api/kb/search', methods=['POST'])
def kb_search():
    """
    知识库检索接口（POST）。被 Spring Boot 后端调用，也可被测试脚本直接调用
    （直连时不经 Java、不需要登录 token，这是把它放在算法端的主要理由之一）。

    请求 JSON：
      - query      : 用户问题（必填）
      - topK       : 返回几条，默认 3
      - sourceType : 检索范围。不传 = authority（默认只查权威源）
                     authority / article / all（两个源都查）
                     ⭐ 有了它才能回答"权威源单独召回了什么"——
                       这也是分别测两个源召回率的前提。

    响应：
      { "code": 200, "message": "success",
        "data": [ {"docId":.., "title":.., "section":.., "sourceType":..,
                   "score":.., "snippet":..}, ... ] }

    📌 每个结果都带 docId + sourceType —— 这是"召回率能不能测"的前提：
       没有 docId 就无法断言"问 X 应该命中文档 Y"；
       没有 sourceType 就无法断言"这条答案该不该标权威来源"。
       这两个字段是**为测试而加**的，不是可选项。

    ⚠️ 出错不抛 500 给调用方，而是返回 code + 可读 message + 空 data：
       RAG 最常见的失败形态就是"检索返回空、然后静默退化成裸模型回答、
       谁也不知道"。调用方必须能区分"检索成功但没命中"和"检索服务挂了"。
    """
    try:
        data = request.json or {}
        query = str(data.get('query') or '').strip()
        top_k = _safe_int(data.get('topK', DEFAULT_TOP_K), DEFAULT_TOP_K)
        # 不传就是默认范围（权威源）；显式传 all 才两源都查
        source_type = data.get('sourceType') or DEFAULT_SOURCE_TYPE
        if source_type not in ('authority', 'article', 'all'):
            return jsonify({'code': 400,
                            'message': "sourceType 只能是 authority / article / all",
                            'data': []})

        if not query:
            return jsonify({'code': 400, 'message': 'query 不能为空', 'data': []})

        hits = _get_kb_retriever().search(query, top_k=top_k, source_type=source_type)
        return jsonify({'code': 200, 'message': 'success', 'data': hits})

    except Exception as error:
        # 检索失败不能拖垮整个服务：记日志 + 返回可读错误，data 留空
        app.logger.exception("知识库检索失败：%s", error)
        return jsonify({'code': 500, 'message': str(error), 'data': []})


@app.route('/api/kb/reload', methods=['POST'])
def kb_reload():
    """
    重建索引。改了语料（重跑 ingest_authority.py）或调了切块参数之后调它，
    **不用重启服务**。

    为什么值得单独开一个口子：
      索引是**进程内存里懒加载**的，文件变了它不会自己知道。
      没有这个接口，每次改语料都得"杀进程 → 重启 → 等启动"，
      做召回实验时这一步会烦到让人不想改参数 —— 而"不想改参数"
      恰恰是评测做不下去的头号原因。

    先清空再重建（而不是原地替换）：清空要拿锁，构建也要拿锁，
    分两步是为了避开同一把非重入锁的死锁。
    """
    global _kb_retriever
    with _kb_retriever_lock:
        _kb_retriever = None
    retriever = _get_kb_retriever()
    return jsonify({
        'code': 200,
        'message': '索引已重建',
        'data': {
            'totalChunks': len(retriever.chunks),
            'duplicatesDropped': getattr(retriever, 'duplicates_dropped', 0),
        },
    })


@app.route('/api/kb/stats', methods=['GET'])
def kb_stats():
    """
    看一眼索引构成。演示和排查时用：能立刻回答"到底装进去了什么、有多少"。
    """
    retriever = _get_kb_retriever()
    stats = getattr(retriever, "stats", {})
    authority_chunks = sum(1 for c in retriever.chunks if c.source_type == 'authority')
    article_chunks = sum(1 for c in retriever.chunks if c.source_type == 'article')
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'totalChunks': len(retriever.chunks),
            'authorityChunks': authority_chunks,
            'articleChunks': article_chunks,
            'duplicatesDropped': getattr(retriever, 'duplicates_dropped', 0),
            'sources': stats,
        },
    })


if __name__ == '__main__':
    # Flask 开发服务器，监听所有网卡 5000 端口
    # 生产环境应使用 gunicorn 或 waitress
    app.run(host='0.0.0.0', port=5000, debug=True)
