# -*- coding: utf-8 -*-
"""
营养匹配 GBDT 模型训练脚本 —— 训练 GradientBoostingRegressor 回归器
======================================================================
核心流程：
  1. 构建训练样本（正样本 = 用户真实交互 + 负样本 = 未交互食谱的低分）
  2. 对每个样本提取33维特征向量（涵盖营养素、餐次、目标类型、疾病约束）
  3. 训练 GradientBoostingRegressor 回归器
  4. 保存模型文件（nutrition_model.joblib）和特征定义文件（feature_schema.json）

为什么用 GBDT 而不是深度学习？
  1. 特征维度低（33维），GBDT 在表格数据上效果通常优于神经网络
  2. 样本量小（~14000条），GBDT 通过 boosting 策略能有效利用少量样本
  3. 可解释性强：可以通过特征重要性（feature_importances_）分析哪些
     营养素对推荐影响最大，答辩时能给出有理有据的分析
  4. 对缺失值和异常值天然鲁棒（树模型不需要特征归一化）

正负样本构建策略：
  ┌─ 正样本 ─────────────────────────────────────────────┐
  │ 来源：数据库中用户真实交互过的食谱（收藏+饮食记录）   │
  │ 标签：交互记录的 rating 值（2.5 ~ 5.0）              │
  │ 含义：用户实际吃过的菜，代表"用户可能喜欢"           │
  └──────────────────────────────────────────────────────┘
  ┌─ 负样本 ─────────────────────────────────────────────┐
  │ 来源：用户未交互过的食谱（从未收藏/记录过的菜）       │
  │ 数量：每个用户取正样本数的2倍（最多2倍）              │
  │ 标签：规则护栏分 × 0.5（范围 0.5 ~ 2.5）             │
  │ 含义：随机菜+低分 → 代表"用户大概率不喜欢的菜"        │
  └──────────────────────────────────────────────────────┘

为什么负样本用规则护栏分×0.5而不是0分？
  纯随机菜打0分会让模型认为所有未交互的菜都是"绝对的差"，
  但实际上用户可能只是没发现这道菜。用护栏分×0.5作为软标签，
  既区分了"好菜"和"普通菜"，又不至于把普通菜一棍子打死。

特征定义（33维特征向量）：
  ┌─────────────────────┬──────┬───────────────────────────┐
  │ 分组                │ 维度 │ 说明                       │
  ├─────────────────────┼──────┼───────────────────────────┤
  │ 食谱营养素(8维)     │  0-7 │ 热量/蛋白/碳水/脂肪/      │
  │                     │      │ 纤维/糖/钠/GI值            │
  ├─────────────────────┼──────┼───────────────────────────┤
  │ 餐次目标(4维)       │ 8-11 │ 目标热量/目标蛋白/         │
  │                     │      │ 目标碳水/目标脂肪          │
  ├─────────────────────┼──────┼───────────────────────────┤
  │ 匹配基础分(4维)     │12-15 │ 能量适配/蛋白适配/         │
  │                     │      │ 碳水适配/脂肪适配          │
  ├─────────────────────┼──────┼───────────────────────────┤
  │ 餐次类型(3维)       │16-18 │ 早餐/午餐/晚餐 (One-Hot)  │
  ├─────────────────────┼──────┼───────────────────────────┤
  │ 饮食目标(10维)      │19-28 │ 10种目标类型 (One-Hot)    │
  ├─────────────────────┼──────┼───────────────────────────┤
  │ 慢性病标志(3维)     │29-31 │ 糖尿病/高血脂/高血压       │
  └─────────────────────┴──────┴───────────────────────────┘

设计理念：
  特征覆盖了"食谱特性 + 用户目标 + 餐次差异 + 疾病约束"四个维度，
  GBDT 能自动学习它们之间非线性的交互关系。
  例如：糖尿病患者+高GI食谱 → 这种组合的负分效果不需要人工定义，
  GBDT 从训练样本中自动学到。

命令行用法：
  python train_nutrition_model.py
  python train_nutrition_model.py --output-model ./custom.joblib --output-schema ./custom.json
"""

import argparse
import json
import os
import sys
from collections import defaultdict

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

# ── 路径处理：确保可以从 training/ 子目录导入 algorithm/ 下的模块 ──
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))     # training/ 目录
ALGORITHM_DIR = os.path.dirname(CURRENT_DIR)                 # algorithm/ 目录（上级）
if ALGORITHM_DIR not in sys.path:
    sys.path.insert(0, ALGORITHM_DIR)

