import random
from pathlib import Path

from config import CONFIG
from generate_interactions import generate_interactions
from generate_recipes import generate_ingredients, generate_recipes
from generate_users import generate_users
from sql_writer import write_sql_file


def main() -> None:
    rng = random.Random(CONFIG.random_seed)

    user_bundle = generate_users(CONFIG, rng)
    ingredient_bundle = generate_ingredients(CONFIG)
    recipe_bundle = generate_recipes(CONFIG, ingredient_bundle["ingredient_map"], rng)
    interaction_bundle = generate_interactions(
        CONFIG,
        user_bundle["user_profiles"],
        recipe_bundle["recipe"],
        recipe_bundle["recipe_profiles"],
        recipe_bundle["recipe_ingredient"],
        ingredient_bundle["ingredient_map"],
        rng,
    )

    rows_by_table = {
        "user": user_bundle["user"],
        "health_info": user_bundle["health_info"],
        "user_diet_preference": user_bundle["user_diet_preference"],
        "diet_goal": user_bundle["diet_goal"],
        "ingredient": ingredient_bundle["ingredient"],
        "recipe": recipe_bundle["recipe"],
        "recipe_ingredient": recipe_bundle["recipe_ingredient"],
        "user_recipe_collect": interaction_bundle["user_recipe_collect"],
        "diet_record": interaction_bundle["diet_record"],
        "diet_record_detail": interaction_bundle["diet_record_detail"],
    }

    output_path = write_sql_file(
        rows_by_table,
        Path(CONFIG.output_sql_path),
        batch_size=CONFIG.insert_batch_size,
    )
    print(f"Generated SQL: {output_path}")
    for table_name, rows in rows_by_table.items():
        print(f"{table_name}: {len(rows)}")


if __name__ == "__main__":
    main()
