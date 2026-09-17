# -*- coding: utf-8 -*-
"""
V1 基础推荐引擎 —— 所有推荐核心方法的基础实现
======================================================================
这是整个推荐系统的代码基石，1075行，V2 引擎继承它并提供 ML 增强。

文件内容按功能分为以下几个部分：
  【A】种子数据（硬编码8用户+24条交互，数据库不可用时的回退）
  【B】推荐主流程（V1的二组件融合：CF×0.55 + 规则护栏×0.45）
  【C】用户画像与相似用户（16维特征向量 + 余弦相似度）
  【D】协同过滤（相似用户加权平均评分）
  【E】规则护栏评分（四大子维度：能量×0.35 + 宏量×0.35 + 目标×0.20 + 慢病×0.10）
  【F】10种目标类型差异化打分策略（300+行，核心领域知识）
  【G】3种慢病约束惩罚规则
  【H】份量个性化调整（因子公式 + 10种目标上下界 + 完整缩放）
  【I】能量目标解析（四级优先级：显式目标 > BMR×系数 > Mifflin估算 > 1800）
  【J】宏量营养素目标解析（显式目标优先 → 按比例计算 → 默认配比）
  【K】辅助方法（过敏检测/餐次推断/烹饪方式判断/标签/理由/数学工具）
"""

import math
import re
from copy import deepcopy