from recommend_engine import RecommendEngine
from real_data_source import load_real_interactions, load_real_recipes, load_real_user_profiles


# ═════════════════════════════════════════════════════════════
# 33维特征顺序定义（固定顺序，训练和推理必须一致）
# ═════════════════════════════════════════════════════════════
# 这个顺序定义了 GBDT 模型的输入结构。
# 任何使用该模型的地方（model_runtime.py 中的 _build_feature_vector）
# 都必须按完全相同顺序构建特征向量，否则模型会学到"错位"的特征。
FEATURE_ORDER = [
    # ── 食谱营养素（8维）──
    "calories", "protein", "carbs", "fat", "fiber", "sugar", "sodium", "gi",
    # ── 餐次目标营养素（4维）──
    "meal_target_calories", "target_protein", "target_carbs", "target_fat",
    # ── 规则基础匹配分（4维）──
    # 这4个特征由推荐引擎的规则函数计算，作为"先验知识"输入模型
    "energy_fit", "protein_fit", "carb_fit", "fat_fit",
    # ── 餐次类型 One-Hot（3维）──
    # 同一食谱在早/午/晚餐的营养适配性不同，所以餐具类型很重要
    "is_breakfast", "is_lunch", "is_dinner",
    # ── 饮食目标 One-Hot（10维）──
    # 10种目标类型，互斥，每个用户只属于一种
    "goal_fat_loss", "goal_muscle_toning", "goal_weight_maintenance",
    "goal_healthy_weight_gain", "goal_blood_sugar_control", "goal_lipid_control",
    "goal_low_sodium", "goal_pregnancy_nutrition", "goal_child_growth",
    "goal_senior_wellness",
    # ── 慢性病标志（3维）──
    # 不是互斥的，可能同时患多种慢性病
    "has_diabetes", "has_hyperlipidemia", "has_hypertension"
]


# ═════════════════════════════════════════════════════════════
# 特征工程辅助函数
# ═════════════════════════════════════════════════════════════

def _meal_type_feature(meal_type: str, target: str) -> float:
    """
    餐次类型特征：One-Hot 编码。
    例如：meal_type="breakfast", target="breakfast" → 1.0，否则 → 0.0
    """
    return 1.0 if meal_type == target else 0.0


def _goal_feature(goal_type: str, target: str) -> float:
    """
    饮食目标特征：One-Hot 编码。
    例如：goal_type="fat_loss", target="fat_loss" → 1.0，否则 → 0.0
    """
    return 1.0 if goal_type == target else 0.0


def _profile_to_health_info(profile):
    """
    将数据库读取的用户画像字典转换为引擎需要的健康档案格式。
    数据库字段（snake_case）→ 引擎字段（camelCase）。

    参数 profile：load_real_user_profiles() 返回的画像字典
    返回：适配 RecommendEngine 接口的健康信息字典
    """
    return {
        "age": profile.get("age"),
        "gender": profile.get("gender"),
        "height": profile.get("height"),
        "weight": profile.get("weight"),
        "bmi": profile.get("bmi"),
        "bmr": profile.get("bmr"),
        "activityLevel": profile.get("activityLevel"),
        "chronicDiseases": profile.get("chronicDiseases"),
        "allergies": profile.get("allergies", "")
    }


def _profile_to_diet_goal(profile):
    """
    将数据库画像字典转换为引擎需要的饮食目标格式。

    参数 profile：load_real_user_profiles() 返回的画像字典
    返回：适配 RecommendEngine 接口的饮食目标字典
    """
    return {
        "goalType": profile.get("goalType"),
        "targetCalories": profile.get("targetCalories"),
        "proteinRatio": profile.get("proteinRatio"),
        "carbsRatio": profile.get("carbsRatio"),
        "fatRatio": profile.get("fatRatio"),
        "proteinTarget": profile.get("proteinTarget"),
        "carbsTarget": profile.get("carbsTarget"),
        "fatTarget": profile.get("fatTarget")
    }


