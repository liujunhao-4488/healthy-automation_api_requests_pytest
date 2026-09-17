# -*- coding: utf-8 -*-
"""
V2 混合推荐引擎 —— 系统核心创新点 #1
======================================================================
职责：
  1. 继承 V1 引擎的所有基础方法（规则护栏/份量调整/能量目标解析等）
  2. 用真实数据库数据替换 V1 的硬编码种子数据
  3. 引入 ML 模型推理：SVD协同过滤 + GBDT营养匹配
  4. 实现三组件加权融合：CF × 0.45 + NutritionML × 0.35 + Guard × 0.20

与 V1 的关键差异：
  ┌──────────────┬─────────────────────┬──────────────────────┐
  │ 维度          │ V1                  │ V2                   │
  ├──────────────┼─────────────────────┼──────────────────────┤
  │ 数据源        │ 8个硬编码用户        │ MySQL 181用户+184食谱 │
  │ 协同过滤      │ 相似用户加权平均      │ SVD嵌入余弦相似度     │
  │              │                     │ → 失败回退V1方式      │
  │ 营养评分      │ 仅规则引擎            │ GBDT模型预测         │
  │              │                     │ → 失败回退规则护栏     │
  │ 融合公式      │ CF×0.55 + Guard×0.45│ CF×0.45 + ML×0.35    │
  │              │                     │ + Guard×0.20         │
  │ 餐次策略      │ 每个食谱只归入一餐     │ 每道菜参与三餐竞争     │
  │              │                     │ 全局去重              │
  │ 份量调节范围  │ 0.6 ~ 1.5           │ 0.5 ~ 2.2            │
  └──────────────┴─────────────────────┴──────────────────────┘

核心流程（get_recommended_recipes）：
  对早/午/晚三餐分别：
    对每道候选食谱：
      ① 过敏硬拦截 → 跳过
      ② 已推荐去重 → 跳过
      ③ _calculate_model_cf_score() → CF分 [1,5]，内部有模型→回退二级降级
      ④ _calculate_health_score()    → 规则护栏分 [0,5]
      ⑤ _build_nutrition_feature_map() → 33维特征 → _calculate_nutrition_ml_score() → ML分 [0,5]
      ⑥ final_score = CF×0.45 + ML×0.35 + Guard×0.20
      ⑦ matchScore = round(final_score × 20)  → 百分制 [0,100]
      ⑧ _personalize_serving() → 份量个性化调整
      ⑨ _build_reason() + _build_tags() → 推荐理由 + 标签
    按 (matchScore, ML分, CF分, 热量偏差) 降序排列
    取 Top-N，标记已推荐
"""

from typing import Any, Dict

from model_runtime import ModelRuntime
from recommend_engine import RecommendEngine
from real_data_source import load_real_interactions, load_real_user_profiles


