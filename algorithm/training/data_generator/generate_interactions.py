import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from config import GeneratorConfig


def generate_interactions(
    config: GeneratorConfig,
    user_profiles: List[Dict[str, object]],
    recipes: List[Dict[str, object]],
    recipe_profiles: List[Dict[str, object]],
    recipe_ingredients: List[Dict[str, object]],
    ingredient_map: Dict[int, Dict[str, object]],
    rng: random.Random,
) -> Dict[str, List[Dict[str, object]]]:
    recipe_profile_map = {row["recipe_id"]: row for row in recipe_profiles}
    recipe_ingredient_map: Dict[int, List[Dict[str, object]]] = defaultdict(list)
    for row in recipe_ingredients:
        recipe_ingredient_map[row["recipe_id"]].append(row)

    collect_rows: List[Dict[str, object]] = []
    diet_record_rows: List[Dict[str, object]] = []
    diet_record_detail_rows: List[Dict[str, object]] = []
    recipe_collect_count: Dict[int, int] = defaultdict(int)

    collect_id = config.collect_id_start
    record_id = config.diet_record_id_start
    detail_id = config.diet_record_detail_id_start

    for user in user_profiles:
        ranked_recipes = sorted(
            recipes,
            key=lambda item: score_recipe_for_user(user, recipe_profile_map[item["id"]], rng),
            reverse=True,
        )
        collect_count = rng.randint(config.collect_min, config.collect_max)
        selected_collects = _weighted_pick(
            ranked_recipes[: max(collect_count * 3, 24)],
            collect_count,
            user,
            recipe_profile_map,
            rng,
        )
        for recipe in selected_collects:
            collect_rows.append(
                {
                    "id": collect_id,
                    "user_id": user["user_id"],
                    "recipe_id": recipe["id"],
                    "create_time": _recent_datetime(rng, 80),
                }
            )
            recipe_collect_count[recipe["id"]] += 1
            collect_id += 1

        day_count = rng.randint(config.record_days_min, config.record_days_max)
        days = sorted({_recent_date(rng, 60) for _ in range(day_count)})
        for current_day in days:
            meals = _meal_sequence(rng)
            for meal_type in meals:
                recipe = _pick_recipe_for_meal(ranked_recipes, meal_type, user, recipe_profile_map, rng)
                if recipe is None:
                    continue
                detail_rows = _record_detail_rows(
                    detail_id,
                    record_id,
                    recipe,
                    recipe_ingredient_map.get(recipe["id"], []),
                    ingredient_map,
                )
                detail_id += len(detail_rows)
                totals = _aggregate_record(detail_rows)
                diet_record_rows.append(
                    {
                        "id": record_id,
                        "user_id": user["user_id"],
                        "record_date": current_day.isoformat(),
                        "meal_type": meal_type,
                        "total_calories": round(totals["calories"], 2),
                        "total_protein": round(totals["protein"], 2),
                        "total_carbs": round(totals["carbs"], 2),
                        "total_fat": round(totals["fat"], 2),
                        "notes": f"训练造数：{recipe['name']}",
                        "is_deleted": 0,
                        "create_time": _combine_day_and_time(current_day, meal_type),
                        "update_time": _combine_day_and_time(current_day, meal_type),
                    }
                )
                diet_record_detail_rows.extend(detail_rows)
                record_id += 1

    for recipe in recipes:
        recipe["collect_count"] = recipe_collect_count.get(recipe["id"], 0)
        recipe.pop("meal_type", None)
        recipe.pop("tags", None)

    return {
        "user_recipe_collect": collect_rows,
        "diet_record": diet_record_rows,
        "diet_record_detail": diet_record_detail_rows,
    }


def score_recipe_for_user(user: Dict[str, object], recipe_profile: Dict[str, object], rng: random.Random) -> float:
    score = 0.0
    if recipe_profile["goal_type"] == user["goal_type"]:
        score += 6.0
    if recipe_profile["meal_type"] in user.get("preferred_meals", []):
        score += 1.2
    user_tags = set(user.get("recipe_tags", []))
    recipe_tags = set(recipe_profile.get("tags", []))
    score += len(user_tags & recipe_tags) * 1.4
    disliked_tokens = set(user.get("dislikes", []))
    if any(token and token in recipe_profile.get("name", "") for token in disliked_tokens):
        score -= 3.0
    score += rng.uniform(0.0, 1.0)
    return score