def _build_feature_map(engine, recipe, meal_type, meal_target, macro_targets,
                       goal_type, chronic_diseases):
    """
    为一个 <用户, 食谱, 餐次> 组合构建完整的33维特征字典。

    这个函数是连接"训练数据"和"推理数据"的桥梁：
    - 训练时：engine._calculate_health_score 计算标签
    - 推理时：engine._calculate_nutrition_ml_score 调用 GBDT 预测

    参数：
      engine          : RecommendEngine 实例（提供评分函数）
      recipe          : 食谱字典（含营养素字段）
      meal_type       : 餐次类型 "breakfast" / "lunch" / "dinner"
      meal_target     : 该餐次的目标热量
      macro_targets   : 该餐次的宏量营养素目标 {protein, carbs, fat}
      goal_type       : 用户饮食目标类型
      chronic_diseases: 用户慢性病字符串

    返回：33维特征字典 {特征名: 值}
    """
    # ── 提取食谱营养素（8维基础营养）──
    # 使用 .get() 兼容不同字段名（totalCalories vs calories）
    calories = float(recipe.get("totalCalories", recipe.get("calories", 0)) or 0)
    protein = float(recipe.get("protein", 0) or 0)
    carbs = float(recipe.get("carbs", 0) or 0)
    fat = float(recipe.get("fat", 0) or 0)
    fiber = float(recipe.get("fiber", 0) or 0)
    sugar = float(recipe.get("sugar", 0) or 0)
    # 钠值可能以不同字段名出现（sodium / salt / na），做兼容处理
    sodium = float(recipe.get("sodium", recipe.get("salt", recipe.get("na", 0))) or 0)
    gi = float(recipe.get("gi", recipe.get("giValue", 0)) or 0)

    return {
        # ── 食谱营养素（8维）──
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "fiber": fiber,
        "sugar": sugar,
        "sodium": sodium,
        "gi": gi,
        # ── 餐次目标（4维）──
        "meal_target_calories": float(meal_target),
        "target_protein": float(macro_targets.get("protein", 0)),
        "target_carbs": float(macro_targets.get("carbs", 0)),
        "target_fat": float(macro_targets.get("fat", 0)),
        # ── 规则基础分（4维）──
        # 调用引擎的适配评分函数，这些分数是"先验知识"
        "energy_fit": float(engine._energy_fit_score(calories, meal_target)),
        "protein_fit": float(engine._target_fit_score(
            protein, macro_targets.get("protein", 0))),
        "carb_fit": float(engine._target_fit_score(
            carbs, macro_targets.get("carbs", 0))),
        "fat_fit": float(engine._target_fit_score(
            fat, macro_targets.get("fat", 0))),
        # ── 餐次类型 One-Hot（3维）──
        "is_breakfast": _meal_type_feature(meal_type, "breakfast"),
        "is_lunch": _meal_type_feature(meal_type, "lunch"),
        "is_dinner": _meal_type_feature(meal_type, "dinner"),
        # ── 饮食目标 One-Hot（10维）──
        "goal_fat_loss": _goal_feature(goal_type, "fat_loss"),
        "goal_muscle_toning": _goal_feature(goal_type, "muscle_toning"),
        "goal_weight_maintenance": _goal_feature(goal_type, "weight_maintenance"),
        "goal_healthy_weight_gain": _goal_feature(goal_type, "healthy_weight_gain"),
        "goal_blood_sugar_control": _goal_feature(goal_type, "blood_sugar_control"),
        "goal_lipid_control": _goal_feature(goal_type, "lipid_control"),
        "goal_low_sodium": _goal_feature(goal_type, "low_sodium"),
        "goal_pregnancy_nutrition": _goal_feature(goal_type, "pregnancy_nutrition"),
        "goal_child_growth": _goal_feature(goal_type, "child_growth"),
        "goal_senior_wellness": _goal_feature(goal_type, "senior_wellness"),
        # ── 慢性病标志（3维）──
        "has_diabetes": 1.0 if "diabetes" in chronic_diseases else 0.0,
        "has_hyperlipidemia": 1.0 if "hyperlipidemia" in chronic_diseases else 0.0,
        "has_hypertension": 1.0 if "hypertension" in chronic_diseases else 0.0
    }


# ═════════════════════════════════════════════════════════════
# 训练样本构建
# ═════════════════════════════════════════════════════════════