class RecommendEngineV2(RecommendEngine):
    """
    V2 混合推荐引擎。
    继承 RecommendEngine（V1）的所有基础方法，
    覆写推荐主流程和 CF/Nutrition 评分方法，引入 ML 推理。
    """

    def __init__(self):
        # 调用父类初始化 → 加载 V1 的硬编码种子数据
        super().__init__()
        # 尝试用数据库真实数据替换种子数据
        try:
            real_profiles = load_real_user_profiles()
            real_interactions = load_real_interactions()
            if real_profiles:
                self.user_profiles = real_profiles    # 替代 V1 的8个硬编码用户
            if real_interactions:
                self.user_recipe_data = real_interactions  # 替代 V1 的24条硬编码交互
        except Exception:
            # 数据库不可用时保留 V1 的种子数据，保证系统仍能运行
            pass
        # 创建 ML 模型运行时（加载 SVD嵌入 + GBDT + 特征定义）
        self.model_runtime = ModelRuntime()

    # =========================================================================
    # 推荐主流程（覆写 V1 方法）
    # =========================================================================

    def get_recommended_recipes(
        self,
        user_id,
        breakfast_count=3,
        lunch_count=3,
        dinner_count=3,
        health_info=None,
        diet_goal=None,
        candidate_recipes=None
    ):
        """
        三组件融合推荐的主流程。

        步骤概览：
          1. 构建用户画像 + 找相似用户
          2. 解析每日能量目标和宏量目标
          3. 对每道候选食谱，计算三个分量得分并加权融合
          4. 对每餐排序取 Top-N
          5. 全局去重（同一食谱不能出现在两餐中）

        与 V1 的两个关键区别：
          - 不再用 _infer_meal_type 限制食谱的餐次归属，每个食谱参与三餐竞争
          - 融合公式从二组件变为三组件
        """
        candidate_recipes = candidate_recipes or []
        grouped = {"breakfast": [], "lunch": [], "dinner": []}
        if not candidate_recipes:
            return grouped

        health_info = health_info or {}
        diet_goal = diet_goal or {}

        # ── 基础画像与目标解析（使用 V1 的方法）──
        user_profile = self._build_user_profile(health_info, diet_goal)
        similar_users = self._find_similar_users(user_profile)  # 16维向量余弦匹配，取前4
        goal_type = self._normalize_text(diet_goal.get("goalType", ""))
        daily_target_calories = self._resolve_daily_energy_target(
            health_info, diet_goal, goal_type
        )

        allergies = self._split_tokens(health_info.get("allergies", ""))
        dislikes = self._split_tokens(health_info.get("dislikes", ""))
        chronic_diseases = self._normalize_text(health_info.get("chronicDiseases", ""))

        # 全局去重集合：同一食谱不会出现在两餐推荐中
        used_recipe_ids = set()

        for meal_type, limit in (
            ("breakfast", breakfast_count),
            ("lunch", lunch_count),
            ("dinner", dinner_count)
        ):
            # ── 解析该餐的目标热量和宏量营养素目标 ──
            meal_target = self._meal_target(daily_target_calories, meal_type)
            # meal_ratio: 早餐30%, 午餐40%, 晚餐30%
            macro_targets = self._resolve_macro_targets(
                daily_target_calories, meal_type, diet_goal, goal_type
            )
            meal_candidates = []

            for recipe in candidate_recipes:
                # ── 已推荐去重：同一道菜不重复出现 ──
                if recipe.get("id") in used_recipe_ids:
                    continue

                # ── 过敏硬拦截：含过敏食材直接跳过（安全第一）──
                if self._contains_allergy(recipe, allergies):
                    continue

                # ── 忌口硬拦截 ──
                if self._contains_dislike(recipe, dislikes):
                    continue

                # =============================================================
                # 三组件打分
                # =============================================================

                # 组件1：协同过滤分 [1, 5]
                # 内部二级降级：SVD嵌入 → V1相似用户加权平均
                model_cf_score = self._calculate_model_cf_score(
                    user_id=user_id,
                    recipe=recipe,
                    user_profile=user_profile,
                    similar_users=similar_users
                )

                # 组件2：规则护栏分 [0, 5]
                # 四个子维度加权：能量适配 0.35 + 宏量适配 0.35 + 目标契合 0.20 + 慢病约束 0.10
                rule_guardrail_score = self._calculate_health_score(
                    recipe,
                    meal_type,
                    meal_target,
                    macro_targets,
                    goal_type,
                    chronic_diseases
                )

                # 组件3：GBDT 营养匹配 ML 分 [0, 5]
                # 先构建33维特征向量，再调用 GBDT 预测
                # 模型不可用时回退到 rule_guardrail_score
                nutrition_feature_map = self._build_nutrition_feature_map(
                    recipe=recipe,
                    meal_type=meal_type,
                    meal_target=meal_target,
                    macro_targets=macro_targets,
                    goal_type=goal_type,
                    chronic_diseases=chronic_diseases
                )
                nutrition_ml_score = self._calculate_nutrition_ml_score(
                    nutrition_feature_map,
                    fallback_score=rule_guardrail_score
                )

                # =============================================================
                # ★ 核心融合公式 ★
                # FinalScore(5分制) = CF×0.45 + NutritionML×0.35 + Guard×0.20
                # 权重来自6组对照实验验证（见 weight_sensitivity_analysis.py）
                # =============================================================
                final_score = (
                    model_cf_score * 0.45
                    + nutrition_ml_score * 0.35
                    + rule_guardrail_score * 0.20
                )

                # ── 热量适配硬惩罚 ──
                # 问题：热门但热量严重偏低的食谱，CF+ML可碾压热量合适的食谱
                # 解决：如果即使用该目标最大份量也达不到餐目标的60%，直接腰斩最终分
                if goal_type in ("healthy_weight_gain", "muscle_toning"):
                    recipe_calories = self._safe_float(
                        recipe.get("totalCalories", recipe.get("calories", 0))
                    )
                    if recipe_calories > 0 and meal_target > 0:
                        # 查该目标的份量上界
                        _, serving_upper = self._goal_serving_bounds(goal_type)
                        max_possible = recipe_calories * serving_upper
                        if max_possible < meal_target * 0.6:
                            # 放大到上限后仍达不到目标60% → 这道菜怎么吃都不够 → 腰斩
                            final_score *= 0.5
                        elif recipe_calories < meal_target * 0.4:
                            # 基础热量不到目标40%（即使放大后勉强够，本质也不合适）→ 打折
                            final_score *= 0.7

                # 份量个性化调整
                enriched_recipe = self._personalize_serving(
                    recipe,
                    meal_target,
                    macro_targets,
                    goal_type
                )

                # 填充输出字段
                enriched_recipe["mealType"] = meal_type
                enriched_recipe["collaborativeScore"] = round(model_cf_score, 2)
                enriched_recipe["modelCfScore"] = round(model_cf_score, 2)        # 前端使用的字段名
                enriched_recipe["nutritionMlScore"] = round(nutrition_ml_score, 2)
                enriched_recipe["healthScore"] = round(rule_guardrail_score, 2)
                # ★ 转为百分制显示 ★
                enriched_recipe["matchScore"] = round(final_score * 20, 0)

                # 生成推荐理由和标签
                serving_factor = self._safe_float(
                    enriched_recipe.get("servingFactor", 1.0)
                ) or 1.0
                enriched_recipe["recommendationReason"] = self._build_reason(
                    meal_type,
                    goal_type,
                    model_cf_score,
                    rule_guardrail_score,
                    enriched_recipe,
                    daily_target_calories,
                    macro_targets,
                    chronic_diseases,
                    serving_factor
                )
                enriched_recipe["tags"] = self._build_tags(
                    enriched_recipe,
                    goal_type,
                    meal_type,
                    chronic_diseases,
                    macro_targets,
                    serving_factor
                )
                meal_candidates.append(enriched_recipe)

            # ── 排序策略（多级排序）──
            # 主排序：matchScore 降序
            # 次排序：nutritionMlScore 降序 → collaborativeScore 降序
            # 第三排序：热量偏差最小的优先（用负绝对值实现）
            meal_candidates.sort(
                key=lambda item: (
                    item.get("matchScore", 0),
                    item.get("nutritionMlScore", 0),
                    item.get("collaborativeScore", 0),
                    -abs(self._safe_float(item.get("totalCalories", 0)) - meal_target)
                ),
                reverse=True
            )

            # 取该餐的 Top-N
            top_recipes = meal_candidates[:limit]
            grouped[meal_type] = top_recipes
            # 标记已推荐，防止出现在其他餐次
            for r in top_recipes:
                used_recipe_ids.add(r.get("id"))

        return grouped

    # =========================================================================
    # 组件1：协同过滤分（带二级降级）
    # =========================================================================

    def _calculate_model_cf_score(
        self,
        user_id: Any,
        recipe: Dict[str, Any],
        user_profile: Dict[str, Any],
        similar_users
    ) -> float:
        """
        计算协同过滤分 [1, 5]，内部实现二级降级：

        第一优先：model_runtime.score_cf()
          → 从 SVD 嵌入字典取出8维向量，余弦相似度 + Sigmoid校准
          → 如果用户/食谱不在嵌入字典中（冷用户/冷食谱）→ 返回 None

        第二降级：父类的 _calculate_collaborative_score()
          → 对4个最相似用户，加权平均他们对这道菜的评分
          → 评分来源：实时从数据库加载的真实交互记录
          → 如果相似用户都没吃过这道菜 → 返回 3.2（中性分）

        设计意图：
          第二降级的评分和训练 SVD 的评分来自同一数据源（load_real_interactions），
          保证了"模型推理"和"规则回退"两个路径打出的分具有可比性。
        """
        # 先算好回退分（不管模型能不能用，提前准备）
        fallback_score = self._calculate_collaborative_score(
            recipe.get("id"), similar_users
        )

        # 构建 CF 预测所需的食谱特征（路径3备用）
        recipe_features = {
            "calories": self._safe_float(
                recipe.get("totalCalories", recipe.get("calories", 0))
            ),
            "protein": self._safe_float(recipe.get("protein", 0)),
            "carbs": self._safe_float(recipe.get("carbs", 0)),
            "fat": self._safe_float(recipe.get("fat", 0))
        }

        # 尝试 ML 模型推理
        model_score = self.model_runtime.score_cf(
            user_id=user_id,
            recipe_id=recipe.get("id"),
            user_profile=user_profile,
            recipe_features=recipe_features,
            fallback_score=fallback_score    # 模型失败时用这个
        )

        # 安全钳制：确保最终分在 [1, 5] 区间
        return self._clamp(
            self._safe_float(model_score) or fallback_score, 1.0, 5.0
        )

    # =========================================================================
    # 组件2：GBDT 营养匹配 ML 分（带降级）
    # =========================================================================

    def _calculate_nutrition_ml_score(
        self,
        feature_map: Dict[str, float],
        fallback_score: float
    ) -> float:
        """
        计算 GBDT 营养匹配分 [0, 5]，带降级。

        首选：model_runtime.score_nutrition_ml()
          → 按33维特征顺序构建向量 → GBDT 回归器预测 → 归一化到 [0,5]

        降级：如果 GBDT 不可用 → 直接使用规则护栏分作为输出
          规则护栏分和 GBDT 分的内在一致性：GBDT 的训练标签正是规则护栏分！
          所以规则护栏分作为 GBDT 的 fallback 是语义一致的。
        """
        model_score = self.model_runtime.score_nutrition_ml(
            feature_map,
            fallback_score=fallback_score
        )
        return self._clamp(
            self._safe_float(model_score) or fallback_score, 0.0, 5.0
        )

    # =========================================================================
    # 33维特征构建
    # =========================================================================

    def _build_nutrition_feature_map(
        self,
        recipe: Dict[str, Any],
        meal_type: str,
        meal_target: float,
        macro_targets: Dict[str, float],
        goal_type: str,
        chronic_diseases: str
    ) -> Dict[str, float]:
        """
        构建 GBDT 模型的33维特征向量（以字典格式返回供后续排序）。

        33维特征分组：
          ┌──────────────────────┬──────┬──────────────────────────────────────┐
          │ 特征组                │ 维度  │ 名称                                  │
          ├──────────────────────┼──────┼──────────────────────────────────────┤
          │ 食谱基础营养           │ 8维  │ calories, protein, carbs, fat,        │
          │                      │      │ fiber, sugar, sodium, gi              │
          │ 餐次营养目标           │ 4维  │ meal_target_calories, target_protein, │
          │                      │      │ target_carbs, target_fat              │
          │ 匹配度预计算           │ 4维  │ energy_fit, protein_fit,              │
          │                      │      │ carb_fit, fat_fit                     │
          │ 餐次 One-Hot          │ 3维  │ is_breakfast, is_lunch, is_dinner     │
          │ 目标类型 One-Hot      │ 10维 │ goal_fat_loss ~ goal_senior_wellness  │
          │ 慢病标记              │ 3维  │ has_diabetes, has_hyperlipidemia,     │
          │                      │      │ has_hypertension                      │
          ├──────────────────────┼──────┼──────────────────────────────────────┤
          │ 合计                  │ 33维 │                                      │
          └──────────────────────┴──────┴──────────────────────────────────────┘

        One-Hot 编码：将"目标类型"这种分类特征转为多个 0/1 开关。
        例如 goal_type="blood_sugar_control" →
          goal_blood_sugar_control=1.0, 其余9个 goal_xxx=0.0

        匹配度预计算特征：将 V1 规则引擎的中间结果作为特征喂给 GBDT。
        这些预计算值与最终评分高度相关，能显著提升 GBDT 的预测精度。
        """
        # 提取食谱的8项基础营养值
        calories = self._safe_float(
            recipe.get("totalCalories", recipe.get("calories", 0))
        )
        protein = self._safe_float(recipe.get("protein", 0))
        carbs = self._safe_float(recipe.get("carbs", 0))
        fat = self._safe_float(recipe.get("fat", 0))
        fiber = self._safe_float(recipe.get("fiber", 0))
        sugar = self._safe_float(recipe.get("sugar", 0))
        sodium = self._safe_float(
            recipe.get("sodium", recipe.get("salt", recipe.get("na", 0)))
        )
        gi = self._safe_float(recipe.get("gi", recipe.get("giValue", 0)))

        return {
            # ── 8维：食谱基础营养 ──
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "fiber": fiber,
            "sugar": sugar,
            "sodium": sodium,
            "gi": gi,
            # ── 4维：餐次营养目标 ──
            "meal_target_calories": self._safe_float(meal_target),
            "target_protein": self._safe_float(macro_targets.get("protein", 0)),
            "target_carbs": self._safe_float(macro_targets.get("carbs", 0)),
            "target_fat": self._safe_float(macro_targets.get("fat", 0)),
            # ── 4维：匹配度预计算（V1规则引擎的中间结果）──
            "energy_fit": self._energy_fit_score(calories, meal_target),
            "protein_fit": self._target_fit_score(
                protein, macro_targets.get("protein", 0)
            ),
            "carb_fit": self._target_fit_score(
                carbs, macro_targets.get("carbs", 0)
            ),
            "fat_fit": self._target_fit_score(
                fat, macro_targets.get("fat", 0)
            ),
            # ── 3维：餐次 One-Hot ──
            "is_breakfast": 1.0 if meal_type == "breakfast" else 0.0,
            "is_lunch": 1.0 if meal_type == "lunch" else 0.0,
            "is_dinner": 1.0 if meal_type == "dinner" else 0.0,
            # ── 10维：目标类型 One-Hot ──
            "goal_fat_loss": 1.0 if goal_type == "fat_loss" else 0.0,
            "goal_muscle_toning": 1.0 if goal_type == "muscle_toning" else 0.0,
            "goal_weight_maintenance": 1.0 if goal_type == "weight_maintenance" else 0.0,
            "goal_healthy_weight_gain": 1.0 if goal_type == "healthy_weight_gain" else 0.0,
            "goal_blood_sugar_control": 1.0 if goal_type == "blood_sugar_control" else 0.0,
            "goal_lipid_control": 1.0 if goal_type == "lipid_control" else 0.0,
            "goal_low_sodium": 1.0 if goal_type == "low_sodium" else 0.0,
            "goal_pregnancy_nutrition": 1.0 if goal_type == "pregnancy_nutrition" else 0.0,
            "goal_child_growth": 1.0 if goal_type == "child_growth" else 0.0,
            "goal_senior_wellness": 1.0 if goal_type == "senior_wellness" else 0.0,
            # ── 3维：慢病标记 ──
            "has_diabetes": 1.0 if self._contains_any(
                chronic_diseases, ["diabetes", "糖尿病", "血糖", "控糖"]
            ) else 0.0,
            "has_hyperlipidemia": 1.0 if self._contains_any(
                chronic_diseases, ["hyperlipidemia", "高血脂", "血脂", "高脂血症", "lipid"]
            ) else 0.0,
            "has_hypertension": 1.0 if self._contains_any(
                chronic_diseases, ["hypertension", "高血压", "血压", "控压"]
            ) else 0.0
        }

    # =========================================================================
    # 食谱营养保护（覆写 V1）
    # =========================================================================

    def _recalculate_recipe_nutrition(self, recipe):
        """
        从食材列表汇总计算食谱营养，带保护逻辑。

        保护逻辑：如果食材级重算导致热量缩水超过30%，
        则回退到原始热量并等比例放大其他营养值。
        原因：某些食谱的食材表条目可能不完整，
        如果汇总值严重偏低，直接使用会误导后续的份量调整。
        """
        original_calories = self._safe_float(
            recipe.get("totalCalories", recipe.get("calories", 0))
        )
        # 先用 V1 方法重算
        recipe = super()._recalculate_recipe_nutrition(recipe)
        recalculated_calories = self._safe_float(
            recipe.get("totalCalories", recipe.get("calories", 0))
        )

        if original_calories > 0 and recalculated_calories > 0:
            ratio = recalculated_calories / original_calories
            if ratio < 0.7:
                # 热量缩水严重，回退并以原始热量为基准放缩所有营养指标
                scale = original_calories / recalculated_calories
                recipe["totalCalories"] = round(original_calories, 0)
                recipe["calories"] = round(original_calories, 0)
                recipe["protein"] = round(
                    self._safe_float(recipe.get("protein", 0)) * scale, 1
                )
                recipe["carbs"] = round(
                    self._safe_float(recipe.get("carbs", 0)) * scale, 1
                )
                recipe["fat"] = round(
                    self._safe_float(recipe.get("fat", 0)) * scale, 1
                )
                recipe["fiber"] = round(
                    self._safe_float(recipe.get("fiber", 0)) * scale, 1
                )

        return recipe

    # =========================================================================
    # 份量因子计算（覆写 V1，范围更宽）
    # =========================================================================

    def _resolve_serving_factor(
        self,
        recipe,
        meal_target_calories,
        macro_targets,
        goal_type
    ):
        """
        计算份量调整因子，公式：0.6 × 能量因子 + 0.4 × 宏量因子

        能量因子 = 餐目标热量 / 食谱热量 （例：目标400，食谱500 → 0.8 → 减量至80%）
        宏量因子 = mean(蛋白比 + 碳水比 + 脂肪比)，每项钳制在 [0.5, 2.0]

        然后经过两层约束：
          1. 目标类型约束：不同目标有不同的份量上下界
          2. 全局安全边界：[0.5, 2.2]

        V2 的上界 (2.2) 比 V1 (1.5) 更宽，
        便于增肌/增重用户能吃到足够多的份量。
        """
        calories = self._safe_float(
            recipe.get("totalCalories", recipe.get("calories", 0))
        )

        # 能量因子：目标热量 ÷ 食谱实际热量
        energy_factor = None
        if calories > 0 and meal_target_calories > 0:
            energy_factor = meal_target_calories / calories

        # 宏量因子：蛋白/碳水/脂肪比值的平均
        # 每项比值钳制在 [0.5, 2.0]，防止极端的单一营养素主导
        macro_factors = []
        for macro_key, recipe_key in (
            ("protein", "protein"),
            ("carbs", "carbs"),
            ("fat", "fat")
        ):
            target_value = self._safe_float((macro_targets or {}).get(macro_key, 0))
            actual_value = self._safe_float(recipe.get(recipe_key, 0))
            if target_value > 0 and actual_value > 0:
                macro_factors.append(
                    self._clamp(target_value / actual_value, 0.5, 2.0)
                )

        macro_factor = (
            sum(macro_factors) / len(macro_factors) if macro_factors else None
        )

        # 加权融合：能量60% + 宏量40%
        if energy_factor is not None and macro_factor is not None:
            factor = 0.6 * energy_factor + 0.4 * macro_factor
        elif energy_factor is not None:
            factor = energy_factor
        elif macro_factor is not None:
            factor = macro_factor
        else:
            factor = 1.0

        # 两层约束
        lower_bound, upper_bound = self._goal_serving_bounds(goal_type)
        factor = self._clamp(factor, lower_bound, upper_bound)
        return self._clamp(factor, 0.5, 2.2)

    def _goal_serving_bounds(self, goal_type):
        """
        10种饮食目标的份量调整上下界。

        以减肥(fat_loss)为例：[0.6, 1.0] 表示至少吃60%，最多吃标准份量。
        以增重(healthy_weight_gain)为例：[1.0, 2.2] 表示至少吃标准份，最多2.2倍。
        """
        mapping = {
            "fat_loss": (0.6, 1.0),          # 减肥：只能减量不能加量
            "muscle_toning": (0.9, 1.6),      # 增肌：至少90%，最多1.6倍
            "weight_maintenance": (0.85, 1.2), # 维持：小范围浮动
            "healthy_weight_gain": (1.0, 2.2), # 增重：只能加量不能减量
            "blood_sugar_control": (0.75, 1.1),# 控糖：偏谨慎
            "lipid_control": (0.75, 1.1),      # 控脂：偏谨慎
            "low_sodium": (0.8, 1.2),          # 控压：基本维持
            "pregnancy_nutrition": (0.9, 1.35),# 孕期：保证营养充足
            "child_growth": (0.9, 1.4),        # 儿童：保证生长发育
            "senior_wellness": (0.75, 1.2)     # 老年：控制食量
        }
        return mapping.get(goal_type, (0.75, 1.35))