def _weighted_pick(
    candidates: List[Dict[str, object]],
    count: int,
    user: Dict[str, object],
    recipe_profile_map: Dict[int, Dict[str, object]],
    rng: random.Random,
) -> List[Dict[str, object]]:
    remaining = list(candidates)
    picked: List[Dict[str, object]] = []
    while remaining and len(picked) < count:
        weights = [max(0.1, score_recipe_for_user(user, recipe_profile_map[item["id"]], rng)) for item in remaining]
        choice = rng.choices(remaining, weights=weights, k=1)[0]
        picked.append(choice)
        remaining = [item for item in remaining if item["id"] != choice["id"]]
    return picked


def _pick_recipe_for_meal(
    ranked_recipes: List[Dict[str, object]],
    meal_type: str,
    user: Dict[str, object],
    recipe_profile_map: Dict[int, Dict[str, object]],
    rng: random.Random,
) -> Optional[Dict[str, object]]:
    meal_candidates = [item for item in ranked_recipes if recipe_profile_map[item["id"]]["meal_type"] == meal_type]
    if not meal_candidates:
        return None
    top_range = meal_candidates[: min(20, len(meal_candidates))]
    weights = [max(0.1, score_recipe_for_user(user, recipe_profile_map[item["id"]], rng)) for item in top_range]
    return rng.choices(top_range, weights=weights, k=1)[0]


def _record_detail_rows(
    detail_id_start: int,
    record_id: int,
    recipe: Dict[str, object],
    recipe_ingredients: List[Dict[str, object]],
    ingredient_map: Dict[int, Dict[str, object]],
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for offset, relation in enumerate(recipe_ingredients):
        ingredient = ingredient_map[relation["ingredient_id"]]
        ratio = float(relation["quantity"]) / 100.0
        rows.append(
            {
                "id": detail_id_start + offset,
                "record_id": record_id,
                "ingredient_id": ingredient["id"],
                "food_name": ingredient["name"],
                "quantity": relation["quantity"],
                "unit": relation["unit"],
                "calories": round(float(ingredient["calories_per_100g"]) * ratio, 2),
                "protein": round(float(ingredient["protein_per_100g"]) * ratio, 2),
                "carbs": round(float(ingredient["carbs_per_100g"]) * ratio, 2),
                "fat": round(float(ingredient["fat_per_100g"]) * ratio, 2),
                "recipe_id": recipe["id"],
                "is_custom": 0,
                "is_deleted": 0,
            }
        )
    return rows


def _aggregate_record(detail_rows: List[Dict[str, object]]) -> Dict[str, float]:
    totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for row in detail_rows:
        totals["calories"] += float(row["calories"])
        totals["protein"] += float(row["protein"])
        totals["carbs"] += float(row["carbs"])
        totals["fat"] += float(row["fat"])
    return totals


def _meal_sequence(rng: random.Random) -> List[str]:
    base_meals = ["breakfast", "lunch", "dinner"]
    if rng.randint(0, 1) == 1:
        return base_meals
    remove_choice = rng.choice(["breakfast", "dinner"])
    return [meal for meal in base_meals if meal != remove_choice]


def _recent_date(rng: random.Random, max_days: int) -> date:
    return date(2026, 4, 26) - timedelta(days=rng.randint(0, max_days))


def _recent_datetime(rng: random.Random, max_days: int) -> str:
    current = datetime(2026, 4, 26, 12, 0, 0) - timedelta(days=rng.randint(0, max_days), minutes=rng.randint(0, 900))
    return current.strftime("%Y-%m-%d %H:%M:%S")


def _combine_day_and_time(current_day: date, meal_type: str) -> str:
    slot = {"breakfast": "08:10:00", "lunch": "12:20:00", "dinner": "18:35:00"}.get(meal_type, "15:00:00")
    return f"{current_day.isoformat()} {slot}"
