import math
from copy import deepcopy


class RecommendEngine:
    def __init__(self):
        self.user_profiles = self._load_user_profiles()
        self.user_recipe_data = self._load_user_recipe_data()

    def _load_user_profiles(self):
        return {
            101: {
                "goalType": "fat_loss",
                "activityLevel": "light",
                "age": 25,
                "gender": "female",
                "bmi": 24.0,
                "chronicDiseases": "",
                "allergies": ""
            },
            102: {
                "goalType": "muscle_toning",
                "activityLevel": "moderate",
                "age": 27,
                "gender": "male",
                "bmi": 23.0,
                "chronicDiseases": "",
                "allergies": ""
            },
            103: {
                "goalType": "blood_sugar_control",
                "activityLevel": "light",
                "age": 46,
                "gender": "female",
                "bmi": 26.0,
                "chronicDiseases": "diabetes",
                "allergies": ""
            },
            104: {
                "goalType": "low_sodium",
                "activityLevel": "light",
                "age": 58,
                "gender": "male",
                "bmi": 25.0,
                "chronicDiseases": "hypertension",
                "allergies": ""
            },
            105: {
                "goalType": "lipid_control",
                "activityLevel": "moderate",
                "age": 42,
                "gender": "male",
                "bmi": 27.0,
                "chronicDiseases": "hyperlipidemia",
                "allergies": ""
            },
            106: {
                "goalType": "weight_maintenance",
                "activityLevel": "moderate",
                "age": 30,
                "gender": "female",
                "bmi": 21.0,
                "chronicDiseases": "",
                "allergies": "shrimp"
            },
            107: {
                "goalType": "pregnancy_nutrition",
                "activityLevel": "light",
                "age": 29,
                "gender": "female",
                "bmi": 22.0,
                "chronicDiseases": "",
                "allergies": ""
            },
            108: {
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
        candidate_recipes = candidate_recipes or []
        grouped = {"breakfast": [], "lunch": [], "dinner": []}
        if not candidate_recipes:
            return grouped

        user_profile = self._build_user_profile(health_info or {}, diet_goal or {})
        similar_users = self._find_similar_users(user_profile)
        target_calories = self._resolve_target_calories(health_info or {}, diet_goal or {})
        goal_type = (diet_goal or {}).get("goalType", "")
        allergies = self._split_tokens((health_info or {}).get("allergies", ""))
        chronic_diseases = self._normalize_text((health_info or {}).get("chronicDiseases", ""))

        for meal_type, limit in (("breakfast", breakfast_count), ("lunch", lunch_count), ("dinner", dinner_count)):
            meal_candidates = []
            for recipe in candidate_recipes:
                inferred_meal_type = recipe.get("mealType") or self._infer_meal_type(recipe)
                if inferred_meal_type != meal_type:
                    continue

                if self._contains_allergy(recipe, allergies):
                    continue

                collaborative_score = self._calculate_collaborative_score(recipe.get("id"), similar_users)
                health_score = self._calculate_health_score(
                    recipe,
                    meal_type,
                    target_calories,
                    goal_type,
                    chronic_diseases
                )
                final_score = collaborative_score * 0.6 + health_score * 0.4

                enriched_recipe = deepcopy(recipe)
                enriched_recipe["mealType"] = meal_type
                enriched_recipe["collaborativeScore"] = round(collaborative_score, 2)
                enriched_recipe["healthScore"] = round(health_score, 2)
                enriched_recipe["matchScore"] = round(final_score * 20, 0)
                enriched_recipe["recommendationReason"] = self._build_reason(
                    meal_type,
                    goal_type,
                    collaborative_score,
                    health_score,
                    recipe,
                    target_calories
                )
                enriched_recipe["tags"] = self._build_tags(recipe, goal_type, meal_type, chronic_diseases)
                meal_candidates.append(enriched_recipe)

            meal_candidates.sort(
                key=lambda item: (
                    item.get("matchScore", 0),
                    item.get("collaborativeScore", 0),
                    -abs(float(item.get("totalCalories", 0) or 0) - self._meal_target(target_calories, meal_type))
                ),
                reverse=True
            )
            grouped[meal_type] = meal_candidates[:limit]

        return grouped

    def _build_user_profile(self, health_info, diet_goal):
        return {
            "goalType": diet_goal.get("goalType", ""),
            "activityLevel": health_info.get("activityLevel", ""),
            "age": float(health_info.get("age") or 30),
            "gender": health_info.get("gender", ""),
            "bmi": float(health_info.get("bmi") or 22),
            "chronicDiseases": health_info.get("chronicDiseases", ""),
            "allergies": health_info.get("allergies", "")
        }

    def _find_similar_users(self, user_profile):
        target_vector = self._profile_to_vector(user_profile)
        similarities = []
        for other_user_id, other_profile in self.user_profiles.items():
            other_vector = self._profile_to_vector(other_profile)
            similarity = self._cosine_similarity(target_vector, other_vector)
            similarities.append((other_user_id, similarity))
        similarities.sort(key=lambda item: item[1], reverse=True)
        return similarities[:4]

    def _profile_to_vector(self, profile):
        goal = self._normalize_text(profile.get("goalType", ""))
        activity = self._normalize_text(profile.get("activityLevel", ""))
        gender = self._normalize_text(profile.get("gender", ""))
        diseases = self._normalize_text(profile.get("chronicDiseases", ""))

        return [
            float(profile.get("age") or 30) / 80.0,
            float(profile.get("bmi") or 22) / 40.0,
            1.0 if gender in ("male", "男") else 0.0,
            1.0 if "fat_loss" in goal else 0.0,
            1.0 if "muscle_toning" in goal else 0.0,
            1.0 if "blood_sugar_control" in goal else 0.0,
            1.0 if "lipid_control" in goal else 0.0,
            1.0 if "low_sodium" in goal else 0.0,
            1.0 if "pregnancy_nutrition" in goal else 0.0,
            1.0 if "senior_wellness" in goal else 0.0,
            1.0 if "high" in activity or "高" in activity else 0.0,
            1.0 if "moderate" in activity or "中" in activity else 0.0,
            1.0 if "light" in activity or "轻" in activity else 0.0,
            1.0 if "diabetes" in diseases or "糖" in diseases else 0.0,
            1.0 if "hypertension" in diseases or "血压" in diseases else 0.0,
            1.0 if "hyperlipidemia" in diseases or "血脂" in diseases else 0.0
        ]

    def _cosine_similarity(self, left, right):
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def _calculate_collaborative_score(self, recipe_id, similar_users):
        weighted_sum = 0.0
        similarity_sum = 0.0
        for other_user_id, similarity in similar_users:
            rating = self._find_rating(other_user_id, recipe_id)
            if rating is None or similarity <= 0:
                continue
            weighted_sum += rating * similarity
            similarity_sum += similarity

        if similarity_sum == 0:
            return 3.2
        return weighted_sum / similarity_sum

    def _find_rating(self, user_id, recipe_id):
        for item in self.user_recipe_data:
            if item["user_id"] == user_id and item["recipe_id"] == recipe_id:
                return float(item["rating"])
        return None

    def _calculate_health_score(self, recipe, meal_type, target_calories, goal_type, chronic_diseases):
        score = 3.0
        calories = float(recipe.get("totalCalories", recipe.get("calories", 0)) or 0)
        protein = float(recipe.get("protein", 0) or 0)
        carbs = float(recipe.get("carbs", 0) or 0)
        fat = float(recipe.get("fat", 0) or 0)
        fiber = float(recipe.get("fiber", 0) or 0)

        meal_target = self._meal_target(target_calories, meal_type)
        if meal_target > 0 and calories > 0:
            diff_ratio = abs(calories - meal_target) / meal_target
            if diff_ratio <= 0.12:
                score += 1.4
            elif diff_ratio <= 0.25:
                score += 0.9
            else:
                score += 0.3

        if goal_type == "fat_loss":
            if protein >= 20:
                score += 0.8
            if fat <= 18:
                score += 0.7
        elif goal_type == "muscle_toning":
            if protein >= 25:
                score += 1.0
            if calories >= meal_target * 0.8:
                score += 0.6
        elif goal_type == "blood_sugar_control":
            if carbs <= 35:
                score += 0.9
            if fiber >= 4:
                score += 0.7
        elif goal_type == "lipid_control":
            if fat <= 16:
                score += 0.9
            if fiber >= 4:
                score += 0.6
        elif goal_type == "low_sodium":
            if self._is_light_cooking(recipe):
                score += 1.0
        elif goal_type == "senior_wellness":
            if self._is_easy_to_digest(recipe):
                score += 0.9
        elif goal_type == "pregnancy_nutrition":
            if protein >= 18:
                score += 0.7
        elif goal_type == "healthy_weight_gain":
            if calories >= meal_target * 0.9:
                score += 0.8
            if carbs >= 30:
                score += 0.5

        if ("糖" in chronic_diseases or "diabetes" in chronic_diseases) and carbs <= 35:
            score += 0.5
        if ("血压" in chronic_diseases or "hypertension" in chronic_diseases) and self._is_light_cooking(recipe):
            score += 0.4
        if ("血脂" in chronic_diseases or "hyperlipidemia" in chronic_diseases) and fat <= 16:
            score += 0.4

        return min(score, 5.0)

    def _build_reason(self, meal_type, goal_type, collaborative_score, health_score, recipe, target_calories):
        parts = [
            f"协同过滤匹配分 {collaborative_score:.1f}，来源于相似用户的食谱偏好",
            f"健康约束适配分 {health_score:.1f}，结合你的目标和健康情况进行了二次筛选"
        ]
        calories = float(recipe.get("totalCalories", recipe.get("calories", 0)) or 0)
        meal_target = self._meal_target(target_calories, meal_type)
        if calories > 0 and meal_target > 0:
            parts.append(f"该餐热量约 {round(calories)} kcal，接近建议值 {round(meal_target)} kcal")
        if goal_type:
            parts.append(f"当前更偏向“{self._goal_label(goal_type)}”目标")
        return "；".join(parts[:3])

    def _build_tags(self, recipe, goal_type, meal_type, chronic_diseases):
        tags = [self._meal_label(meal_type), self._goal_label(goal_type)]
        protein = float(recipe.get("protein", 0) or 0)
        fat = float(recipe.get("fat", 0) or 0)
        fiber = float(recipe.get("fiber", 0) or 0)
        carbs = float(recipe.get("carbs", 0) or 0)
        if protein >= 20:
            tags.append("高蛋白")
        if fat <= 15:
            tags.append("低脂")
        if fiber >= 4:
            tags.append("高纤维")
        if ("糖" in chronic_diseases or "diabetes" in chronic_diseases) and carbs <= 35:
            tags.append("控糖友好")
        return [tag for tag in tags if tag]

    def _resolve_target_calories(self, health_info, diet_goal):
        target = diet_goal.get("targetCalories")
        if target:
            return float(target)
        bmr = float(health_info.get("bmr") or 0)
        if bmr <= 0:
            return 1800.0
        activity = self._normalize_text(health_info.get("activityLevel", ""))
        if "high" in activity or "高" in activity:
            return bmr * 1.75
        if "moderate" in activity or "中" in activity:
            return bmr * 1.55
        if "light" in activity or "轻" in activity:
            return bmr * 1.375
        return bmr * 1.2

    def _meal_target(self, total_target, meal_type):
        if meal_type == "lunch":
            return total_target * 0.4
        return total_target * 0.3

    def _contains_allergy(self, recipe, allergies):
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

    def _infer_meal_type(self, recipe):
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
        calories = float(recipe.get("totalCalories", recipe.get("calories", 0)) or 0)
        if calories <= 350:
            return "breakfast"
        if calories <= 560:
            return "lunch"
        return "dinner"

    def _is_light_cooking(self, recipe):
        text = " ".join(
            [
                self._normalize_text(recipe.get("name", "")),
                self._normalize_text(recipe.get("description", "")),
                self._normalize_text(recipe.get("tips", ""))
            ]
        )
        return any(keyword in text for keyword in ("蒸", "煮", "炖", "清淡"))

    def _is_easy_to_digest(self, recipe):
        text = " ".join(
            [
                self._normalize_text(recipe.get("name", "")),
                self._normalize_text(recipe.get("description", "")),
                self._normalize_text(recipe.get("tips", ""))
            ]
        )
        return any(keyword in text for keyword in ("粥", "汤", "蒸", "软"))

    def _split_tokens(self, text):
        normalized = self._normalize_text(text).replace("，", ",").replace("、", ",").replace("；", ",")
        return [item.strip() for item in normalized.split(",") if item.strip()]

    def _meal_label(self, meal_type):
        return {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}.get(meal_type, "")

    def _goal_label(self, goal_type):
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

    def _normalize_text(self, text):
        return str(text or "").strip().lower()
