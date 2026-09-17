import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from config import GeneratorConfig
from profiles import USER_PROFILES


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    height_m = max(height_cm / 100.0, 0.01)
    return round(weight_kg / (height_m * height_m), 2)


def calculate_bmr(gender: str, age: int, height_cm: float, weight_kg: float) -> int:
    if gender == "female":
        value = 447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.33 * age
    else:
        value = 88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age
    return int(round(value))


def _weighted_profile_keys(config: GeneratorConfig) -> List[str]:
    keys: List[str] = []
    for profile_key, weight in config.user_group_distribution.items():
        keys.extend([profile_key] * max(1, int(weight * 100)))
    return keys


def _random_goal_dates(rng: random.Random) -> Tuple[str, str]:
    start_date = datetime(2026, 1, 1) + timedelta(days=rng.randint(0, 100))
    end_date = start_date + timedelta(days=rng.randint(60, 180))
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def _macro_targets(target_calories: float, ratios: Tuple[float, float, float]) -> Tuple[float, float, float]:
    protein_ratio, carbs_ratio, fat_ratio = ratios
    protein_target = round(target_calories * protein_ratio / 4.0, 1)
    carbs_target = round(target_calories * carbs_ratio / 4.0, 1)
    fat_target = round(target_calories * fat_ratio / 9.0, 1)
    return protein_target, carbs_target, fat_target


def generate_users(config: GeneratorConfig, rng: random.Random) -> Dict[str, List[Dict[str, object]]]:
    profile_keys = _weighted_profile_keys(config)
    rows = {
        "user": [],
        "health_info": [],
        "user_diet_preference": [],
        "diet_goal": [],
        "user_profiles": [],
    }

    for index in range(config.user_count):
        profile_key = rng.choice(profile_keys)
        profile = USER_PROFILES[profile_key]
        user_id = config.user_id_start + index
        gender = "female" if rng.random() < 0.55 else "male"
        age = rng.randint(*profile["age_range"])
        height = round(rng.uniform(*profile["height_range"]), 1)
        weight = round(rng.uniform(*profile["weight_range"]), 1)
        bmi = calculate_bmi(height, weight)
        bmr = calculate_bmr(gender, age, height, weight)
        activity_level = rng.choice(profile["activity_levels"])
        exercise_duration = rng.randint(*profile["exercise_duration_range"])
        exercise_type = ",".join(rng.sample(profile["exercise_types"], k=min(2, len(profile["exercise_types"]))))
        chronic_diseases = rng.choice(profile["chronic_diseases"])
        target_calories = round(rng.uniform(*profile["target_calories_range"]), 1)
        protein_ratio, carbs_ratio, fat_ratio = profile["macro_ratio"]
        protein_target, carbs_target, fat_target = _macro_targets(target_calories, profile["macro_ratio"])
        water_target = rng.choice([1600, 1800, 2000, 2200, 2400, 2600])
        meal_frequency = rng.randint(*profile["meal_frequency_range"])
        snack_preference = rng.choice(profile["snack_preference"])
        favorites = "、".join(rng.sample(profile["favorites"], k=min(3, len(profile["favorites"]))))
        dislikes = "、".join(rng.sample(profile["dislikes"], k=min(2, len(profile["dislikes"]))))
        allergies = rng.choice(profile["allergies"])
        start_date, end_date = _random_goal_dates(rng)
        goal_type = profile["goal_type"]
        username = f"{goal_type}_user_{index + 1:03d}"
        email = f"{username}@example.com"
        phone = f"13{rng.randint(100000000, 999999999)}"
        create_time = (
            datetime(2026, 1, 1) + timedelta(days=rng.randint(0, 100), minutes=rng.randint(0, 1440))
        ).strftime("%Y-%m-%d %H:%M:%S")

        rows["user"].append(
            {
                "id": user_id,
                "username": username,
                "password": config.default_password_hash,
                "email": email,
                "phone": phone,
                "avatar": None,
                "role": "user",
                "status": 1,
                "create_time": create_time,
                "update_time": create_time,
            }
        )
        rows["health_info"].append(
            {
                "id": config.health_info_id_start + index,
                "user_id": user_id,
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight,
                "bmi": bmi,
                "bmr": bmr,
                "blood_pressure": _blood_pressure_for_profile(goal_type, rng),
                "blood_sugar": _blood_sugar_for_profile(goal_type, rng),
                "activity_level": activity_level,
                "exercise_duration": exercise_duration,
                "exercise_type": exercise_type,
                "chronic_diseases": chronic_diseases,
                "create_time": create_time,
                "update_time": create_time,
            }
        )
        rows["user_diet_preference"].append(
            {
                "id": config.preference_id_start + index,
                "user_id": user_id,
                "diet_type": profile["diet_type"],
                "allergies": allergies,
                "dislikes": dislikes,
                "favorites": favorites,
                "meal_frequency": meal_frequency,
                "snack_preference": snack_preference,
                "create_time": create_time,
                "update_time": create_time,
            }
        )
        rows["diet_goal"].append(
            {
                "id": config.goal_id_start + index,
                "user_id": user_id,
                "goal_type": goal_type,
                "target_weight": round(weight + _target_weight_delta(goal_type, rng), 1),
                "target_calories": target_calories,
                "protein_ratio": protein_ratio,
                "carbs_ratio": carbs_ratio,
                "fat_ratio": fat_ratio,
                "protein_target": protein_target,
                "carbs_target": carbs_target,
                "fat_target": fat_target,
                "water_target": water_target,
                "status": 1,
                "start_date": start_date,
                "end_date": end_date,
                "reminder_enabled": 1 if rng.random() < 0.72 else 0,
                "reminder_time": rng.choice(["07:30:00", "08:00:00", "12:00:00", "18:30:00"]),
                "create_time": create_time,
                "update_time": create_time,
            }
        )
        rows["user_profiles"].append(
            {
                "user_id": user_id,
                "profile_key": profile_key,
                "goal_type": goal_type,
                "favorites": profile["favorites"],
                "dislikes": profile["dislikes"],
                "recipe_tags": profile["recipe_tags"],
                "article_tags": profile["article_tags"],
                "preferred_meals": profile["preferred_meals"],
                "chronic_diseases": chronic_diseases,
                "target_calories": target_calories,
            }
        )

    return rows


def _target_weight_delta(goal_type: str, rng: random.Random) -> float:
    if goal_type == "fat_loss":
        return -rng.uniform(3.0, 10.0)
    if goal_type == "healthy_weight_gain":
        return rng.uniform(2.0, 8.0)
    if goal_type == "muscle_toning":
        return rng.uniform(1.0, 5.0)
    return rng.uniform(-2.0, 2.0)


def _blood_pressure_for_profile(goal_type: str, rng: random.Random) -> str:
    if goal_type == "low_sodium":
        systolic = rng.randint(132, 148)
        diastolic = rng.randint(82, 96)
    elif goal_type == "senior_wellness":
        systolic = rng.randint(124, 146)
        diastolic = rng.randint(76, 92)
    else:
        systolic = rng.randint(108, 132)
        diastolic = rng.randint(68, 86)
    return f"{systolic}/{diastolic}"


def _blood_sugar_for_profile(goal_type: str, rng: random.Random) -> float:
    if goal_type == "blood_sugar_control":
        return round(rng.uniform(6.2, 9.4), 1)
    if goal_type == "senior_wellness":
        return round(rng.uniform(5.1, 7.1), 1)
    return round(rng.uniform(4.4, 6.1), 1)
