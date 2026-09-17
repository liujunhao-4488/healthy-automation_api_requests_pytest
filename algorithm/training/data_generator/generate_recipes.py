import json
import random
from datetime import datetime, timedelta
from typing import Dict, List

from config import GeneratorConfig
from ingredient_pool import BASE_INGREDIENTS
from recipe_templates import RECIPE_TEMPLATES

GOAL_LABELS = {
    "fat_loss": "减脂",
    "muscle_toning": "增肌塑形",
    "weight_maintenance": "维持体重",
    "healthy_weight_gain": "健康增重",
    "blood_sugar_control": "控糖饮食",
    "lipid_control": "控脂饮食",
    "low_sodium": "低钠饮食",
    "pregnancy_nutrition": "孕期营养",
    "child_growth": "儿童成长",
    "senior_wellness": "老年养护",
}


def generate_ingredients(config: GeneratorConfig) -> Dict[str, object]:
    count = min(config.ingredient_count, len(BASE_INGREDIENTS))
    ingredient_rows: List[Dict[str, object]] = []
    ingredient_map: Dict[int, Dict[str, object]] = {}

    for index in range(count):
        seed = BASE_INGREDIENTS[index]
        ingredient_id = config.ingredient_id_start + index
        row = {
            "id": ingredient_id,
            "name": seed["name"],
            "category": seed["category"],
            "sub_category": seed["sub_category"],
            "calories_per_100g": seed["calories"],
            "protein_per_100g": seed["protein"],
            "carbs_per_100g": seed["carbs"],
            "fat_per_100g": seed["fat"],
            "fiber_per_100g": seed["fiber"],
            "sugar_per_100g": seed["sugar"],
            "sodium_per_100g": seed["sodium"],
            "gi_value": seed["gi"],
            "cholesterol_per_100g": seed["cholesterol"],
            "description": f"{seed['name']}，适合作为{seed['category']}类饮食训练样本。",
            "image_url": None,
            "status": 1,
            "create_time": "2026-01-01 08:00:00",
            "update_time": "2026-01-01 08:00:00",
        }
        ingredient_rows.append(row)
        ingredient_map[ingredient_id] = {**row, "tags": seed["tags"]}

    return {"ingredient": ingredient_rows, "ingredient_map": ingredient_map}


