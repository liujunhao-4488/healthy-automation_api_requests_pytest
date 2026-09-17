# -*- coding: utf-8 -*-
"""
真实数据源 —— 从 MySQL 数据库读取用户、食谱和交互数据
======================================================================
职责：
  1. 连接 MySQL 数据库（配置通过环境变量读取）
  2. 加载用户完整画像（多表 JOIN：user + health_info + user_diet_preference + diet_goal）
  3. 加载食谱数据（recipe + ingredient + recipe_ingredient 汇总计算 GI/糖/钠）
  4. 加载用户-食谱交互记录（收藏 + 饮食记录）并转换为显式评分

环境变量（有默认值，不设置也能跑）：
  DB_HOST     : 数据库地址，默认 localhost
  DB_PORT     : 端口，默认 3306
  DB_USERNAME : 用户名，默认 root
  DB_PASSWORD : 密码，默认 123456
  DB_NAME     : 数据库名，默认 health_diet

关键转换公式（隐式反馈 → 显式评分）：
  rating = min(5.0, 2.5 + 饮食记录次数 × 0.4 + 收藏次数 × 0.7)

设计原则：
  - 所有数值字段都经过 _safe_float/_safe_int 防御脏数据
  - 数据库连接使用 autocommit 模式，读取完即释放
  - PyMySQL 导入失败不阻塞模块加载（允许在没有数据库依赖的环境中 import）
"""

import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:  # pragma: no cover - optional dependency at runtime
    pymysql = None
    DictCursor = None


# =========================================================================
# 安全类型转换（防御数据库脏数据）
# =========================================================================

def _safe_float(value: Any, default: float = 0.0) -> float:
    """尝试将值转为 float，失败或为 None 时返回默认值"""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    """尝试将值转为 int，失败或为 None 时返回默认值"""
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


# =========================================================================
# 数据库连接
# =========================================================================

