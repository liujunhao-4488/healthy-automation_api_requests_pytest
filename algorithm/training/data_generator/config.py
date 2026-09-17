from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class GeneratorConfig:
    random_seed: int = 20260426
    user_count: int = 180
    ingredient_count: int = 84
    recipe_count: int = 180
    article_count: int = 48
    collect_min: int = 8
    collect_max: int = 18
    record_days_min: int = 14
    record_days_max: int = 32
    record_meals_min: int = 2
    record_meals_max: int = 3
    read_history_min: int = 4
    read_history_max: int = 12
    output_mode: str = "sql"
    output_sql_path: Path = Path("D:/biyesheji/database/generated_training_data.sql")
    insert_batch_size: int = 200
    user_id_start: int = 100001
    health_info_id_start: int = 200001
    preference_id_start: int = 300001
    goal_id_start: int = 400001
    ingredient_id_start: int = 500001
    recipe_id_start: int = 600001
    recipe_ingredient_id_start: int = 700001
    collect_id_start: int = 800001
    diet_record_id_start: int = 900001
    diet_record_detail_id_start: int = 1000001
    article_id_start: int = 1100001
    read_record_id_start: int = 1200001
    default_password_hash: str = (
        "$2a$10$rs0vAkSKgVKMWWWSYojuje4dho5mfroXlf9HhF.93/MFFPqXSGvt2"
    )
    mysql_config: Dict[str, object] = field(
        default_factory=lambda: {
            "host": "127.0.0.1",
            "port": 3306,
            "user": "root",
            "password": "123456",
            "database": "health_diet",
            "charset": "utf8mb4",
        }
    )
    user_group_distribution: Dict[str, float] = field(
        default_factory=lambda: {
            "fat_loss": 0.28,
            "muscle_toning": 0.18,
            "weight_maintenance": 0.18,
            "healthy_weight_gain": 0.08,
            "blood_sugar_control": 0.10,
            "lipid_control": 0.08,
            "low_sodium": 0.06,
            "senior_wellness": 0.04,
        }
    )


CONFIG = GeneratorConfig()