class RecommendEngine:
    """V1 基础推荐引擎。提供所有推荐核心方法，被 V2 继承。"""

    def __init__(self):
        # 加载内置种子数据（数据库不可用时的回退方案）
        self.user_profiles = self._load_user_profiles()
        self.user_recipe_data = self._load_user_recipe_data()

    # =========================================================================
    # 【A】种子数据 —— 覆盖8种饮食目标的样例用户和交互记录
    # =========================================================================

    def _load_user_profiles(self):
        """
        硬编码8个样例用户画像，每种饮食目标一个代表。
        这些数据在实际部署时会被 real_data_source.load_real_user_profiles() 替换。
        设计时确覆盖了：减肥/增肌/控糖/控压/控脂/维持/孕期/老年。
        """
        return {
            101: {  # 减肥减脂 — 青年女性
                "goalType": "fat_loss",
                "activityLevel": "light",
                "age": 25,
                "gender": "female",
                "bmi": 24.0,
                "chronicDiseases": "",
                "allergies": ""
            },
            102: {  # 增肌塑形 — 青年男性
                "goalType": "muscle_toning",
                "activityLevel": "moderate",
                "age": 27,
                "gender": "male",
                "bmi": 23.0,
                "chronicDiseases": "",
                "allergies": ""
            },
            103: {  # 控糖饮食 — 中年女性，糖尿病
                "goalType": "blood_sugar_control",
                "activityLevel": "light",
                "age": 46,
                "gender": "female",
                "bmi": 26.0,
                "chronicDiseases": "diabetes",
                "allergies": ""
            },
            104: {  # 控压低盐 — 中老年男性，高血压
                "goalType": "low_sodium",
                "activityLevel": "light",
                "age": 58,
                "gender": "male",
                "bmi": 25.0,
                "chronicDiseases": "hypertension",
                "allergies": ""
            },
            105: {  # 控脂降脂 — 中年男性，高血脂
                "goalType": "lipid_control",
                "activityLevel": "moderate",
                "age": 42,
                "gender": "male",
                "bmi": 27.0,
                "chronicDiseases": "hyperlipidemia",
                "allergies": ""
            },
            106: {  # 维持体重 — 青年女性，虾过敏
                "goalType": "weight_maintenance",
                "activityLevel": "moderate",
                "age": 30,
                "gender": "female",
                "bmi": 21.0,
                "chronicDiseases": "",
                "allergies": "shrimp"
            },
            107: {  # 孕妇营养 — 青年女性
                "goalType": "pregnancy_nutrition",
                "activityLevel": "light",
                "age": 29,
                "gender": "female",
                "bmi": 22.0,
                "chronicDiseases": "",
                "allergies": ""
            },
            108: {  # 老年养生 — 老年女性，高血压
                "goalType": "senior_wellness",
                "activityLevel": "light",
                "age": 66,
                "gender": "female",
                "bmi": 23.0,
                "chronicDiseases": "hypertension",
                "allergies": ""
            }
        }

    def _load_user_recipe_data(self):
        """
        硬编码24条用户-食谱评分记录（每个用户3道菜，评分4-5）。
        覆盖12道候选食谱，为相似用户匹配提供初始评分数据。
        """
        return [
            {"user_id": 101, "recipe_id": 3, "rating": 5},
            {"user_id": 101, "recipe_id": 6, "rating": 4},
            {"user_id": 101, "recipe_id": 8, "rating": 5},
            {"user_id": 102, "recipe_id": 2, "rating": 4},
            {"user_id": 102, "recipe_id": 4, "rating": 5},
            {"user_id": 102, "recipe_id": 7, "rating": 4},
            {"user_id": 103, "recipe_id": 1, "rating": 4},
            {"user_id": 103, "recipe_id": 5, "rating": 5},
            {"user_id": 103, "recipe_id": 9, "rating": 5},
            {"user_id": 104, "recipe_id": 1, "rating": 5},
            {"user_id": 104, "recipe_id": 7, "rating": 4},
            {"user_id": 104, "recipe_id": 12, "rating": 5},
            {"user_id": 105, "recipe_id": 5, "rating": 4},
            {"user_id": 105, "recipe_id": 9, "rating": 5},
            {"user_id": 105, "recipe_id": 12, "rating": 4},
            {"user_id": 106, "recipe_id": 10, "rating": 5},
            {"user_id": 106, "recipe_id": 11, "rating": 4},
            {"user_id": 106, "recipe_id": 7, "rating": 4},
            {"user_id": 107, "recipe_id": 2, "rating": 4},
            {"user_id": 107, "recipe_id": 11, "rating": 5},
            {"user_id": 107, "recipe_id": 12, "rating": 4},
            {"user_id": 108, "recipe_id": 1, "rating": 4},
            {"user_id": 108, "recipe_id": 9, "rating": 5},
            {"user_id": 108, "recipe_id": 12, "rating": 5}
        ]

    # =========================================================================
    # 【B】推荐主流程（V1 的二组件融合版本）
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
        V1 推荐主流程：每个食谱只归入一个餐次，二组件加权融合。

        流程：
          1. 构建用户画像 → 找4个最相似用户
          2. 解析全天能量目标 → 分配三餐比例（早30% 午40% 晚30%）
          3. 对每道候选食谱：
             a) 推断餐次归属（关键词 + 热量范围）
             b) 过敏检查 → 硬拦截
             c) 协同过滤分：相似用户对该食谱评分的加权平均
             d) 规则护栏分：能量/宏量/目标/慢病四维加权
             e) 融合：final_score = CF×0.55 + 规则护栏×0.45
             f) 份量个性化调整
             g) 生成推荐理由和标签
          4. 每餐排序取 Top-N

        V2 覆写了这个方法，主要改进：
          - 取消餐次归属限制（每道菜参与三餐竞争）
          - 三组件融合（加入 GBDT 营养ML分）
          - 全局去重
        """
        candidate_recipes = candidate_recipes or []
        grouped = {"breakfast": [], "lunch": [], "dinner": []}
        if not candidate_recipes:
            return grouped

        health_info = health_info or {}
        diet_goal = diet_goal or {}

        # ── 用户画像与相似用户 ──
        user_profile = self._build_user_profile(health_info, diet_goal)
        similar_users = self._find_similar_users(user_profile)
        goal_type = self._normalize_text(diet_goal.get("goalType", ""))
        daily_target_calories = self._resolve_daily_energy_target(
            health_info, diet_goal, goal_type
        )

        allergies = self._split_tokens(health_info.get("allergies", ""))
        dislikes = self._split_tokens(health_info.get("dislikes", ""))
        chronic_diseases = self._normalize_text(health_info.get("chronicDiseases", ""))

        for meal_type, limit in (
            ("breakfast", breakfast_count),
            ("lunch", lunch_count),
            ("dinner", dinner_count)
        ):
            meal_target = self._meal_target(daily_target_calories, meal_type)
            macro_targets = self._resolve_macro_targets(
                daily_target_calories, meal_type, diet_goal, goal_type
            )
            meal_candidates = []

            for recipe in candidate_recipes:
                # ── 餐次归属判断（V1特色：每个食谱只归入一餐）──
                inferred_meal_type = (
                    recipe.get("mealType") or self._infer_meal_type(recipe)
                )
                if inferred_meal_type != meal_type:
                    continue  # 不属于当前餐次，跳过

                # ── 过敏硬拦截 ──
                if self._contains_allergy(recipe, allergies):
                    continue

                # ── 忌口硬拦截 ──
                if self._contains_dislike(recipe, dislikes):
                    continue

                # ── 组件1：协同过滤分 [1,5] ──
                collaborative_score = self._calculate_collaborative_score(
                    recipe.get("id"), similar_users
                )

                # ── 组件2：规则护栏分 [0,5] ──
                # 这是 V1 唯一的营养评估组件（V2 拆分成了 ML + Guard 两个组件）
                health_score = self._calculate_health_score(
                    recipe,
                    meal_type,
                    meal_target,
                    macro_targets,
                    goal_type,
                    chronic_diseases
                )

                # ── V1的融合公式（二组件）──
                final_score = collaborative_score * 0.55 + health_score * 0.45

                enriched_recipe = self._personalize_serving(
                    recipe,
                    meal_target,
                    macro_targets,
                    goal_type
                )
                enriched_recipe["mealType"] = meal_type
                enriched_recipe["collaborativeScore"] = round(collaborative_score, 2)
                enriched_recipe["healthScore"] = round(health_score, 2)
                enriched_recipe["matchScore"] = round(final_score * 20, 0)

                serving_factor = self._safe_float(
                    enriched_recipe.get("servingFactor", 1.0)
                ) or 1.0
                enriched_recipe["recommendationReason"] = self._build_reason(
                    meal_type,
                    goal_type,
                    collaborative_score,
                    health_score,
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

            # ── 排序：匹配分 > CF分 > 热量偏差 ──
            meal_candidates.sort(
                key=lambda item: (
                    item.get("matchScore", 0),
                    item.get("collaborativeScore", 0),
                    -abs(self._safe_float(item.get("totalCalories", 0)) - meal_target)
                ),
                reverse=True
            )
            grouped[meal_type] = meal_candidates[:limit]

        return grouped

    # =========================================================================
    # 【C】用户画像与相似用户计算
    # =========================================================================

    def _build_user_profile(self, health_info, diet_goal):
        """将前端传入的 health_info + diet_goal 合并为标准画像字典。"""
        return {
            "goalType": diet_goal.get("goalType", ""),
            "activityLevel": health_info.get("activityLevel", ""),
            "age": self._safe_float(health_info.get("age")) or 30,
            "gender": health_info.get("gender", ""),
            "bmi": self._safe_float(health_info.get("bmi")) or 22,
            "chronicDiseases": health_info.get("chronicDiseases", ""),
            "allergies": health_info.get("allergies", "")
        }

    def _find_similar_users(self, user_profile):
        """
        从 user_profiles 中找到与目标用户最相似的4个用户。

        方法：
          1. 将目标用户画像转为16维特征向量
          2. 对每个已有用户同样转16维向量
          3. 计算余弦相似度
          4. 排序取前4

        为什么是4个？
          太少 → 单个用户的噪音影响大
          太多 → 会引入不相似用户的无关数据
          4是协同过滤领域常用的经验值。
        """
        target_vector = self._profile_to_vector(user_profile)
        similarities = []
        for other_user_id, other_profile in self.user_profiles.items():
            other_vector = self._profile_to_vector(other_profile)
            similarity = self._cosine_similarity(target_vector, other_vector)
            similarities.append((other_user_id, similarity))
        similarities.sort(key=lambda item: item[1], reverse=True)
        return similarities[:4]

    def _profile_to_vector(self, profile):
        """
        将用户画像转为16维归一化特征向量。

        16维构成：
          [0] age/80          → 年龄归一化（80岁为基准）
          [1] bmi/40           → BMI归一化（40为极限）
          [2] is_male          → 性别标记（男=1, 女=0）
          [3-9] goal_type      → 7种目标 One-Hot（fat_loss ~ senior_wellness）
          [10-12] activity     → 3种活动量 One-Hot（高/中/轻）
          [13-15] disease      → 3种慢病 One-Hot（糖尿病/高血压/高血脂）

        除法归一化：将绝对数值映射到 [0,1] 区间，避免量纲差异影响余弦相似度。
        One-Hot：将分类变量转为 0/1 开关，不同目标间的距离均等。
        """
        goal = self._normalize_text(profile.get("goalType", ""))
        activity = self._normalize_text(profile.get("activityLevel", ""))
        gender = self._normalize_text(profile.get("gender", ""))
        diseases = self._normalize_text(profile.get("chronicDiseases", ""))

        return [
            # ── 数值特征（归一化到 [0,1]）──
            self._safe_float(profile.get("age")) / 80.0,
            self._safe_float(profile.get("bmi")) / 40.0,
            1.0 if gender in ("male", "男") else 0.0,
            # ── 目标类型 One-Hot（7维）──
            1.0 if "fat_loss" in goal else 0.0,
            1.0 if "muscle_toning" in goal else 0.0,
            1.0 if "blood_sugar_control" in goal else 0.0,
            1.0 if "lipid_control" in goal else 0.0,
            1.0 if "low_sodium" in goal else 0.0,
            1.0 if "pregnancy_nutrition" in goal else 0.0,
            1.0 if "senior_wellness" in goal else 0.0,
            # ── 活动量 One-Hot（3维）──
            1.0 if "high" in activity or "高" in activity else 0.0,
            1.0 if "moderate" in activity or "中" in activity else 0.0,
            1.0 if "light" in activity or "轻" in activity else 0.0,
            # ── 慢病 One-Hot（3维）──
            1.0 if "diabetes" in diseases or "糖" in diseases else 0.0,
            1.0 if "hypertension" in diseases or "血压" in diseases else 0.0,
            1.0 if "hyperlipidemia" in diseases or "血脂" in diseases else 0.0
        ]

    def _cosine_similarity(self, left, right):
        """
        两个向量的余弦相似度。

        公式：cos(θ) = (A·B) / (|A| × |B|)

        取值范围：[-1, 1]（1 = 方向完全一致，0 = 无关，-1 = 完全相反）
        余弦相似度只关注方向不关注大小，适合比较用户画像这种
        "特征构成相似度" 而非 "绝对值接近度" 的场景。
        """
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    # =========================================================================
    # 【D】协同过滤 —— 基于相似用户的加权平均评分（V1方式，V2中作为回退）
    # =========================================================================

    def _calculate_collaborative_score(self, recipe_id, similar_users):
        """
        协同过滤分 = Σ(相似用户对该食谱的评分 × 该用户的相似度) / Σ(相似度)

        本质是相似用户的评分加权平均，相似度越高的用户权重越大。

        如果4个相似用户都没有对该食谱的评分记录 → 返回 3.2（中性分）。
        3.2 的选择原因：在所有用户对所有食谱的评分中，均值约3.2。
        """
        weighted_sum = 0.0
        similarity_sum = 0.0
        for other_user_id, similarity in similar_users:
            rating = self._find_rating(other_user_id, recipe_id)
            if rating is None or similarity <= 0:
                continue
            weighted_sum += rating * similarity
            similarity_sum += similarity

        if similarity_sum == 0:
            return 3.2  # 中性分
        return weighted_sum / similarity_sum

    def _find_rating(self, user_id, recipe_id):
        """
        从交互记录字典中查找指定用户对指定食谱的评分。
        优先从 self.user_recipe_data（可能被 V2 替换为数据库数据）中查找。
        找不到返回 None。
        """
        for item in self.user_recipe_data:
            if item["user_id"] == user_id and item["recipe_id"] == recipe_id:
                return float(item["rating"])
        return None

    # =========================================================================
    # 【E】规则护栏评分 —— 四维子评分的加权融合
    # =========================================================================

    def _calculate_health_score(
        self,
        recipe,
        meal_type,
        meal_target_calories,
        macro_targets,
        goal_type,
        chronic_diseases
    ):
        """
        规则护栏总分（百分制）→ 除以20转5分制。

        四个子维度和权重：
          能量适配 (energy_fit)  → 35%  食谱热量是否接近该餐目标
          宏量适配 (macro_fit)   → 35%  蛋白/碳水/脂肪是否接近目标配比
          目标契合 (goal_fit)    → 20%  是否符合特定饮食目标（10种不同策略）
          慢病约束 (disease_fit)  → 10%  慢性病患者是否有额外禁忌

        设计原理：
          能量和宏量各35%是最核心的两个维度——食物最基本的属性
          就是"吃多少"（能量）和"吃什么"（宏量比例）。
          目标契合20%是针对用户个性化目标的微调。
          慢病约束10%是安全兜底——只在违规时扣分。
        """
        # 提取食谱营养值
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

        # ── 四维子评分 ──
        energy_fit = self._energy_fit_score(calories, meal_target_calories)
        macro_fit = self._macro_fit_score(protein, carbs, fat, macro_targets)
        goal_fit = self._goal_fit_score(
            recipe,
            goal_type,
            calories, protein, carbs, fat, fiber, sugar, sodium, gi,
            meal_target_calories,
            macro_targets
        )
        disease_fit = self._disease_fit_score(
            recipe,
            chronic_diseases,
            carbs, fat, fiber, sugar, sodium, gi,
            macro_targets
        )

        # ── 加权融合（百分制）──
        health_score_100 = (
            0.35 * energy_fit
            + 0.35 * macro_fit
            + 0.20 * goal_fit
            + 0.10 * disease_fit
        )
        # 除以20转为5分制
        return self._clamp(health_score_100 / 20.0, 0.0, 5.0)

    # =========================================================================
    # 【F】10种饮食目标的差异化打分策略（本文件核心，300+行）
    # =========================================================================

    def _goal_fit_score(
        self,
        recipe,
        goal_type,
        calories, protein, carbs, fat, fiber, sugar, sodium, gi,
        meal_target_calories, macro_targets
    ):
        """
        根据用户的饮食目标类型，对食谱进行差异化打分。

        基础分：60分（及格线）
        然后根据目标类型加减分，不同目标关注不同的营养维度。

        10种目标策略速查：
          fat_loss (减肥减脂)        → 高蛋白 + 控制脂肪 + 低热量 + 高纤维
          muscle_toning (增肌塑形)   → 高蛋白 + 充足碳水 + 充足热量
          weight_maintenance (维持)  → 能量均衡 + 宏量均衡
          healthy_weight_gain (增重) → 高热量 + 高碳水 + 充足蛋白
          blood_sugar_control (控糖) → 低碳水 + 高纤维 + 低GI + 低糖
          lipid_control (控脂)       → 低脂肪 + 高纤维
          low_sodium (控压)          → 低钠 + 清淡烹饪
          pregnancy_nutrition (孕期)  → 高蛋白 + 充足热量 + 高纤维
          child_growth (儿童)        → 充足热量 + 蛋白 + 碳水
          senior_wellness (老年)     → 易消化 + 低负担

        每个策略内部先算4个基础匹配度（protein_fit/carb_fit/fat_fit/energy_fit），
        再根据目标类型进行针对性的加减分。
        """
        # 先算四个基础匹配度（0-100分）
        protein_fit = self._target_fit_score(protein, macro_targets.get("protein", 0))
        carb_fit = self._target_fit_score(carbs, macro_targets.get("carbs", 0))
        fat_fit = self._target_fit_score(fat, macro_targets.get("fat", 0))
        energy_fit = self._energy_fit_score(calories, meal_target_calories)

        score = 60.0  # 基础分

        # ── 减肥减脂 ──
        if goal_type == "fat_loss":
            # 重点：控脂肪、增加蛋白以维持饱腹感
            score += 0.20 * protein_fit + 0.10 * energy_fit
            score += 10 if fat <= macro_targets.get("fat", 0) * 1.05 else -10
            score += 8 if fiber >= 4 else 0  # 高纤维增加饱腹感

        # ── 增肌塑形 ──
        elif goal_type == "muscle_toning":
            # 重点：高蛋白 + 充足碳水和能量支持训练
            score += 0.25 * protein_fit + 0.10 * carb_fit + 0.08 * energy_fit
            if meal_target_calories > 0:
                calorie_ratio = calories / meal_target_calories
                if calorie_ratio < 0.5:        # 食谱热量不到目标一半 → 严重不足
                    score -= 35
                elif calorie_ratio < 0.7:       # 食谱热量不到目标70% → 明显不足
                    score -= 25
                elif calorie_ratio < 0.8:       # 原阈值 → 轻微不足
                    score -= 12

        # ── 维持体重 ──
        elif goal_type == "weight_maintenance":
            # 重点：各类均衡
            score += 0.18 * energy_fit + 0.12 * ((protein_fit + carb_fit + fat_fit) / 3.0)

        # ── 健康增重 ──
        elif goal_type == "healthy_weight_gain":
            # 重点：高热量 + 高碳水 + 充足蛋白
            score += 0.22 * energy_fit + 0.12 * carb_fit + 0.08 * protein_fit
            if meal_target_calories > 0:
                calorie_ratio = calories / meal_target_calories
                if calorie_ratio < 0.5:        # 食谱热量不到目标一半 → 严重不足
                    score -= 35
                elif calorie_ratio < 0.7:       # 食谱热量不到目标70% → 明显不足
                    score -= 25
                elif calorie_ratio < 0.9:       # 原阈值 → 轻微不足
                    score -= 12

        # ── 控糖饮食 ──
        elif goal_type == "blood_sugar_control":
            # 重点：碳水≤35g + 高纤维 + 低GI(≤55) + 低糖(≤12g)
            carb_limit = min((macro_targets.get("carbs", 0) * 1.05) or 35, 35)
            score += 20 if carbs <= carb_limit else -20  # 碳水超标严厉扣分
            score += 12 if fiber >= 4 else -4             # 纤维能减缓血糖上升
            score += 10 if 0 < sugar <= 12 else (-8 if sugar > 18 else 0)
            score += 10 if 0 < gi <= 55 else (-8 if gi >= 70 else 0)  # GI低血糖升得慢
            score += 0.06 * fat_fit

        # ── 控脂降脂 ──
        elif goal_type == "lipid_control":
            # 重点：脂肪≤16g + 高纤维
            fat_limit = min((macro_targets.get("fat", 0) * 1.05) or 16, 16)
            score += 20 if fat <= fat_limit else -18
            score += 10 if fiber >= 4 else -4
            score += 0.08 * carb_fit

        # ── 控压低盐 ──
        elif goal_type == "low_sodium":
            # 重点：钠≤350mg + 清淡烹饪方式（蒸/煮/炖）
            score += 24 if 0 < sodium <= 350 else (-16 if sodium > 700 else 0)
            score += 8 if self._is_light_cooking(recipe) else -4
            score += 0.12 * energy_fit

        # ── 孕妇营养 ──
        elif goal_type == "pregnancy_nutrition":
            # 重点：高蛋白 + 充足能量 + 膳食纤维
            score += 0.20 * protein_fit + 0.10 * energy_fit
            score += 8 if fiber >= 3 else 0
            if meal_target_calories > 0 and calories < meal_target_calories * 0.85:
                score -= 12

        # ── 儿童成长 ──
        elif goal_type == "child_growth":
            # 重点：保障生长所需能量 + 蛋白 + 碳水
            score += 0.18 * energy_fit + 0.12 * protein_fit + 0.12 * carb_fit
            if meal_target_calories > 0 and calories < meal_target_calories * 0.85:
                score -= 10

        # ── 老年养生 ──
        elif goal_type == "senior_wellness":
            # 重点：易消化（粥/汤/蒸/软）+ 低钠低脂
            score += 22 if self._is_easy_to_digest(recipe) else -6
            score += 0.10 * protein_fit + 0.08 * fat_fit

        # ── 未指定目标 → 默认均衡 ──
        else:
            score += 0.15 * energy_fit + 0.15 * ((protein_fit + carb_fit + fat_fit) / 3.0)

        return self._clamp(score, 0.0, 100.0)

    # =========================================================================
    # 【G】3种慢病的约束惩罚
    # =========================================================================

    def _disease_fit_score(
        self,
        recipe,
        chronic_diseases,
        carbs, fat, fiber, sugar, sodium, gi,
        macro_targets
    ):
        """
        慢性病约束打分，默认70分（不扣分），违规则从70分开始扣。

        三种慢病（可以同时存在）：
          糖尿病(diabetes) → 碳水超标、纤维不足、糖/GI过高 → 扣分
          高血脂(hyperlipidemia) → 脂肪超标、纤维不足 → 扣分
          高血压(hypertension) → 钠超标、重口味烹饪 → 扣分

        惩罚力度设计：
          慢病约束权重只有10%（在 _calculate_health_score 中），
          所以这里的扣分相对温和——不会因为一道菜钠偏高就直接排除，
          但会显著降低综合评分。这是"软约束"而非"硬过滤"。
        """
        if not chronic_diseases:
            return 70.0  # 无慢病 → 默认70分（不干预）

        score = 70.0
        disease_text = self._normalize_text(chronic_diseases)

        # 同时检测中英文慢病关键词
        has_diabetes = self._contains_any(
            disease_text, ["diabetes", "糖尿病", "血糖", "控糖"]
        )
        has_hyperlipidemia = self._contains_any(
            disease_text, ["hyperlipidemia", "高血脂", "血脂", "高脂血症", "lipid"]
        )
        has_hypertension = self._contains_any(
            disease_text, ["hypertension", "高血压", "血压", "控压"]
        )

        # ── 糖尿病约束 ──
        if has_diabetes:
            carb_limit = min((macro_targets.get("carbs", 0) * 1.05) or 35, 35)
            score += 14 if carbs <= carb_limit else -18
            score += 10 if fiber >= 4 else -6
            score += 8 if 0 < sugar <= 12 else (-8 if sugar > 18 else 0)
            score += 8 if 0 < gi <= 55 else (-8 if gi >= 70 else 0)

        # ── 高血脂约束 ──
        if has_hyperlipidemia:
            fat_limit = min((macro_targets.get("fat", 0) * 1.05) or 16, 16)
            score += 14 if fat <= fat_limit else -18
            score += 8 if fiber >= 4 else 0

        # ── 高血压约束 ──
        if has_hypertension:
            # 中餐一餐的标准钠摄入约 300-500mg
            # ≤350mg 是低钠标准，>700mg 严重超标
            score += 14 if 0 < sodium <= 350 else (-14 if sodium > 700 else 0)
            score += 6 if self._is_light_cooking(recipe) else -4

        return self._clamp(score, 0.0, 100.0)

    # =========================================================================
    # 能量 & 宏量匹配度
    # =========================================================================

    def _energy_fit_score(self, calories, meal_target_calories):
        """能量适配分 = 热量值与目标的匹配度（复用 _target_fit_score）"""
        return self._target_fit_score(calories, meal_target_calories)

    def _macro_fit_score(self, protein, carbs, fat, macro_targets):
        """
        宏量营养素适配分 = 蛋白35% + 碳水35% + 脂肪30%

        脂肪权重略低的原因：
          碳水每克4kcal，蛋白质每克4kcal，脂肪每克9kcal。
          在等热量前提下，脂肪的克数本身就少，所以配比偏差的容忍度更高。
        """
        if protein <= 0 and carbs <= 0 and fat <= 0:
            return 45.0  # 所有宏量数据缺失

        protein_fit = self._target_fit_score(protein, macro_targets.get("protein", 0))
        carb_fit = self._target_fit_score(carbs, macro_targets.get("carbs", 0))
        fat_fit = self._target_fit_score(fat, macro_targets.get("fat", 0))

        return 0.35 * protein_fit + 0.35 * carb_fit + 0.30 * fat_fit

    def _target_fit_score(self, actual, target):
        """
        通用目标匹配度评分。根据实际值与目标值的偏差比例打分。

        评分标准（偏差率 = |实际-目标| / 目标）：
          ≤ 8%    → 100分  (非常接近)
          ≤ 15%   → 90分   (接近)
          ≤ 25%   → 78分   (可接受)
          ≤ 35%   → 66分   (偏差较大)
          ≤ 50%   → 52分   (偏差很大)
          > 50%   → 35分   (完全不匹配)

        这是一个阶梯函数，而非连续函数。
        选择阶梯而非平滑的原因：营养学中的"适量"本身就是一个范围概念，
        过于精确的连续函数反而给人一种"毫米级精确"的假象。
        """
        actual = self._safe_float(actual)
        target = self._safe_float(target)
        if actual <= 0 or target <= 0:
            return 55.0  # 数据缺失时的中性分

        diff_ratio = abs(actual - target) / target
        if diff_ratio <= 0.08:
            return 100.0
        if diff_ratio <= 0.15:
            return 90.0
        if diff_ratio <= 0.25:
            return 78.0
        if diff_ratio <= 0.35:
            return 66.0
        if diff_ratio <= 0.50:
            return 52.0
        if diff_ratio <= 0.65:
            return 35.0
        if diff_ratio <= 0.80:
            return 20.0
        return 10.0

    # =========================================================================
    # 推荐理由 & 标签生成
    # =========================================================================

    def _build_reason(
        self,
        meal_type, goal_type,
        collaborative_score, health_score,
        recipe, target_calories, macro_targets,
        chronic_diseases, serving_factor=1.0
    ):
        """
        生成推荐理由文本，最多5条用中文分号连接。

        理由片段类型：
          - 协同过滤匹配分说明
          - 营养模型适配分说明
          - 热量对比（该餐 vs 目标）
          - 宏量配比评价
          - 慢病适配说明
          - 份量调整提示
          - 当前目标偏好说明
        """
        parts = [
            f"协同过滤匹配分 {collaborative_score:.1f}，来源于相似用户的食谱偏好",
            f"营养模型适配分 {health_score:.1f}，综合了能量、宏量营养素和健康约束"
        ]

        calories = self._safe_float(
            recipe.get("totalCalories", recipe.get("calories", 0))
        )
        meal_target = self._meal_target(target_calories, meal_type)
        if calories > 0 and meal_target > 0:
            parts.append(f"该餐热量约 {round(calories)} kcal，参考目标为 {round(meal_target)} kcal")

        # 宏量配比整体评价
        protein = self._safe_float(recipe.get("protein", 0))
        carbs = self._safe_float(recipe.get("carbs", 0))
        fat = self._safe_float(recipe.get("fat", 0))
        macro_fit = (
            self._target_fit_score(protein, macro_targets.get("protein", 0))
            + self._target_fit_score(carbs, macro_targets.get("carbs", 0))
            + self._target_fit_score(fat, macro_targets.get("fat", 0))
        ) / 3.0
        if macro_fit >= 80:
            parts.append("该餐蛋白质/碳水/脂肪配比与当前目标较匹配")
        elif macro_fit >= 65:
            parts.append("该餐宏量营养素结构基本贴近当前目标")

        # 慢病适配
        if chronic_diseases:
            chronic_text = self._normalize_text(chronic_diseases)
            if (
                self._contains_any(chronic_text, ["diabetes", "糖尿病", "血糖", "控糖"])
                and carbs <= 35
            ):
                parts.append("结合你的控糖需求，优先选择了碳水更克制的方案")
            if (
                self._contains_any(chronic_text, ["hyperlipidemia", "高血脂", "血脂", "高脂血症", "lipid"])
                and fat <= 16
            ):
                parts.append("结合你的血脂管理需求，优先考虑了脂肪更可控的方案")
            if (
                self._contains_any(chronic_text, ["hypertension", "高血压", "血压", "控压"])
                and self._is_light_cooking(recipe)
            ):
                parts.append("结合你的血压管理需求，优先考虑了清淡烹饪方式")

        # 份量调整
        if abs(serving_factor - 1.0) >= 0.08:
            parts.append(f"已按你的目标将该食谱份量调整为 {serving_factor:.2f} 倍")

        if goal_type:
            parts.append(f'当前更偏向"{self._goal_label(goal_type)}"目标')

        return "；".join(parts[:5])  # 最多5条

    def _build_tags(
        self,
        recipe, goal_type, meal_type,
        chronic_diseases, macro_targets=None,
        serving_factor=1.0
    ):
        """
        生成推荐标签列表（前端展示用徽章/badge）。

        标签分层：
          基础标签 → 营养标签 → 目标特定标签 → 慢病标签 → 份量标签

        标签采用"追加去重"策略：同一个标签不会重复出现。
        """
        tags = []
        # 基础标签
        self._append_tag(tags, self._meal_label(meal_type))
        self._append_tag(tags, self._goal_label(goal_type))

        protein = self._safe_float(recipe.get("protein", 0))
        fat = self._safe_float(recipe.get("fat", 0))
        fiber = self._safe_float(recipe.get("fiber", 0))
        carbs = self._safe_float(recipe.get("carbs", 0))
        calories = self._safe_float(
            recipe.get("totalCalories", recipe.get("calories", 0))
        )

        # 通用营养标签（任何用户看到都有意义）
        if protein >= 20:
            self._append_tag(tags, "高蛋白")
        if fat <= 15:
            self._append_tag(tags, "低脂")
        if fiber >= 4:
            self._append_tag(tags, "高纤维")

        # 宏量匹配标签（针对当前用户目标的精准匹配）
        if macro_targets:
            if self._target_fit_score(protein, macro_targets.get("protein", 0)) >= 85:
                self._append_tag(tags, "蛋白匹配")
            if self._target_fit_score(carbs, macro_targets.get("carbs", 0)) >= 85:
                self._append_tag(tags, "碳水平衡")
            if self._target_fit_score(fat, macro_targets.get("fat", 0)) >= 85:
                self._append_tag(tags, "脂肪适配")

        # 目标特定标签
        if goal_type == "fat_loss" and protein >= 20 and fat <= 18:
            self._append_tag(tags, "减脂友好")
        elif goal_type == "muscle_toning" and protein >= 25:
            self._append_tag(tags, "增肌友好")
        elif goal_type == "weight_maintenance" and 260 <= calories <= 620:
            self._append_tag(tags, "维持友好")
        elif goal_type == "healthy_weight_gain" and calories >= 420:
            self._append_tag(tags, "增重友好")
        elif goal_type == "blood_sugar_control" and carbs <= 35 and fiber >= 4:
            self._append_tag(tags, "控糖友好")
        elif goal_type == "lipid_control" and fat <= 16:
            self._append_tag(tags, "控脂友好")
        elif goal_type == "low_sodium" and self._is_light_cooking(recipe):
            self._append_tag(tags, "低盐烹饪")
        elif goal_type == "pregnancy_nutrition" and protein >= 18:
            self._append_tag(tags, "孕期关注")
        elif goal_type == "child_growth" and protein >= 16 and carbs >= 25:
            self._append_tag(tags, "成长支持")
        elif goal_type == "senior_wellness" and self._is_easy_to_digest(recipe):
            self._append_tag(tags, "易消化")

        # 慢病标签（慢性病用户专属）
        if chronic_diseases:
            chronic_text = self._normalize_text(chronic_diseases)
            if (
                self._contains_any(chronic_text, ["diabetes", "糖尿病", "血糖", "控糖"])
                and carbs <= 35
            ):
                self._append_tag(tags, "控糖友好")
            if (
                self._contains_any(chronic_text, ["hyperlipidemia", "高血脂", "血脂", "高脂血症", "lipid"])
                and fat <= 16
            ):
                self._append_tag(tags, "控脂友好")
            if (
                self._contains_any(chronic_text, ["hypertension", "高血压", "血压", "控压"])
                and self._is_light_cooking(recipe)
            ):
                self._append_tag(tags, "清淡烹饪")

        # 份量标签
        if serving_factor <= 0.9:
            self._append_tag(tags, "小份控制")
        elif serving_factor >= 1.1:
            self._append_tag(tags, "能量补充")

        return [tag for tag in tags if tag]

    # =========================================================================
    # 【H】份量个性化调整
    # =========================================================================

    def _personalize_serving(self, recipe, meal_target_calories, macro_targets, goal_type):
        """
        份量个性化调整的主入口。

        步骤：
          1. 解析标准份量 → 赋予 standardServings 字段
          2. 从食材汇总重算营养值
          3. 计算份量因子（serving factor）
          4. 按因子缩放所有营养指标和食材用量
          5. 生成标准 vs 推荐份量的对比数据

        输出字段：
          standardServings      : 原始标准份量
          recommendedServings   : 个性化推荐份量
          servingFactor         : 缩放因子
          standardNutrition     : 标准份量下的营养值快照
          recommendedNutrition  : 推荐份量下的营养值快照
          servingNote           : 份量调整说明文本
        """
        base_recipe = deepcopy(recipe)  # 深复制，不修改原始数据
        standard_servings = self._resolve_standard_servings(base_recipe)
        base_recipe["standardServings"] = round(standard_servings, 2)
        base_recipe = self._recalculate_recipe_nutrition(base_recipe)

        serving_factor = self._resolve_serving_factor(
            base_recipe, meal_target_calories, macro_targets, goal_type
        )
        personalized = self._apply_serving_scale_to_recipe(base_recipe, serving_factor)

        # 填充份量相关字段
        personalized["standardServings"] = round(standard_servings, 2)
        personalized["recommendedServings"] = round(
            standard_servings * serving_factor, 2
        )
        personalized["servingFactor"] = round(serving_factor, 2)
        personalized["standardNutrition"] = self._extract_key_nutrition(base_recipe)
        personalized["recommendedNutrition"] = self._extract_key_nutrition(personalized)

        # 生成份量调整说明
        if serving_factor <= 0.95:
            personalized["servingNote"] = (
                f"标准 {standard_servings:.2f} 份，建议约 {personalized['recommendedServings']:.2f} 份，"
                "以贴近该餐目标"
            )
        elif serving_factor >= 1.05:
            personalized["servingNote"] = (
                f"标准 {standard_servings:.2f} 份，建议约 {personalized['recommendedServings']:.2f} 份，"
                "以补足该餐目标"
            )
        else:
            personalized["servingNote"] = (
                f"标准 {standard_servings:.2f} 份，建议约 {personalized['recommendedServings']:.2f} 份，"
                "当前与该餐目标基本一致"
            )

        return personalized

    def _resolve_serving_factor(self, recipe, meal_target_calories, macro_targets, goal_type):
        """
        计算份量调整因子。

        公式：0.6 × energy_factor + 0.4 × macro_factor

        energy_factor = 目标热量 / 食谱热量
        macro_factor  = mean(蛋白比, 碳水比, 脂肪比)

        两层约束：
          1. 目标类型约束（_goal_serving_bounds）
          2. 全局安全范围 [0.6, 1.5]

        为什么60:40？
          能量因子反应的是"吃多少够"，是主因素。
          宏量因子反应的是"营养素够不够"，是辅助微调。
          60:40 的配比在实验中表现最优（能量是主要目标）。
        """
        calories = self._safe_float(
            recipe.get("totalCalories", recipe.get("calories", 0))
        )
        energy_factor = None
        if calories > 0 and meal_target_calories > 0:
            energy_factor = meal_target_calories / calories

        macro_factors = []
        for macro_key, recipe_key in (
            ("protein", "protein"),
            ("carbs", "carbs"),
            ("fat", "fat")
        ):
            target_value = self._safe_float((macro_targets or {}).get(macro_key, 0))
            actual_value = self._safe_float(recipe.get(recipe_key, 0))
            if target_value > 0 and actual_value > 0:
                macro_factors.append(target_value / actual_value)

        macro_factor = (
            sum(macro_factors) / len(macro_factors) if macro_factors else None
        )

        # 加权融合
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
        return self._clamp(factor, 0.6, 1.5)

    def _goal_serving_bounds(self, goal_type):
        """
        10种饮食目标的份量调整上下界。

        份量调节的核心原则：
          - 减肥 → 只能减量（≤1.0）
          - 增重/增肌 → 鼓励加量（≥1.0）
          - 控制类（控糖/控脂/控压）→ 偏保守
          - 特殊人群（孕期/儿童）→ 保证下限
        """
        mapping = {
            "fat_loss": (0.6, 1.0),
            "muscle_toning": (0.9, 1.45),
            "weight_maintenance": (0.85, 1.2),
            "healthy_weight_gain": (1.0, 1.5),
            "blood_sugar_control": (0.75, 1.1),
            "lipid_control": (0.75, 1.1),
            "low_sodium": (0.8, 1.2),
            "pregnancy_nutrition": (0.9, 1.35),
            "child_growth": (0.9, 1.4),
            "senior_wellness": (0.75, 1.2)
        }
        return mapping.get(goal_type, (0.75, 1.35))

    # ── 份量相关辅助方法 ──

    def _resolve_standard_servings(self, recipe):
        """从多个可能的字段名中解析标准份量数。优先级：standardServings > servings > servingSize。"""
        for key in ("standardServings", "servings", "servingSize", "portionCount", "portion"):
            value = self._safe_float(recipe.get(key))
            if value > 0:
                return self._clamp(value, 0.5, 6.0)
        return 1.0  # 默认 1 份

    def _extract_key_nutrition(self, recipe):
        """提取关键营养指标的当前值快照，用于标准 vs 推荐份量对比。"""
        calories = self._safe_float(
            recipe.get("totalCalories", recipe.get("calories", 0))
        )
        return {
            "calories": round(calories, 0),
            "protein": round(self._safe_float(recipe.get("protein", 0)), 1),
            "carbs": round(self._safe_float(recipe.get("carbs", 0)), 1),
            "fat": round(self._safe_float(recipe.get("fat", 0)), 1),
            "fiber": round(self._safe_float(recipe.get("fiber", 0)), 1),
            "sugar": round(self._safe_float(recipe.get("sugar", 0)), 1),
            "sodium": round(self._safe_float(recipe.get("sodium", 0)), 0),
            "gi": round(self._safe_float(recipe.get("gi", recipe.get("giValue", 0))), 0)
        }

    def _apply_serving_scale_to_recipe(self, recipe, serving_factor):
        """
        将食谱的所有营养成分按份量因子等比缩放。

        缩放的字段（数值型）：
          totalCalories, calories, protein, carbs, fat,
          fiber, sugar, sodium

        缩放的子对象：
          ingredients 列表中的每个食材（用量 + 各项营养）

        食材缩放时会同时保留 standardQuantity（原始量，如"100g"）
        和 recommendedQuantity（调整后量，如"80g"），方便前端对比展示。
        """
        scaled = deepcopy(recipe)
        # 直接缩放顶层营养字段
        numeric_digits = {
            "totalCalories": 0,
            "calories": 0,
            "protein": 1,
            "carbs": 1,
            "fat": 1,
            "fiber": 1,
            "sugar": 1,
            "sodium": 0
        }

        for field, digits in numeric_digits.items():
            self._scale_numeric_field(scaled, field, serving_factor, digits)

        # 缩放食材列表
        ingredients = scaled.get("ingredients")
        if isinstance(ingredients, list):
            scaled["ingredients"] = self._scale_ingredients(ingredients, serving_factor)

        # 缩放后重新从食材汇总计算全食谱营养（避免缩放误差累积）
        return self._recalculate_recipe_nutrition(scaled)

    def _scale_ingredients(self, ingredients, serving_factor):
        """
        按份量因子缩放食材列表中的每一项。

        每个食材会得到两个新字段：
          standardQuantity    → "100g"（原始用量）
          recommendedQuantity → "80g"（调整后用量，当因子=0.8时）

        同时缩放食材层级的营养成分。
        """
        scaled_ingredients = []
        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                scaled_ingredients.append(ingredient)
                continue

            item = deepcopy(ingredient)
            quantity_value, quantity_unit = self._resolve_ingredient_quantity(item)
            if quantity_value is not None:
                unit = str(item.get("unit") or quantity_unit or "").strip()
                standard_value = round(quantity_value, 1)
                recommended_value = round(quantity_value * serving_factor, 1)

                # 保存标准量和推荐量，前端可对比展示
                item["standardQuantityValue"] = standard_value
                item["recommendedQuantityValue"] = recommended_value
                item["standardQuantity"] = self._format_quantity(standard_value, unit)
                item["recommendedQuantity"] = self._format_quantity(
                    recommended_value, unit
                )

            # 缩放食材层级的营养值
            has_scaled_quantity = self._scale_numeric_field(
                item, "quantityValue", serving_factor, 1
            )
            if not has_scaled_quantity and quantity_value is not None:
                item["quantityValue"] = round(quantity_value * serving_factor, 1)
                if not item.get("unit") and quantity_unit:
                    item["unit"] = quantity_unit

            self._scale_numeric_field(item, "calories", serving_factor, 1)
            self._scale_numeric_field(item, "protein", serving_factor, 1)
            self._scale_numeric_field(item, "carbs", serving_factor, 1)
            self._scale_numeric_field(item, "fat", serving_factor, 1)
            self._scale_numeric_field(item, "fiber", serving_factor, 1)
            self._scale_numeric_field(item, "sugar", serving_factor, 1)
            self._scale_numeric_field(item, "sodium", serving_factor, 0)
            scaled_ingredients.append(item)

        return scaled_ingredients

    def _resolve_ingredient_quantity(self, ingredient):
        """
        从食材对象中解析用量数值和单位。

        支持两种字段格式：
          - quantityValue + unit：直接数值（如 quantityValue=100, unit="g"）
          - quantity：混合字符串（如 "100g"、"1.5勺"），通过正则解析
        """
        quantity_value = self._safe_float(ingredient.get("quantityValue"))
        if quantity_value > 0:
            return (quantity_value, str(ingredient.get("unit") or "").strip())

        if "quantity" in ingredient:
            parsed_value, parsed_unit = self._parse_quantity(ingredient.get("quantity"))
            if parsed_value is not None:
                return (parsed_value, parsed_unit)

        return (None, "")

    def _format_quantity(self, value, unit):
        """格式化用量显示文本：整数不带小数，非整数保留一位。例：100g, 1.5勺"""
        if value is None:
            return ""
        if float(value).is_integer():
            quantity_text = str(int(round(value)))
        else:
            quantity_text = f"{value:.1f}"
        return f"{quantity_text}{unit or ''}".strip()

    def _recalculate_recipe_nutrition(self, recipe):
        """
        从食材列表汇总计算全食谱的营养值。

        为什么需要重算？
          食谱的静态营养字段（totalCalories/protein/carbs等）是固定的，
          但经过份量调整后，食材用量变了，营养值也需要跟着变。
          直接从缩放后的食材列表重新汇总，保证营养数据与实际用量一致。

        GI 值的计算：以碳水量为权重的加权平均。
          因为 GI（血糖生成指数）只对含碳水化合物的食物有意义。
          例：胡萝卜（碳水6g，GI=70）+ 鸡胸肉（碳水0g，GI无意义）
          → GI = (70×6 + 0×0) / (6+0) = 70，正确。
        """
        ingredients = recipe.get("ingredients")
        if not isinstance(ingredients, list) or not ingredients:
            return recipe

        total_calories = 0.0
        total_protein = 0.0
        total_carbs = 0.0
        total_fat = 0.0
        total_fiber = 0.0
        total_sugar = 0.0
        total_sodium = 0.0
        weighted_gi = 0.0
        gi_carb_weight = 0.0
        has_nutrition = False

        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                continue

            ingredient_calories = self._safe_float(ingredient.get("calories"))
            ingredient_protein = self._safe_float(ingredient.get("protein"))
            ingredient_carbs = self._safe_float(ingredient.get("carbs"))
            ingredient_fat = self._safe_float(ingredient.get("fat"))
            ingredient_fiber = self._safe_float(ingredient.get("fiber"))
            ingredient_sugar = self._safe_float(ingredient.get("sugar"))
            ingredient_sodium = self._safe_float(ingredient.get("sodium"))
            ingredient_gi = self._safe_float(
                ingredient.get("gi", ingredient.get("giValue", 0))
            )

            # 只要有任意一项营养数据，就计入汇总
            if (
                ingredient_calories > 0
                or ingredient_protein > 0
                or ingredient_carbs > 0
                or ingredient_fat > 0
            ):
                has_nutrition = True
                total_calories += ingredient_calories
                total_protein += ingredient_protein
                total_carbs += ingredient_carbs
                total_fat += ingredient_fat
                total_fiber += ingredient_fiber
                total_sugar += ingredient_sugar
                total_sodium += ingredient_sodium
                # GI加权累加
                if ingredient_gi > 0 and ingredient_carbs > 0:
                    weighted_gi += ingredient_gi * ingredient_carbs
                    gi_carb_weight += ingredient_carbs

        if not has_nutrition:
            return recipe

        recipe["totalCalories"] = round(total_calories, 0)
        recipe["calories"] = round(total_calories, 0)
        recipe["protein"] = round(total_protein, 1)
        recipe["carbs"] = round(total_carbs, 1)
        recipe["fat"] = round(total_fat, 1)
        recipe["fiber"] = round(total_fiber, 1)
        recipe["sugar"] = round(total_sugar, 1)
        recipe["sodium"] = round(total_sodium, 0)
        # GI = 加权和 / 碳水权重和
        recipe["gi"] = (
            round(weighted_gi / gi_carb_weight, 0)
            if gi_carb_weight > 0
            else self._safe_float(recipe.get("gi", 0))
        )
        return recipe

    def _scale_numeric_field(self, payload, key, factor, digits=1):
        """安全缩放字典中的数值字段。字段不存在返回False，存在则原地缩放。"""
        if key not in payload:
            return False
        value = payload.get(key)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return False

        payload[key] = round(numeric * factor, digits)
        return True

    def _parse_quantity(self, quantity):
        """
        解析混合用量字符串（如 "100g"、"1.5勺"、"200ml"）。

        正则：匹配 "数值 + 可选空格 + 单位"
        返回：(数值, 单位) 或 (None, "")
        """
        text = str(quantity or "").strip()
        if not text:
            return (None, "")

        matched = re.match(r"^(-?\d+(?:\.\d+)?)\s*([^\d\s].*)?$", text)
        if not matched:
            return (None, "")

        value = self._safe_float(matched.group(1))
        if value <= 0:
            return (None, "")
        unit = (matched.group(2) or "").strip()
        return (value, unit)

    # =========================================================================
    # 【I】每日能量目标解析（四级优先级）
    # =========================================================================

    def _resolve_daily_energy_target(self, health_info, diet_goal, goal_type):
        """
        解析用户每日所需的总热量目标。

        四级优先级（前面可用就不用后面的）：
          Level 1: 用户在饮食目标中显式设置的目标热量
          Level 2: BMR × 活动系数（从健康档案中的BMR计算）
          Level 3: Mifflin-St Jeor 公式估算BMR × 活动系数
          Level 4: 硬编码默认值 1800 kcal（绝对兜底）

        设计意图：尽可能用真实数据，每一级都是前一级的安全网。
        """
        # Level 1: 显式目标
        explicit_target = self._safe_float(diet_goal.get("targetCalories"))
        if explicit_target > 0:
            return explicit_target

        # Level 2: 健康档案中的 BMR
        bmr = self._safe_float(health_info.get("bmr"))
        if bmr <= 0:
            bmr = self._estimate_bmr_mifflin(health_info)  # Level 3

        if bmr > 0:
            base_target = bmr * self._resolve_activity_multiplier(
                health_info.get("activityLevel", "")
            )
        else:
            base_target = 1800.0  # Level 4

        # 根据目标类型调整能量
        return self._apply_goal_energy_adjustment(base_target, goal_type)

    def _resolve_target_calories(self, health_info, diet_goal):
        """
        解析目标热量（对外接口，内部复用 _resolve_daily_energy_target）。
        此方法在 training 模块中被调用。
        """
        goal_type = self._normalize_text((diet_goal or {}).get("goalType", ""))
        return self._resolve_daily_energy_target(
            health_info or {}, diet_goal or {}, goal_type
        )

    def _resolve_activity_multiplier(self, activity_level):
        """
        活动水平系数。

        - 久坐/不运动 → 1.2（BMR × 1.2 = 维持体重所需热量）
        - 轻度活动     → 1.375（每周轻度运动1-3天）
        - 中度活动     → 1.55（每周中等运动3-5天）
        - 高度活动     → 1.75（每周剧烈运动6-7天）

        默认 1.2（安全保守估计，宁可低估不超估）。
        """
        activity = self._normalize_text(activity_level)
        if "high" in activity or "高" in activity:
            return 1.75
        if "moderate" in activity or "中" in activity:
            return 1.55
        if "light" in activity or "轻" in activity:
            return 1.375
        return 1.2

    def _apply_goal_energy_adjustment(self, daily_target, goal_type):
        """
        根据饮食目标调整每日总热量：

          fat_loss          → ×0.85  (制造15%热量缺口）
          healthy_weight_gain → ×1.12 (创造12%热量盈余)
          muscle_toning     → ×1.08  (轻微盈余支持肌肉合成)
          pregnancy_nutrition → +250   (额外250kcal支持胎儿发育)
          child_growth      → ×1.10  (10%额外支持生长)
          senior_wellness   → ×0.95  (老年人代谢降低，适当减少)
          其他              → 不变

        最低保底 1200 kcal（低于此值的减肥计划不健康也不可持续）。
        """
        target = self._safe_float(daily_target)
        if target <= 0:
            target = 1800.0

        if goal_type == "fat_loss":
            target *= 0.85
        elif goal_type == "healthy_weight_gain":
            target *= 1.12
        elif goal_type == "muscle_toning":
            target *= 1.08
        elif goal_type == "pregnancy_nutrition":
            target += 250
        elif goal_type == "child_growth":
            target *= 1.10
        elif goal_type == "senior_wellness":
            target *= 0.95

        return max(target, 1200.0)

    def _estimate_bmr_mifflin(self, health_info):
        """
        Mifflin-St Jeor 方程 —— 估算基础代谢率（BMR）。

        男性：BMR = 10×体重 + 6.25×身高 - 5×年龄 + 5
        女性：BMR = 10×体重 + 6.25×身高 - 5×年龄 - 161
        未知性别取中间值 -78。

        这是目前营养学领域最准确的 BMR 估算公式之一（相比 Harris-Benedict）。
        需要年龄、身高、体重三项数据齐全才计算，缺任一返回0。
        """
        age = self._safe_float(health_info.get("age"))
        height = self._safe_float(health_info.get("height"))
        weight = self._safe_float(health_info.get("weight"))
        if age <= 0 or height <= 0 or weight <= 0:
            return 0.0

        gender = self._normalize_text(health_info.get("gender", ""))
        if gender in ("male", "man", "男"):
            sex_const = 5
        elif gender in ("female", "woman", "女"):
            sex_const = -161
        else:
            sex_const = -78  # 中性估计

        bmr = 10 * weight + 6.25 * height - 5 * age + sex_const
        return max(bmr, 0.0)

    # =========================================================================
    # 【J】宏量营养素目标解析
    # =========================================================================

    def _resolve_macro_targets(
        self, daily_target_calories, meal_type, diet_goal, goal_type
    ):
        """
        解析单餐的蛋白/碳水/脂肪目标（克数）。

        优先使用用户显式设置的目标（proteinTarget/carbsTarget/fatTarget），
        按餐次比例分配。
        如果未设置显式目标 → 从比例计算（proteinRatio/carbsRatio/fatRatio）
        如果比例也未设置 → 使用默认配比（按目标类型）。

        计算公式（示例）：
          餐蛋白目标 = 餐热量 × 蛋白供能比 / 4（每克蛋白4kcal）
          餐脂肪目标 = 餐热量 × 脂肪供能比 / 9（每克脂肪9kcal）
        """
        meal_ratio = self._meal_ratio(meal_type)  # 早30% 午40% 晚30%

        # ── 路径1: 显式设置的目标克数 ──
        explicit_protein = self._safe_float(diet_goal.get("proteinTarget"))
        explicit_carbs = self._safe_float(diet_goal.get("carbsTarget"))
        explicit_fat = self._safe_float(diet_goal.get("fatTarget"))
        if explicit_protein > 0 and explicit_carbs > 0 and explicit_fat > 0:
            return {
                "protein": explicit_protein * meal_ratio,
                "carbs": explicit_carbs * meal_ratio,
                "fat": explicit_fat * meal_ratio
            }

        # ── 路径2: 从比例计算 ──
        ratios = self._extract_macro_ratios(diet_goal)
        if not ratios:
            ratios = self._default_macro_ratios(goal_type)  # ── 路径3: 默认配比

        meal_kcal = self._meal_target(daily_target_calories, meal_type)
        if meal_kcal <= 0:
            meal_kcal = 600.0

        return {
            # 蛋白供能比 ÷ 4 kcal/g = 蛋白克数
            "protein": meal_kcal * ratios["protein"] / 4.0,
            # 碳水供能比 ÷ 4 kcal/g = 碳水克数
            "carbs": meal_kcal * ratios["carbs"] / 4.0,
            # 脂肪供能比 ÷ 9 kcal/g = 脂肪克数
            "fat": meal_kcal * ratios["fat"] / 9.0
        }

    def _extract_macro_ratios(self, diet_goal):
        """
        从 diet_goal 中提取宏量营养素供能比例。

        自动检测输入格式：
          - 百分比格式（如 30/40/30）→ 除以100归一化
          - 小数格式（如 0.3/0.4/0.3）→ 直接使用

        返回 {"protein": 0.30, "carbs": 0.40, "fat": 0.30}
        """
        protein_ratio = self._safe_float(diet_goal.get("proteinRatio"))
        carbs_ratio = self._safe_float(diet_goal.get("carbsRatio"))
        fat_ratio = self._safe_float(diet_goal.get("fatRatio"))

        if protein_ratio <= 0 or carbs_ratio <= 0 or fat_ratio <= 0:
            return None

        total = protein_ratio + carbs_ratio + fat_ratio
        if total <= 0:
            return None

        # 自动检测：如果总和 > 1.5 → 很可能是百分比格式（30+40+30=100 > 1.5）
        if total > 1.5:
            protein_ratio /= 100.0
            carbs_ratio /= 100.0
            fat_ratio /= 100.0

        total = protein_ratio + carbs_ratio + fat_ratio
        if total <= 0:
            return None

        return {
            "protein": protein_ratio / total,
            "carbs": carbs_ratio / total,
            "fat": fat_ratio / total
        }

    def _default_macro_ratios(self, goal_type):
        """
        10种饮食目标的默认宏量营养素供能比例。

        设计依据：
          - 减肥：较高蛋白（30%）维持饱腹感，降低碳水（40%）
          - 增肌：高蛋白（30%）+ 较高碳水（45%）供能训练
          - 维持：均衡配比（20% 50% 30%）
          - 增重：高碳水（55%）提供能量盈余
          - 控糖：略低碳水（40%）+ 略高蛋白（25%）+ 略高脂肪（35%）
          - 控脂：维持碳水（50%）+ 低脂（25%）
          - 长者：略高蛋白（22%）防止肌肉流失
        """
        mapping = {
            "fat_loss": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
            "muscle_toning": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
            "weight_maintenance": {"protein": 0.20, "carbs": 0.50, "fat": 0.30},
            "healthy_weight_gain": {"protein": 0.20, "carbs": 0.55, "fat": 0.25},
            "blood_sugar_control": {"protein": 0.25, "carbs": 0.40, "fat": 0.35},
            "lipid_control": {"protein": 0.25, "carbs": 0.50, "fat": 0.25},
            "low_sodium": {"protein": 0.20, "carbs": 0.50, "fat": 0.30},
            "pregnancy_nutrition": {"protein": 0.20, "carbs": 0.50, "fat": 0.30},
            "child_growth": {"protein": 0.20, "carbs": 0.55, "fat": 0.25},
            "senior_wellness": {"protein": 0.22, "carbs": 0.48, "fat": 0.30}
        }
        return mapping.get(goal_type, {"protein": 0.20, "carbs": 0.50, "fat": 0.30})

    # ── 餐次分配 ──

    def _meal_target(self, total_target, meal_type):
        """从全天目标计算单餐目标热量。午餐占40%，早/晚餐各占30%。"""
        return total_target * self._meal_ratio(meal_type)

    def _meal_ratio(self, meal_type):
        """三餐热量配比：午餐为一天的主力餐，所以占40%"""
        if meal_type == "lunch":
            return 0.4
        return 0.3

    # =========================================================================
    # 【K】辅助方法
    # =========================================================================

    def _contains_allergy(self, recipe, allergies):
        """
        检查食谱是否含有用户过敏的食材。

        匹配范围：
          食谱名称 + 描述 + 所有食材名称
        匹配方式：
          子字符串包含（大小写不敏感）

        这是硬过滤——一旦命中，该食谱直接出局，不需要后续打分。
        安全第一，宁可误杀不可漏放。
        """
        if not allergies:
            return False
        text_parts = [
            self._normalize_text(recipe.get("name", "")),
            self._normalize_text(recipe.get("description", ""))
        ]
        for ingredient in recipe.get("ingredients", []):
            if isinstance(ingredient, dict):
                text_parts.append(self._normalize_text(ingredient.get("name", "")))
            else:
                text_parts.append(self._normalize_text(str(ingredient)))
        recipe_text = " ".join(text_parts)
        return any(token and token in recipe_text for token in allergies)

    def _contains_dislike(self, recipe, dislikes):
        """
        检查食谱是否含有用户忌口的食材。
        匹配逻辑和 _contains_allergy 完全一致：
          食谱名称 + 描述 + 所有食材名称
        子字符串包含（大小写不敏感）。
        同样是硬过滤——命中即出局。
        """
        if not dislikes:
            return False
        text_parts = [
            self._normalize_text(recipe.get("name", "")),
            self._normalize_text(recipe.get("description", ""))
        ]
        for ingredient in recipe.get("ingredients", []):
            if isinstance(ingredient, dict):
                text_parts.append(self._normalize_text(ingredient.get("name", "")))
            else:
                text_parts.append(self._normalize_text(str(ingredient)))
        recipe_text = " ".join(text_parts)
        return any(token and token in recipe_text for token in dislikes)

    def _infer_meal_type(self, recipe):
        """
        从食谱的名称/描述/分类/热量推断其自然属于哪一餐。

        判断逻辑：
          1. 关键词匹配（中英文）
          2. 热量范围：≤350 → 早餐，≤560 → 午餐，>560 → 晚餐

        这是 V1 的餐次归属逻辑，V2 不再使用此方法
        （V2 中每个食谱参与三餐竞争，由分数决定归属）。
        """
        text = " ".join(
            [
                self._normalize_text(recipe.get("name", "")),
                self._normalize_text(recipe.get("description", "")),
                self._normalize_text(recipe.get("category", ""))
            ]
        )
        if any(keyword in text for keyword in ("早餐", "燕麦", "粥", "鸡蛋", "牛奶", "面包")):
            return "breakfast"
        if any(keyword in text for keyword in ("午餐", "米饭", "便当", "鸡胸", "牛肉", "意面")):
            return "lunch"
        if any(keyword in text for keyword in ("晚餐", "汤", "鱼", "蒸", "炖", "蔬菜")):
            return "dinner"

        # 关键词不匹配 → 用热量推断
        calories = self._safe_float(
            recipe.get("totalCalories", recipe.get("calories", 0))
        )
        if calories <= 350:
            return "breakfast"
        if calories <= 560:
            return "lunch"
        return "dinner"

    def _is_light_cooking(self, recipe):
        """判断是否为清淡烹饪方式（蒸/煮/炖）。用于高血压/控压场景。"""
        text = " ".join(
            [
                self._normalize_text(recipe.get("name", "")),
                self._normalize_text(recipe.get("description", "")),
                self._normalize_text(recipe.get("tips", ""))
            ]
        )
        return any(keyword in text for keyword in ("蒸", "煮", "炖", "清淡"))

    def _is_easy_to_digest(self, recipe):
        """判断是否为易消化食物（粥/汤/蒸/软）。用于老年养生场景。"""
        text = " ".join(
            [
                self._normalize_text(recipe.get("name", "")),
                self._normalize_text(recipe.get("description", "")),
                self._normalize_text(recipe.get("tips", ""))
            ]
        )
        return any(keyword in text for keyword in ("粥", "汤", "蒸", "软"))

    def _split_tokens(self, text):
        """
        拆分以逗号/顿号/分号分隔的文本为 token 列表。
        用于拆分过敏食材字符串（如 "虾,蟹,贝类" → ["虾", "蟹", "贝类"]）。
        """
        normalized = (
            self._normalize_text(text)
            .replace("，", ",")
            .replace("、", ",")
            .replace("；", ",")
        )
        return [item.strip() for item in normalized.split(",") if item.strip()]

    # ── 标签映射 ──

    def _meal_label(self, meal_type):
        """餐次英文 → 中文"""
        return {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}.get(meal_type, "")

    def _goal_label(self, goal_type):
        """目标类型英文 → 中文"""
        return {
            "fat_loss": "减肥减脂",
            "muscle_toning": "增肌塑形",
            "weight_maintenance": "维持体重",
            "healthy_weight_gain": "健康增重",
            "blood_sugar_control": "控糖饮食",
            "lipid_control": "控脂降脂",
            "low_sodium": "控压低盐",
            "pregnancy_nutrition": "孕妇营养",
            "child_growth": "儿童成长",
            "senior_wellness": "老年养生"
        }.get(goal_type, "均衡饮食")

    def _append_tag(self, tags, tag):
        """向标签列表追加不重复的标签"""
        if tag and tag not in tags:
            tags.append(tag)

    def _contains_any(self, text, keywords):
        """检查文本中是否包含任意一个关键词（大小写不敏感）"""
        normalized = self._normalize_text(text)
        return any(keyword in normalized for keyword in keywords)

    # ── 基础数学/字符串工具 ──

    def _safe_float(self, value):
        """安全浮点转换，防 None/非数字"""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _clamp(self, value, minimum, maximum):
        """钳制值到 [minimum, maximum]"""
        return max(minimum, min(maximum, value))

    def _normalize_text(self, text):
        """文本归一化：转字符串 → 去首尾空白 → 全小写。用于所有关键词匹配。"""
        return str(text or "").strip().lower()