def _db_config() -> Dict[str, Any]:
    """
    构建数据库连接配置。
    所有参数均可通过环境变量覆盖，未设置时使用默认值。
    DictCursor 让查询结果以字典格式返回（字段名→值），方便后续处理。
    autocommit=True 因为只做读取操作，不需要事务管理。
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": _safe_int(os.getenv("DB_PORT", 3306), 3306),
        "user": os.getenv("DB_USERNAME", "root"),
        "password": os.getenv("DB_PASSWORD", "123456"),
        "database": os.getenv("DB_NAME", "health_diet"),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": True
    }


def _connect():
    """创建数据库连接。PyMySQL 未安装时抛出明确错误。"""
    if pymysql is None:
        raise RuntimeError("PyMySQL is required for real database training")
    return pymysql.connect(**_db_config())


def _fetch_all(sql: str) -> List[Dict[str, Any]]:
    """
    执行 SQL 查询并返回所有结果行。
    使用 context manager（with 语法），自动关闭连接和游标。
    """
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return list(cursor.fetchall() or [])


# =========================================================================
# 用户画像加载（4张表联合构建）
# =========================================================================

def load_real_user_profiles() -> Dict[int, Dict[str, Any]]:
    """
    从数据库加载所有活跃用户的完整画像。

    查询4张表：
      user                  → 用户ID + 状态（只取 status=1 的活跃用户）
      health_info           → 年龄/性别/身高/体重/BMI/BMR/活动量/慢性病
      user_diet_preference  → 过敏/忌口/偏好
      diet_goal             → 目标类型/热量目标/宏量配比（取每个用户最新一条）

    返回格式：
      { user_id: { "goalType": "...", "age": 25, "bmi": 22.0, ... } }

    每个用户画像有17个字段（见下方 profiles 字典的初始化）。
    未填写的字段会被后续表的真实数据覆盖，覆盖不到的保留默认值。
    """
    # ── 1. 读取用户表：只取活跃用户（status != 0）──
    user_rows = _fetch_all(
        """
        SELECT id, COALESCE(status, 1) AS status
        FROM user
        """
    )

    # ── 2. 读取健康档案表 ──
    health_rows = _fetch_all(
        """
        SELECT
            user_id,
            age,
            gender,
            height,
            weight,
            bmi,
            bmr,
            activity_level,
            chronic_diseases
        FROM health_info
        """
    )

    # ── 3. 读取饮食偏好表 ──
    preference_rows = _fetch_all(
        """
        SELECT
            user_id,
            allergies,
            dislikes,
            favorites
        FROM user_diet_preference
        """
    )

    # ── 4. 读取饮食目标表：按 user_id 分组，每组取最新一条 ──
    goal_rows = _fetch_all(
        """
        SELECT
            user_id,
            goal_type,
            target_calories,
            protein_ratio,
            carbs_ratio,
            fat_ratio,
            protein_target,
            carbs_target,
            fat_target,
            update_time
        FROM diet_goal
        ORDER BY user_id, update_time DESC, id DESC
        """
    )

    # ── 5. 组装用户画像 ──

    # 先为每个活跃用户创建默认画像（全是默认值）
    profiles: Dict[int, Dict[str, Any]] = {}
    for row in user_rows:
        user_id = _safe_int(row.get("id"))
        if user_id <= 0 or _safe_int(row.get("status"), 1) == 0:
            # 跳过无效ID和已禁用用户
            continue
        profiles[user_id] = {
            "goalType": "",
            "activityLevel": "",
            "age": 30,
            "gender": "",
            "height": 0.0,
            "weight": 0.0,
            "bmi": 22.0,
            "bmr": 0.0,
            "chronicDiseases": "",
            "allergies": "",
            "dislikes": "",
            "favorites": "",
            "targetCalories": 0.0,
            "proteinRatio": 0.0,
            "carbsRatio": 0.0,
            "fatRatio": 0.0,
            "proteinTarget": 0.0,
            "carbsTarget": 0.0,
            "fatTarget": 0.0
        }

    # 用健康档案数据覆盖默认值
    for row in health_rows:
        user_id = _safe_int(row.get("user_id"))
        if user_id not in profiles:
            continue  # 健康档案中有但 user 表没匹配到，跳过
        profiles[user_id].update({
            "age": _safe_int(row.get("age"), 30),
            "gender": row.get("gender") or "",
            "height": _safe_float(row.get("height")),
            "weight": _safe_float(row.get("weight")),
            "bmi": _safe_float(row.get("bmi"), 22.0) or 22.0,
            "bmr": _safe_float(row.get("bmr")),
            "activityLevel": row.get("activity_level") or "",
            "chronicDiseases": row.get("chronic_diseases") or ""
        })

    # 用饮食偏好数据覆盖
    for row in preference_rows:
        user_id = _safe_int(row.get("user_id"))
        if user_id not in profiles:
            continue
        profiles[user_id].update({
            "allergies": row.get("allergies") or "",
            "dislikes": row.get("dislikes") or "",
            "favorites": row.get("favorites") or ""
        })

    # 取每个用户的最新一条饮食目标
    # goal_rows 已按 user_id, update_time DESC, id DESC 排序
    # 所以每个用户遇到的第一行就是最新的
    latest_goal_by_user: Dict[int, Dict[str, Any]] = {}
    for row in goal_rows:
        user_id = _safe_int(row.get("user_id"))
        if user_id <= 0 or user_id in latest_goal_by_user:
            # 已经在字典中 → 跳过（保留最先读到的即最新的一条）
            continue
        latest_goal_by_user[user_id] = row

    # 用饮食目标数据覆盖
    for user_id, row in latest_goal_by_user.items():
        if user_id not in profiles:
            continue
        profiles[user_id].update({
            "goalType": row.get("goal_type") or "",
            "targetCalories": _safe_float(row.get("target_calories")),
            "proteinRatio": _safe_float(row.get("protein_ratio")),
            "carbsRatio": _safe_float(row.get("carbs_ratio")),
            "fatRatio": _safe_float(row.get("fat_ratio")),
            "proteinTarget": _safe_float(row.get("protein_target")),
            "carbsTarget": _safe_float(row.get("carbs_target")),
            "fatTarget": _safe_float(row.get("fat_target"))
        })

    return profiles


# =========================================================================
# 食谱数据加载（多表汇总计算）
# =========================================================================

def load_real_recipes() -> Dict[int, Dict[str, Any]]:
    """
    从数据库加载所有已发布食谱及其营养数据。

    查询2个来源：
      recipe 表            → 食谱基本信息和静态营养字段
      recipe_ingredient + ingredient 表 → 通过食材汇总计算GI/糖/钠

    为什么GI/糖/钠要从食材汇总计算？
      食谱表中的 GI 值是固定字段，但前端传入的候选食谱可能没有这些字段。
      而从食材汇总计算能保证数据完整性——只要食材表有营养数据，
      就能算出每个食谱的GI/糖/钠。

    GI 值计算：Σ(食材GI × 食材碳水含量 × 用量) / Σ(食材碳水含量 × 用量)
    这是加权平均，以碳水量为权重，因为GI只对碳水化合物有意义。
    """
    # ── 1. 读取已发布食谱 ──
    recipe_rows = _fetch_all(
        """
        SELECT
            id,
            name,
            description,
            category,
            cooking_time,
            difficulty,
            servings,
            total_calories,
            protein,
            carbs,
            fat,
            fiber,
            collect_count,
            view_count,
            goal_type,
            status
        FROM recipe
        WHERE COALESCE(status, 1) = 1
        """
    )

    # ── 2. 从食材表汇总计算额外的营养指标 ──
    nutrition_rows = _fetch_all(
        """
        SELECT
            ri.recipe_id,
            -- 糖 = Σ(食材含糖量 × 用量 / 100)
            SUM(COALESCE(i.sugar_per_100g, 0) * COALESCE(ri.quantity, 0) / 100) AS sugar,
            -- 钠 = Σ(食材含钠量 × 用量 / 100)
            SUM(COALESCE(i.sodium_per_100g, 0) * COALESCE(ri.quantity, 0) / 100) AS sodium,
            -- GI值分子 = Σ(食材GI × 食材碳水 × 用量 / 100)
            SUM(COALESCE(i.gi_value, 0) * COALESCE(i.carbs_per_100g, 0) * COALESCE(ri.quantity, 0) / 100) AS weighted_gi,
            -- GI值分母 = Σ(食材碳水 × 用量 / 100)
            SUM(COALESCE(i.carbs_per_100g, 0) * COALESCE(ri.quantity, 0) / 100) AS gi_carb_weight
        FROM recipe_ingredient ri
        INNER JOIN ingredient i ON i.id = ri.ingredient_id
        GROUP BY ri.recipe_id
        """
    )

    # 构建 recipe_id → 汇总营养 的快速查找表
    nutrition_by_recipe = {
        _safe_int(row.get("recipe_id")): row
        for row in nutrition_rows
        if _safe_int(row.get("recipe_id")) > 0
    }

    # ── 3. 组装食谱数据 ──
    recipes: Dict[int, Dict[str, Any]] = {}
    for row in recipe_rows:
        recipe_id = _safe_int(row.get("id"))
        if recipe_id <= 0:
            continue

        # 取出该食谱的汇总营养数据（可能为空）
        nutrition = nutrition_by_recipe.get(recipe_id, {})
        gi_weight = _safe_float(nutrition.get("gi_carb_weight"))
        weighted_gi = _safe_float(nutrition.get("weighted_gi"))

        # 构建标准化的食谱字典
        recipes[recipe_id] = {
            "id": recipe_id,
            "name": row.get("name") or "",
            "description": row.get("description") or "",
            "category": row.get("category") or "",
            "cookingTime": _safe_int(row.get("cooking_time")),
            "difficulty": row.get("difficulty") or "",
            "servings": _safe_float(row.get("servings"), 1.0) or 1.0,
            "totalCalories": _safe_float(row.get("total_calories")),
            "protein": _safe_float(row.get("protein")),
            "carbs": _safe_float(row.get("carbs")),
            "fat": _safe_float(row.get("fat")),
            "fiber": _safe_float(row.get("fiber")),
            "sugar": _safe_float(nutrition.get("sugar")),
            "sodium": _safe_float(nutrition.get("sodium")),
            # GI = 加权GI和 / 碳水权重和（加权平均，避免无碳水的食材影响结果）
            "gi": weighted_gi / gi_weight if gi_weight > 0 else 0.0,
            "collectCount": _safe_int(row.get("collect_count")),
            "viewCount": _safe_int(row.get("view_count")),
            "goalType": row.get("goal_type") or ""
        }
    return recipes


# =========================================================================
# 用户-食谱交互数据加载（隐式反馈 → 显式评分）
# =========================================================================

def load_real_interactions() -> List[Dict[str, Any]]:
    """
    从数据库读取用户与食谱的交互记录，并将隐式行为转换为显式评分。

    两个数据源：
      1. user_recipe_collect  → 收藏行为（强信号：用户主动收藏 = 喜欢）
      2. diet_record_detail   → 饮食记录行为（中等信号：记录不代表喜欢，
                                 但多次记录同一道菜说明接受度高）

    合并策略：
      按 (user_id, recipe_id) 合并两个来源的计数。
      同一对可能有多个收藏记录（多次收藏同一道菜）和多个饮食记录。

    评分公式：
      rating = min(5.0, 2.5 + 饮食记录次数 × 0.4 + 收藏次数 × 0.7)

    系数设计原理：
      - 收藏权重(0.7) > 记录权重(0.4)：收藏是更强的喜好信号
      - 基础分 2.5：没有任何交互时默认为中性，但需要用户至少有一次交互才会被记录
      - 分数区间 2.5~5.0：隐式反馈无法表达"不喜欢"，所以没有低分

    返回格式：
      [{"user_id": 1, "recipe_id": 3, "rating": 4.1, "collect_count": 1, "record_count": 2}, ...]
      按 (user_id, recipe_id) 排序。
    """
    # ── 1. 读取收藏记录 ──
    collect_rows = _fetch_all(
        """
        SELECT
            user_id,
            recipe_id
        FROM user_recipe_collect
        """
    )

    # ── 2. 读取饮食记录详情（聚合每个用户对每道菜的记录次数）──
    record_rows = _fetch_all(
        """
        SELECT
            dr.user_id,
            drd.recipe_id,
            COUNT(*) AS record_count
        FROM diet_record_detail drd
        INNER JOIN diet_record dr ON dr.id = drd.record_id
        WHERE drd.recipe_id IS NOT NULL
          AND COALESCE(drd.is_deleted, 0) = 0    -- 排除已删除的记录详情
          AND COALESCE(dr.is_deleted, 0) = 0     -- 排除已删除的饮食记录
        GROUP BY dr.user_id, drd.recipe_id
        """
    )

    # ── 3. 合并两个来源 ──

    # 使用 defaultdict：不存在时自动创建 {"collect_count": 0, "record_count": 0}
    interaction_map: Dict[Tuple[int, int], Dict[str, float]] = defaultdict(lambda: {
        "collect_count": 0.0,
        "record_count": 0.0
    })

    # 累加收藏计数
    for row in collect_rows:
        key = (_safe_int(row.get("user_id")), _safe_int(row.get("recipe_id")))
        if key[0] <= 0 or key[1] <= 0:
            continue
        interaction_map[key]["collect_count"] += 1.0

    # 累加饮食记录计数
    for row in record_rows:
        key = (_safe_int(row.get("user_id")), _safe_int(row.get("recipe_id")))
        if key[0] <= 0 or key[1] <= 0:
            continue
        interaction_map[key]["record_count"] += _safe_float(row.get("record_count"), 0.0)

    # ── 4. 将合并后的计数转换为显式评分 ──
    interactions: List[Dict[str, Any]] = []
    for (user_id, recipe_id), payload in interaction_map.items():
        collect_count = payload["collect_count"]
        record_count = payload["record_count"]
        # ★核心公式★：隐式反馈 → 显式评分
        rating = min(5.0, 2.5 + record_count * 0.4 + collect_count * 0.7)
        interactions.append({
            "user_id": user_id,
            "recipe_id": recipe_id,
            "rating": round(rating, 2),            # 保留两位小数
            "collect_count": int(collect_count),
            "record_count": int(record_count)
        })

    # 排序：保证每次加载结果顺序一致（对 SVD 训练无影响，但方便调试对比）
    interactions.sort(key=lambda item: (item["user_id"], item["recipe_id"]))
    return interactions