def generate_recipes(
    config: GeneratorConfig,
    ingredient_map: Dict[int, Dict[str, object]],
    rng: random.Random,
) -> Dict[str, object]:
    recipes: List[Dict[str, object]] = []
    recipe_ingredients: List[Dict[str, object]] = []
    recipe_profiles: List[Dict[str, object]] = []
    ingredient_index = _build_ingredient_index(ingredient_map)

    for index in range(config.recipe_count):
        template = RECIPE_TEMPLATES[index % len(RECIPE_TEMPLATES)]
        recipe_id = config.recipe_id_start + index
        picked = _pick_ingredients(template, ingredient_index, rng)
        ingredient_links = _build_recipe_ingredient_rows(config, recipe_id, index, picked, rng)
        nutrition = _aggregate_nutrition(ingredient_links, ingredient_map)
        name = _build_recipe_name(template, picked, rng)
        description = _build_description(template, picked, nutrition)
        instructions = json.dumps(_build_steps(picked), ensure_ascii=False)
        create_time = (datetime(2026, 1, 1) + timedelta(days=index % 120, minutes=index % 1440)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        tags = list({template["goal_type"], template["meal_type"], *[tag for item in picked for tag in item["tags"][:1]]})

        recipe_row = {
            "id": recipe_id,
            "name": name,
            "description": description,
            "category": template["category"],
            "cuisine_type": rng.choice(template["cuisine_options"]),
            "cooking_time": rng.randint(8, 35),
            "difficulty": rng.choice(template["difficulty_options"]),
            "servings": 1,
            "total_calories": round(nutrition["calories"], 2),
            "calories_per_serving": round(nutrition["calories"], 2),
            "protein": round(nutrition["protein"], 2),
            "carbs": round(nutrition["carbs"], 2),
            "fat": round(nutrition["fat"], 2),
            "fiber": round(nutrition["fiber"], 2),
            "instructions": instructions,
            "tips": _build_tips(template),
            "image_url": None,
            "creator_id": None,
            "is_custom": 0,
            "score": round(rng.uniform(4.1, 4.9), 1),
            "score_count": rng.randint(8, 80),
            "view_count": rng.randint(20, 320),
            "collect_count": 0,
            "suitable_for": _build_suitable_for(template["goal_type"]),
            "goal_type": template["goal_type"],
            "status": 1,
            "create_time": create_time,
            "update_time": create_time,
            "meal_type": template["meal_type"],
            "tags": json.dumps(tags, ensure_ascii=False),
        }
        recipes.append(recipe_row)
        recipe_ingredients.extend(ingredient_links)
        recipe_profiles.append(
            {
                "recipe_id": recipe_id,
                "goal_type": template["goal_type"],
                "meal_type": template["meal_type"],
                "tags": tags,
                "ingredient_ids": [item["ingredient_id"] for item in ingredient_links],
                "name": name,
            }
        )

    return {
        "recipe": recipes,
        "recipe_ingredient": recipe_ingredients,
        "recipe_profiles": recipe_profiles,
    }


def _build_ingredient_index(ingredient_map: Dict[int, Dict[str, object]]) -> Dict[str, List[Dict[str, object]]]:
    index: Dict[str, List[Dict[str, object]]] = {}
    for item in ingredient_map.values():
        tags = item.get("tags", [])
        if isinstance(tags, str):
            tags = json.loads(tags)
        for tag in tags:
            index.setdefault(tag, []).append(item)
    return index


def _pick_ingredients(
    template: Dict[str, object],
    index: Dict[str, List[Dict[str, object]]],
    rng: random.Random,
) -> List[Dict[str, object]]:
    picked: List[Dict[str, object]] = []
    seen_ids = set()
    for tag_group in template["required_tags"]:
        candidates: List[Dict[str, object]] = []
        for tag in tag_group:
            candidates.extend(index.get(tag, []))
        candidates = [item for item in candidates if item["id"] not in seen_ids]
        if not candidates:
            continue
        choice = rng.choice(candidates)
        picked.append(choice)
        seen_ids.add(choice["id"])

    for tag_group in template.get("optional_tags", []):
        if rng.random() > 0.55:
            continue
        candidates = []
        for tag in tag_group:
            candidates.extend(index.get(tag, []))
        candidates = [item for item in candidates if item["id"] not in seen_ids]
        if not candidates:
            continue
        choice = rng.choice(candidates)
        picked.append(choice)
        seen_ids.add(choice["id"])

    return picked[:6]


def _build_recipe_ingredient_rows(
    config: GeneratorConfig,
    recipe_id: int,
    recipe_index: int,
    ingredients: List[Dict[str, object]],
    rng: random.Random,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for offset, ingredient in enumerate(ingredients):
        quantity = _quantity_for_category(str(ingredient["category"]), rng)
        rows.append(
            {
                "id": config.recipe_ingredient_id_start + recipe_index * 10 + offset,
                "recipe_id": recipe_id,
                "ingredient_id": ingredient["id"],
                "quantity": quantity,
                "unit": "g",
                "is_optional": 0 if offset < 3 else (1 if rng.random() < 0.2 else 0),
                "notes": None,
            }
        )
    return rows


def _aggregate_nutrition(
    ingredient_links: List[Dict[str, object]],
    ingredient_map: Dict[int, Dict[str, object]],
) -> Dict[str, float]:
    nutrition = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "fiber": 0.0}
    for item in ingredient_links:
        ingredient = ingredient_map[item["ingredient_id"]]
        ratio = float(item["quantity"]) / 100.0
        nutrition["calories"] += float(ingredient["calories_per_100g"]) * ratio
        nutrition["protein"] += float(ingredient["protein_per_100g"]) * ratio
        nutrition["carbs"] += float(ingredient["carbs_per_100g"]) * ratio
        nutrition["fat"] += float(ingredient["fat_per_100g"]) * ratio
        nutrition["fiber"] += float(ingredient["fiber_per_100g"]) * ratio
    return nutrition


def _quantity_for_category(category: str, rng: random.Random) -> int:
    if category == "主食":
        return rng.randint(60, 140)
    if category in {"肉类", "蛋类", "豆制品", "乳制品"}:
        return rng.randint(50, 160)
    if category == "坚果":
        return rng.randint(10, 25)
    if category == "调味":
        return rng.randint(2, 12)
    return rng.randint(40, 120)


def _build_recipe_name(template: Dict[str, object], ingredients: List[Dict[str, object]], rng: random.Random) -> str:
    names = [str(item["name"]) for item in ingredients]
    slots = {
        "main": names[0] if names else "时令食材",
        "grain": names[1] if len(names) > 1 else names[0] if names else "杂粮",
        "veg": names[2] if len(names) > 2 else "蔬菜",
        "fruit": names[3] if len(names) > 3 else "水果",
    }
    return rng.choice(template["name_patterns"]).format(**slots)


def _build_description(template: Dict[str, object], ingredients: List[Dict[str, object]], nutrition: Dict[str, float]) -> str:
    ingredient_names = "、".join(str(item["name"]) for item in ingredients[:4])
    goal_label = GOAL_LABELS.get(str(template["goal_type"]), "均衡饮食")
    return (
        f"围绕 {goal_label} 目标设计，采用 {ingredient_names} 组合，"
        f"单份约 {round(nutrition['calories'])} kcal，适合作为{template['category']}训练样本。"
    )


def _build_steps(ingredients: List[Dict[str, object]]) -> List[str]:
    names = "、".join(str(item["name"]) for item in ingredients[:4])
    return [
        f"将 {names} 按配方份量清洗并准备好。",
        "先处理主食和蛋白质食材至熟。",
        "再加入蔬菜类食材翻拌或焯熟后组合装盘。",
        "按口味加入少量调味，完成出品。",
    ]


def _build_tips(template: Dict[str, object]) -> str:
    goal_type = template["goal_type"]
    if goal_type == "blood_sugar_control":
        return "优先选择低 GI 主食，避免额外加糖。"
    if goal_type == "low_sodium":
        return "调味尽量清淡，控制盐和酱油用量。"
    if goal_type == "muscle_toning":
        return "训练前后食用时可适度增加蛋白质食材份量。"
    return "食材份量可根据个人能量目标做微调。"


def _build_suitable_for(goal_type: str) -> str:
    mapping = {
        "fat_loss": "减脂人群",
        "muscle_toning": "增肌人群",
        "weight_maintenance": "均衡维持人群",
        "healthy_weight_gain": "健康增重人群",
        "blood_sugar_control": "控糖人群",
        "lipid_control": "控脂人群",
        "low_sodium": "低盐饮食人群",
        "senior_wellness": "老年养生人群",
    }
    return mapping.get(goal_type, "通用人群")