def _build_real_training_samples():
    """
    从数据库构建真实训练样本（首选路径）。

    数据来源：
      - load_real_user_profiles() → 用户画像（目标类型、慢性病）
      - load_real_recipes()       → 食谱数据（营养素值）
      - load_real_interactions()  → 用户-食谱交互（评分标签）

    构建流程：
      ① 按用户分组交互记录，得到每个用户吃过的菜和评分
      ② 遍历每个用户：
          a. 用画像解析目标类型和慢性病
          b. 对每个正样本（用户吃过的菜）：提取33维特征 + 交互评分作为标签
          c. 对负样本（用户没吃过的菜）：提取33维特征 + 护栏分×0.5作为标签
      ③ 检查样本数是否足够（至少10条）

    返回：(特征矩阵, 标签向量, 特征顺序列表, "database")
    """
    # ── 创建引擎实例（用于调用适配评分函数）──
    engine = RecommendEngine()

    # ── 加载三类数据 ──
    profiles = load_real_user_profiles()
    recipes = load_real_recipes()
    interactions = load_real_interactions()

    # 三者缺一不可
    if not profiles or not recipes or not interactions:
        raise ValueError("Insufficient real database data for nutrition model training")

    # ── 按用户组织交互评分 ──
    # ratings_by_user: {user_id: {recipe_id: rating, ...}, ...}
    ratings_by_user = defaultdict(dict)
    for item in interactions:
        user_id = int(item["user_id"])
        recipe_id = int(item["recipe_id"])
        ratings_by_user[user_id][recipe_id] = float(item.get("rating", 0))

    features = []  # 特征矩阵 X
    labels = []    # 标签向量 y

    # ── 遍历每个用户，构建正负样本 ──
    for user_id, profile in profiles.items():
        user_ratings = ratings_by_user.get(int(user_id), {})
        if not user_ratings:
            # 该用户没有任何交互记录，跳过（无法构建正样本）
            continue

        # 解析用户信息
        health_info = _profile_to_health_info(profile)
        diet_goal = _profile_to_diet_goal(profile)
        goal_type = str(profile.get("goalType") or "").strip()
        chronic_diseases = str(profile.get("chronicDiseases") or "").lower()

        # 计算该用户的每日能量目标（用于后续餐次目标分配）
        daily_target = engine._resolve_daily_energy_target(
            health_info, diet_goal, goal_type
        )

        # 记录用户交互过的食谱ID集合（用于排除正样本）
        interacted_recipe_ids = set(user_ratings.keys())

        # ── 正样本：用户真实交互过的食谱 ──
        for recipe_id, rating in user_ratings.items():
            recipe = recipes.get(int(recipe_id))
            if not recipe:
                continue

            # 确定餐次类型（食谱自带或根据名称推断）
            meal_type = recipe.get("mealType") or engine._infer_meal_type(recipe)
            # 计算该餐次的宏量营养素目标
            macro_targets = engine._resolve_macro_targets(
                daily_target, meal_type, diet_goal, goal_type
            )
            meal_target = engine._meal_target(daily_target, meal_type)

            # 构建33维特征
            feature_map = _build_feature_map(
                engine, recipe, meal_type, meal_target, macro_targets,
                goal_type, chronic_diseases
            )
            # 按固定顺序提取特征值
            features.append([feature_map[name] for name in FEATURE_ORDER])
            # 标签：用户真实交互评分，范围限制在 [1.0, 5.0]
            labels.append(float(max(1.0, min(5.0, rating))))

        # ── 负样本：用户未交互过的食谱 ──
        # 从所有食谱中选出用户没吃过的
        negative_candidates = [
            recipe for recipe_id, recipe in sorted(recipes.items())
            if recipe_id not in interacted_recipe_ids
        ][:max(2, len(interacted_recipe_ids))]
        # 负样本数量：至少2条，最多和正样本数一样（避免类别不平衡过严重）

        for recipe in negative_candidates:
            meal_type = recipe.get("mealType") or engine._infer_meal_type(recipe)
            macro_targets = engine._resolve_macro_targets(
                daily_target, meal_type, diet_goal, goal_type
            )
            meal_target = engine._meal_target(daily_target, meal_type)

            # 构建33维特征（和正样本使用相同的特征工程函数）
            feature_map = _build_feature_map(
                engine, recipe, meal_type, meal_target, macro_targets,
                goal_type, chronic_diseases
            )

            # 负样本标签：用规则护栏分 × 0.5
            # 护栏分完全匹配 = 5.0，所以负样本标签范围 [0.5, 2.5]
            health_score = engine._calculate_health_score(
                recipe=recipe,
                meal_type=meal_type,
                meal_target_calories=meal_target,
                macro_targets=macro_targets,
                goal_type=goal_type,
                chronic_diseases=chronic_diseases
            )
            features.append([feature_map[name] for name in FEATURE_ORDER])
            labels.append(float(max(0.5, min(2.5, health_score * 0.5))))

    # 防御：样本数太少无法训练
    if len(features) < 10:
        raise ValueError(
            "Real database samples are too sparse for nutrition model training"
        )

    return np.array(features, dtype=float), np.array(labels, dtype=float), \
        FEATURE_ORDER, "database"


def _build_fallback_training_samples():
    """
    生成合成训练样本（回退路径，数据库不可用时使用）。

    设计思路：
      用10种用户画像 × 12道合成食谱 × 3种餐次类型，
      通过规则引擎计算健康评分作为标签，构建监督学习的训练集。

    合成画像覆盖了全部10种目标类型，以及3种慢性病的组合：
      - fat_loss          → 减脂（无慢病）
      - muscle_toning     → 增肌（无慢病）
      - blood_sugar_control → 血糖控制（+糖尿病）
      - lipid_control     → 血脂控制（+高血脂）
      - low_sodium        → 低钠饮食（+高血压）
      - weight_maintenance → 维持体重（无慢病）
      - healthy_weight_gain → 健康增重（无慢病）
      - pregnancy_nutrition → 孕期营养（无慢病）
      - child_growth      → 儿童发育（无慢病）
      - senior_wellness   → 老年健康（+高血压）

    合成食谱设计：
      12道菜覆盖早/午/晚餐，营养素值呈递进变化，
      确保模型能学到"不同热量/蛋白/碳水/脂肪 对评分的影响"。

    返回：(特征矩阵, 标签向量, 特征顺序列表, "fallback_seed")
    """
    engine = RecommendEngine()

    # ── 10种合成用户画像 ──
    synthetic_profiles = [
        {"goalType": "fat_loss",           "chronicDiseases": "",            "mealType": "breakfast"},
        {"goalType": "muscle_toning",       "chronicDiseases": "",            "mealType": "lunch"},
        {"goalType": "blood_sugar_control", "chronicDiseases": "diabetes",    "mealType": "dinner"},
        {"goalType": "lipid_control",       "chronicDiseases": "hyperlipidemia", "mealType": "lunch"},
        {"goalType": "low_sodium",          "chronicDiseases": "hypertension",  "mealType": "dinner"},
        {"goalType": "weight_maintenance",  "chronicDiseases": "",            "mealType": "lunch"},
        {"goalType": "healthy_weight_gain", "chronicDiseases": "",            "mealType": "dinner"},
        {"goalType": "pregnancy_nutrition", "chronicDiseases": "",            "mealType": "breakfast"},
        {"goalType": "child_growth",        "chronicDiseases": "",            "mealType": "breakfast"},
        {"goalType": "senior_wellness",     "chronicDiseases": "hypertension",  "mealType": "lunch"}
    ]

    # ── 12道合成食谱（营养素值递进变化，模拟多样性）──
    recipes = []
    for recipe_id in range(1, 13):
        recipes.append({
            "id": recipe_id,
            "name": f"recipe_{recipe_id}",
            # 营养素值随ID递增，让12道菜呈现梯度差异
            "totalCalories": 280 + recipe_id * 30,    # 310 ~ 640 千卡
            "protein": 12 + recipe_id * 1.5,           # 13.5 ~ 30 克
            "carbs": 20 + recipe_id * 2.3,             # 22.3 ~ 47.6 克
            "fat": 8 + recipe_id * 0.9,                # 8.9 ~ 18.8 克
            "fiber": 2 + (recipe_id % 5),              # 3 ~ 6 克
            "sugar": max(0.5, 16 - recipe_id),         # 15.5 ~ 4 克（递减）
            "sodium": 220 + recipe_id * 18,            # 238 ~ 436 毫克
            "gi": 42 + recipe_id * 3,                  # 45 ~ 75
            # ID 1-4 早餐，5-8 午餐，9-12 晚餐
            "mealType": "breakfast" if recipe_id <= 4
                        else ("lunch" if recipe_id <= 8 else "dinner"),
            # 每3道有一道标注"轻烹饪"（让模型学到烹饪方式的细微差异）
            "description": "light cooking" if recipe_id % 3 == 0
                           else "regular cooking"
        })

    features = []
    labels = []

    # ── 遍历所有 画像×餐次 组合，每个组合评估所有合成食谱 ──
    for profile in synthetic_profiles:
        goal_type = profile["goalType"]
        meal_type = profile["mealType"]
        chronic_diseases = profile["chronicDiseases"]

        # 使用固定每日目标1900千卡
        daily_target = 1900
        meal_target = engine._meal_target(daily_target, meal_type)
        macro_targets = engine._resolve_macro_targets(
            daily_target, meal_type, {"goalType": goal_type}, goal_type
        )

        for recipe in recipes:
            # 构建33维特征
            feature_map = _build_feature_map(
                engine, recipe, meal_type, meal_target, macro_targets,
                goal_type, chronic_diseases
            )
            # 标签：引擎规则健康评分（范围 1.0 ~ 5.0）
            health_score = engine._calculate_health_score(
                recipe=recipe,
                meal_type=meal_type,
                meal_target_calories=meal_target,
                macro_targets=macro_targets,
                goal_type=goal_type,
                chronic_diseases=chronic_diseases
            )
            features.append([feature_map[name] for name in FEATURE_ORDER])
            labels.append(float(health_score))

    return np.array(features, dtype=float), np.array(labels, dtype=float), \
        FEATURE_ORDER, "fallback_seed"


def build_training_samples():
    """
    训练样本构建的统一入口。
    优先使用数据库真实数据，数据库不可用时回退到合成数据。

    返回：(特征矩阵 X, 标签向量 y, 特征顺序, 数据来源标识)
    """
    try:
        return _build_real_training_samples()
    except Exception:
        # 数据库连接失败 / 数据不足 → 使用合成数据
        return _build_fallback_training_samples()


# ═════════════════════════════════════════════════════════════
# 模型训练与保存
# ═════════════════════════════════════════════════════════════

def train_nutrition_model(output_model_path: str, output_schema_path: str):
    """
    训练 GBDT 营养匹配模型并保存。

    参数：
      output_model_path  : 模型文件输出路径（.joblib）
      output_schema_path : 特征定义文件输出路径（.json）

    训练流程：
      ① 调用 build_training_samples() 获取训练数据
      ② 创建 GradientBoostingRegressor 实例并训练
      ③ 序列化模型到 nutrition_model.joblib
      ④ 保存特征定义到 feature_schema.json

    GBDT 超参数说明（使用 sklearn 默认值）：
      - n_estimators=100     : 100棵决策树，迭代提升100轮
      - learning_rate=0.1    : 每棵树的贡献权重，小值 → 更稳健但需要更多树
      - max_depth=3          : 每棵树最大深度3层（最多捕捉三阶特征交互）
      - random_state=42      : 固定随机种子，保证每次训练结果一致
      - loss='squared_error' : 均方误差损失函数（回归任务标准配置）

    为什么用默认参数而不调参？
      1. 样本量适中（~14000条），默认参数已经足够
      2. 33维特征用 max_depth=3 能学到 1-3 阶的特征交互
      3. 避免过度调参导致过拟合（答辩时也更好解释）
      4. 实际业务中，推荐质量更多取决于特征工程的质量而非GBDT调参
    """
    # ── 步骤①：获取训练数据 ──
    x_train, y_train, feature_order, data_source = build_training_samples()

    # ── 步骤②：创建并训练 GBDT 回归器 ──
    # random_state=42 固定随机种子 → 模型可复现
    model = GradientBoostingRegressor(random_state=42)
    model.fit(x_train, y_train)

    # ── 步骤③：保存模型 ──
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    joblib.dump(model, output_model_path)

    # ── 步骤④：保存特征定义文件 ──
    schema = {
        "feature_order": feature_order,               # 33个特征名（按顺序）
        "defaults": {name: 0.0 for name in feature_order},  # 缺失特征默认填0
        "data_source": data_source,                   # "database" 或 "fallback_seed"
        "sample_count": int(len(x_train))             # 训练样本总数
    }
    with open(output_schema_path, "w", encoding="utf-8") as file:
        json.dump(schema, file, ensure_ascii=False, indent=2)


def main():
    """命令行入口：解析参数 → 调用训练函数"""
    parser = argparse.ArgumentParser(
        description="训练 GBDT 营养匹配模型"
    )
    # 默认输出路径：algorithm/models/
    default_models_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models"
    )
    parser.add_argument(
        "--output-model",
        default=os.path.join(default_models_dir, "nutrition_model.joblib"),
        help="模型输出路径（默认 algorithm/models/nutrition_model.joblib）"
    )
    parser.add_argument(
        "--output-schema",
        default=os.path.join(default_models_dir, "feature_schema.json"),
        help="特征定义文件输出路径（默认 algorithm/models/feature_schema.json）"
    )
    args = parser.parse_args()

    train_nutrition_model(args.output_model, args.output_schema)


if __name__ == "__main__":
    main()
