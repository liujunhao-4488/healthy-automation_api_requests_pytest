# -*- coding: utf-8 -*-
"""
混合推荐权重敏感性分析脚本 —— 为论文权重选择提供量化依据
======================================================================
用途：
  对多组 (w_cf, w_nut, w_guard) 权重配置进行对比实验，
  验证当前方案 (0.45/0.35/0.20) 是否为最优折衷。

实验设计：
  ┌──────────────────────────────────────────────────────────┐
  │ 6组权重方案，代表不同的推荐策略倾向：                       │
  │                                                          │
  │ W1: CF主导型    (0.55/0.25/0.20) — 协同过滤权重最高       │
  │ W2: 营养主导型  (0.25/0.55/0.20) — ML营养模型权重最高     │
  │ W3: 护栏增强型  (0.25/0.35/0.40) — 规则护栏权重最高       │
  │ W4: 均衡型      (0.33/0.34/0.33) — 三个分量等权重         │
  │ W5: 当前方案    (0.45/0.35/0.20) — ★生产环境使用          │
  │ W6: 高护栏兜底  (0.35/0.45/0.20) — ML营养权重稍高于CF     │
  └──────────────────────────────────────────────────────────┘

评估指标（7个维度）：
  ┌─────────────────────┬──────────────────────────────────┐
  │ 指标                │ 含义                               │
  ├─────────────────────┼──────────────────────────────────┤
  │ avg_match_score     │ 平均最终匹配分（越高越好）          │
  │ avg_calorie_deviation │ 平均热量偏差%（越低越好）         │
  │ avg_protein_deviation │ 平均蛋白质偏差%（越低越好）       │
  │ avg_carbs_deviation   │ 平均碳水偏差%（越低越好）         │
  │ avg_fat_deviation     │ 平均脂肪偏差%（越低越好）         │
  │ coverage_rate       │ 推荐覆盖率%（不重复食谱/总食谱，    │
  │                     │   越高说明推荐多样性越好）           │
  │ constraint_violation_rate │ 约束违规率%（越低越好）       │
  └─────────────────────┴──────────────────────────────────┘

测试数据：
  优先从数据库加载真实用户画像和食谱（≥8个用户时使用）。
  数据库不可用时，回退到内置的8个合成用户画像 + 22道合成食谱。

测试用户覆盖（8种真实/合成画像）：
  - 101: 减脂（年轻女性，轻活动）
  - 102: 增肌（年轻男性，中等活动）
  - 103: 血糖控制（中年女性，患糖尿病）
  - 104: 低钠饮食（老年男性，患高血压）
  - 105: 血脂控制（中年男性，患高血脂）
  - 106: 维持体重（年轻女性，无慢病，虾过敏）
  - 107: 孕期营养（年轻女性，无慢病）
  - 108: 老年健康（老年女性，患高血压）

用法:
  python weight_sensitivity_analysis.py

输出:
  6组权重的7项指标对比表 + 各指标最优方案 + 当前方案详细分析
"""

import math
import os
import sys
from collections import defaultdict
from copy import deepcopy

# 确保可以导入同目录下的 RecommendEngineV2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recommend_engine_v2 import RecommendEngineV2


# ═════════════════════════════════════════════════════════════
# 备选合成食谱（数据库不可用时使用）
# ═════════════════════════════════════════════════════════════
# 22道菜覆盖早(6)/午(7)/晚(9)三餐，涵盖"健康"到"高热量/高钠"的
# 全梯度食谱，确保实验能测试各推荐策略在不同质量食谱上的表现差异。
SYNTHETIC_RECIPES = [
    # ── 早餐类（6道）──
    # 从320kcal燕麦粥到280kcal蒸红薯，覆盖低GI~中GI范围
    {"id": 1, "name": "燕麦牛奶粥", "mealType": "breakfast",
     "totalCalories": 320, "protein": 12, "carbs": 48, "fat": 8,
     "fiber": 5, "sugar": 12, "sodium": 80, "gi": 55,
     "cookingTime": 10, "difficulty": "easy"},
    {"id": 2, "name": "全麦鸡蛋三明治", "mealType": "breakfast",
     "totalCalories": 380, "protein": 18, "carbs": 42, "fat": 14,
     "fiber": 4, "sugar": 6, "sodium": 420, "gi": 50,
     "cookingTime": 15, "difficulty": "easy"},
    {"id": 3, "name": "豆浆油条套餐", "mealType": "breakfast",
     "totalCalories": 450, "protein": 14, "carbs": 55, "fat": 18,
     "fiber": 2, "sugar": 8, "sodium": 350, "gi": 70,  # ← 高GI，糖尿病用户应避
     "cookingTime": 5, "difficulty": "easy"},
    {"id": 4, "name": "酸奶水果碗", "mealType": "breakfast",
     "totalCalories": 250, "protein": 10, "carbs": 38, "fat": 6,
     "fiber": 4, "sugar": 22, "sodium": 60, "gi": 45,  # ← 高糖，减脂用户应避
     "cookingTime": 5, "difficulty": "easy"},
    {"id": 5, "name": "蒸红薯+水煮蛋", "mealType": "breakfast",
     "totalCalories": 280, "protein": 10, "carbs": 45, "fat": 5,
     "fiber": 6, "sugar": 14, "sodium": 120, "gi": 48,  # ← 高纤维低脂，健康之选
     "cookingTime": 20, "difficulty": "easy"},
    {"id": 6, "name": "小米南瓜粥", "mealType": "breakfast",
     "totalCalories": 200, "protein": 5, "carbs": 40, "fat": 2,
     "fiber": 3, "sugar": 10, "sodium": 30, "gi": 52,  # ← 低热量低钠，老年人友好
     "cookingTime": 25, "difficulty": "easy"},

    # ── 午餐类（7道）──
    # 从350kcal鸡胸沙拉到750kcal红烧肉，覆盖"极健康"到"极不健康"
    {"id": 7, "name": "鸡胸肉蔬菜沙拉", "mealType": "lunch",
     "totalCalories": 350, "protein": 35, "carbs": 15, "fat": 16,
     "fiber": 5, "sugar": 6, "sodium": 380, "gi": 30,  # ← 低GI高蛋白，减脂/增肌首选
     "cookingTime": 15, "difficulty": "easy"},
    {"id": 8, "name": "清蒸鲈鱼+糙米饭", "mealType": "lunch",
     "totalCalories": 480, "protein": 32, "carbs": 50, "fat": 14,
     "fiber": 3, "sugar": 2, "sodium": 280, "gi": 50,  # ← 均衡营养，低钠低糖
     "cookingTime": 25, "difficulty": "medium"},
    {"id": 9, "name": "番茄牛腩盖饭", "mealType": "lunch",
     "totalCalories": 650, "protein": 30, "carbs": 68, "fat": 24,
     "fiber": 3, "sugar": 8, "sodium": 680, "gi": 65,  # ← 高钠中GI，高血压用户应避
     "cookingTime": 35, "difficulty": "medium"},
    {"id": 10, "name": "豆腐菌菇汤+杂粮饭", "mealType": "lunch",
     "totalCalories": 380, "protein": 18, "carbs": 52, "fat": 10,
     "fiber": 5, "sugar": 4, "sodium": 320, "gi": 48,  # ← 低脂中蛋白，素食友好
     "cookingTime": 20, "difficulty": "easy"},
    {"id": 11, "name": "虾仁西兰花意面", "mealType": "lunch",
     "totalCalories": 520, "protein": 28, "carbs": 58, "fat": 16,
     "fiber": 4, "sugar": 5, "sodium": 450, "gi": 45,  # ← 含虾！过敏用户(#106)应过滤
     "cookingTime": 20, "difficulty": "medium"},
    {"id": 12, "name": "红烧肉+米饭", "mealType": "lunch",
     "totalCalories": 750, "protein": 22, "carbs": 65, "fat": 42,
     "fiber": 1, "sugar": 8, "sodium": 850, "gi": 68,  # ← 高脂高钠高GI，三个慢病全触发
     "cookingTime": 40, "difficulty": "hard"},
    {"id": 13, "name": "清炒时蔬+鸡丝凉面", "mealType": "lunch",
     "totalCalories": 420, "protein": 24, "carbs": 48, "fat": 13,
     "fiber": 4, "sugar": 7, "sodium": 400, "gi": 42,  # ← 中热量均衡，适合日常
     "cookingTime": 15, "difficulty": "easy"},

    # ── 晚餐类（9道）──
    # 从180kcal凉拌黄瓜到680kcal麻辣香锅，全面覆盖
    {"id": 14, "name": "冬瓜排骨汤", "mealType": "dinner",
     "totalCalories": 300, "protein": 20, "carbs": 10, "fat": 18,
     "fiber": 2, "sugar": 3, "sodium": 350, "gi": 30,  # ← 低碳水低GI，血糖控制友好
     "cookingTime": 40, "difficulty": "medium"},
    {"id": 15, "name": "清蒸鱼+蒜蓉菠菜", "mealType": "dinner",
     "totalCalories": 280, "protein": 28, "carbs": 8, "fat": 14,
     "fiber": 3, "sugar": 2, "sodium": 300, "gi": 25,  # ← 极低GI高蛋白，健康首选
     "cookingTime": 20, "difficulty": "easy"},
    {"id": 16, "name": "紫薯银耳羹", "mealType": "dinner",
     "totalCalories": 220, "protein": 5, "carbs": 42, "fat": 2,
     "fiber": 5, "sugar": 16, "sodium": 40, "gi": 45,  # ← 低钠高糖，高血压可吃但减脂需慎
     "cookingTime": 30, "difficulty": "easy"},
    {"id": 17, "name": "牛肉蔬菜杂粮饭", "mealType": "dinner",
     "totalCalories": 500, "protein": 30, "carbs": 50, "fat": 16,
     "fiber": 4, "sugar": 5, "sodium": 420, "gi": 48,  # ← 均衡高蛋白，增肌友好
     "cookingTime": 30, "difficulty": "medium"},
    {"id": 18, "name": "番茄蛋花汤+蒸饺", "mealType": "dinner",
     "totalCalories": 400, "protein": 16, "carbs": 48, "fat": 15,
     "fiber": 2, "sugar": 6, "sodium": 500, "gi": 55,  # ← 钠刚好500（高血压阈值边界）
     "cookingTime": 20, "difficulty": "easy"},
    {"id": 19, "name": "凉拌黄瓜+小米粥", "mealType": "dinner",
     "totalCalories": 180, "protein": 5, "carbs": 35, "fat": 3,
     "fiber": 3, "sugar": 6, "sodium": 150, "gi": 42,  # ← 极低热量低钠，减肥/老年友好
     "cookingTime": 15, "difficulty": "easy"},
    {"id": 20, "name": "三文鱼牛油果碗", "mealType": "dinner",
     "totalCalories": 450, "protein": 26, "carbs": 30, "fat": 24,
     "fiber": 6, "sugar": 4, "sodium": 250, "gi": 35,  # ← 高纤维Omega-3，心血管友好
     "cookingTime": 15, "difficulty": "easy"},
    {"id": 21, "name": "红烧豆腐+藜麦饭", "mealType": "dinner",
     "totalCalories": 360, "protein": 18, "carbs": 44, "fat": 12,
     "fiber": 4, "sugar": 5, "sodium": 380, "gi": 48,  # ← 植物蛋白+全谷物，均衡之选
     "cookingTime": 20, "difficulty": "easy"},
    {"id": 22, "name": "麻辣香锅（含虾）", "mealType": "dinner",
     "totalCalories": 680, "protein": 32, "carbs": 45, "fat": 38,
     "fiber": 3, "sugar": 8, "sodium": 1200, "gi": 55,  # ← 超高钠(1200mg)! 高血压大忌 + 含虾
     "cookingTime": 25, "difficulty": "hard"},
]


# ═════════════════════════════════════════════════════════════
# 测试用户画像（覆盖8种饮食目标 + 慢性病组合 + 过敏案例）
# ═════════════════════════════════════════════════════════════
TEST_USERS = [
    # 用户101：减脂目标
    # 年轻女性，BMI=24（正常偏高），减脂 → 低热量+高蛋白
    {"user_id": 101,
     "health_info": {"age": 25, "gender": "female", "height": 162, "weight": 63,
                     "bmi": 24.0, "bmr": 1350, "activityLevel": "light",
                     "chronicDiseases": "", "allergies": ""},
     "diet_goal": {"goalType": "fat_loss", "targetCalories": 1500,
                   "proteinTarget": 90, "carbsTarget": 150, "fatTarget": 42,
                   "waterTarget": 2000}},

    # 用户102：增肌目标
    # 年轻男性，中等活动量，BMR=1680 → 高热量+高蛋白
    {"user_id": 102,
     "health_info": {"age": 27, "gender": "male", "height": 175, "weight": 70,
                     "bmi": 22.9, "bmr": 1680, "activityLevel": "moderate",
                     "chronicDiseases": "", "allergies": ""},
     "diet_goal": {"goalType": "muscle_toning", "targetCalories": 2400,
                   "proteinTarget": 150, "carbsTarget": 270, "fatTarget": 67,
                   "waterTarget": 2500}},

    # 用户103：血糖控制目标
    # 中年女性，患糖尿病 → 低GI + 低碳水（GI > 60应被惩罚）
    {"user_id": 103,
     "health_info": {"age": 46, "gender": "female", "height": 158, "weight": 65,
                     "bmi": 26.0, "bmr": 1280, "activityLevel": "light",
                     "chronicDiseases": "diabetes", "allergies": ""},
     "diet_goal": {"goalType": "blood_sugar_control", "targetCalories": 1600,
                   "proteinTarget": 80, "carbsTarget": 160, "fatTarget": 44,
                   "waterTarget": 2000}},

    # 用户104：低钠饮食目标
    # 老年男性，患高血压 → 低钠（>500mg应被惩罚）
    {"user_id": 104,
     "health_info": {"age": 58, "gender": "male", "height": 170, "weight": 72,
                     "bmi": 24.9, "bmr": 1550, "activityLevel": "light",
                     "chronicDiseases": "hypertension", "allergies": ""},
     "diet_goal": {"goalType": "low_sodium", "targetCalories": 1800,
                   "proteinTarget": 80, "carbsTarget": 225, "fatTarget": 50,
                   "waterTarget": 2000}},

    # 用户105：血脂控制目标
    # 中年男性，患高血脂 → 低脂（高脂食谱应被惩罚）
    {"user_id": 105,
     "health_info": {"age": 42, "gender": "male", "height": 172, "weight": 80,
                     "bmi": 27.0, "bmr": 1700, "activityLevel": "moderate",
                     "chronicDiseases": "hyperlipidemia", "allergies": ""},
     "diet_goal": {"goalType": "lipid_control", "targetCalories": 1800,
                   "proteinTarget": 90, "carbsTarget": 200, "fatTarget": 50,
                   "waterTarget": 2000}},

    # 用户106：维持体重目标
    # 年轻女性，虾过敏 → 含虾食谱(ID=11,20)应被过滤
    {"user_id": 106,
     "health_info": {"age": 30, "gender": "female", "height": 165, "weight": 57,
                     "bmi": 20.9, "bmr": 1320, "activityLevel": "moderate",
                     "chronicDiseases": "", "allergies": "shrimp"},
     "diet_goal": {"goalType": "weight_maintenance", "targetCalories": 2000,
                   "proteinTarget": 100, "carbsTarget": 250, "fatTarget": 56,
                   "waterTarget": 2000}},

    # 用户107：孕期营养目标
    # 年轻女性 → 高营养密度+均衡
    {"user_id": 107,
     "health_info": {"age": 29, "gender": "female", "height": 160, "weight": 56,
                     "bmi": 21.9, "bmr": 1280, "activityLevel": "light",
                     "chronicDiseases": "", "allergies": ""},
     "diet_goal": {"goalType": "pregnancy_nutrition", "targetCalories": 2100,
                   "proteinTarget": 105, "carbsTarget": 260, "fatTarget": 58,
                   "waterTarget": 2500}},

    # 用户108：老年健康目标
    # 老年女性，患高血压 → 低钠+易消化
    {"user_id": 108,
     "health_info": {"age": 66, "gender": "female", "height": 155, "weight": 55,
                     "bmi": 22.9, "bmr": 1120, "activityLevel": "light",
                     "chronicDiseases": "hypertension", "allergies": ""},
     "diet_goal": {"goalType": "senior_wellness", "targetCalories": 1600,
                   "proteinTarget": 70, "carbsTarget": 200, "fatTarget": 44,
                   "waterTarget": 1800}},
]


# ═════════════════════════════════════════════════════════════
# 权重配置方案（6组对比实验）
# ═════════════════════════════════════════════════════════════
# 每组配置是三维权重 (w_cf, w_nut, w_guard)，三者之和恒为1.0。
# W5 (0.45/0.35/0.20) 是当前生产环境使用的方案。
WEIGHT_CONFIGS = [
    {"id": "W1", "label": "CF主导型",
     "w_cf": 0.55, "w_nut": 0.25, "w_guard": 0.20},
    # ↑ 策略倾向：重度依赖协同过滤，"喜欢这个的人也喜欢那个"的逻辑占主导
    #   优点：个性化强，能发现用户自己也没意识到的偏好
    #   缺点：冷用户（新注册）效果差，推荐可能偏离营养目标

    {"id": "W2", "label": "营养主导型",
     "w_cf": 0.25, "w_nut": 0.55, "w_guard": 0.20},
    # ↑ 策略倾向：ML营养模型占主导，推荐最符合营养目标的菜
    #   优点：营养配比精准，慢病患者优先受益
    #   缺点：可能推荐"营养完美但用户不爱吃"的菜，用户体验下降

    {"id": "W3", "label": "护栏增强型",
     "w_cf": 0.25, "w_nut": 0.35, "w_guard": 0.40},
    # ↑ 策略倾向：规则护栏权重提高到0.40，最强安全兜底
    #   优点：约束违规率最低，对慢病患者最安全
    #   缺点：过于保守，个性化不足，推荐结果"千篇一律"

    {"id": "W4", "label": "均衡型",
     "w_cf": 0.33, "w_nut": 0.34, "w_guard": 0.33},
    # ↑ 策略倾向：三个维度各占1/3，无偏好
    #   优点：各方面兼顾，没有明显短板
    #   缺点：各方面都不突出，可能"面面俱到但样样不精"

    {"id": "W5", "label": "当前方案",
     "w_cf": 0.45, "w_nut": 0.35, "w_guard": 0.20},
    # ↑ ★ 生产环境当前使用的权重组合 ★
    #   设计原理：CF个性化主导(45%) + ML营养辅助(35%) + 护栏兜底(20%)
    #   这个配置的假设是："用户喜欢"比"营养完美"更重要，
    #   但营养也不能偏离太远，护栏作为安全网防止极端不健康的推荐。

    {"id": "W6", "label": "高护栏兜底型",
     "w_cf": 0.35, "w_nut": 0.45, "w_guard": 0.20},
    # ↑ 策略倾向：ML权重略高于CF，但保持护栏不变
    #   对比W5和W6可以观察：在护栏不变的情况下，
    #   CF↓10% + ML↑10% 对整体推荐质量的影响。
]


# ═════════════════════════════════════════════════════════════
# 工具函数
# ═════════════════════════════════════════════════════════════

def _safe_float(value, default=0.0):
    """安全浮点转换，防 None/非数字/异常"""
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


# ═════════════════════════════════════════════════════════════
# 数据加载
# ═════════════════════════════════════════════════════════════

def load_data():
    """
    加载测试数据：优先从数据库读取真实数据，失败则使用内置合成数据。

    数据库加载条件：
      - 至少有8个有目标类型的用户画像
      - 食谱数据非空

    返回：
      (users, recipes) — 用户画像列表和食谱列表
    """
    recipes = SYNTHETIC_RECIPES
    users = TEST_USERS
    db_available = False

    try:
        from real_data_source import load_real_user_profiles, load_real_recipes

        real_profiles = load_real_user_profiles()
        real_recipes = load_real_recipes()

        if real_profiles and real_recipes:
            db_available = True

            # ── 将数据库画像转换为 TEST_USERS 格式 ──
            db_users = []
            for uid, profile in real_profiles.items():
                # 只取有目标类型的用户（无目标无法评估营养适配）
                if not profile.get("goalType"):
                    continue
                db_users.append({
                    "user_id": uid,
                    "health_info": {
                        "age": profile.get("age", 30),
                        "gender": profile.get("gender", ""),
                        "height": profile.get("height", 0),
                        "weight": profile.get("weight", 0),
                        "bmi": profile.get("bmi", 22),
                        "bmr": profile.get("bmr", 0),
                        "activityLevel": profile.get("activityLevel", ""),
                        "chronicDiseases": profile.get("chronicDiseases", ""),
                        "allergies": profile.get("allergies", ""),
                    },
                    "diet_goal": {
                        "goalType": profile.get("goalType", ""),
                        "targetCalories": profile.get("targetCalories", 2000),
                        "proteinTarget": profile.get("proteinTarget", 100),
                        "carbsTarget": profile.get("carbsTarget", 250),
                        "fatTarget": profile.get("fatTarget", 56),
                        "waterTarget": 2000,
                    }
                })

            # 数据库用户数足够（≥8）才使用真实数据
            if len(db_users) >= 8:
                users = db_users
                # 将真实食谱字典转为列表格式（保留 id 字段）
                recipes_list = []
                for rid, r in real_recipes.items():
                    r["id"] = rid
                    recipes_list.append(r)
                recipes = recipes_list
                print(f"[DB] 加载 {len(users)} 位用户, {len(recipes)} 道食谱")
            else:
                print(f"[警告] DB用户数不足({len(db_users)}), 使用内置测试数据")

    except Exception as e:
        import traceback
        print(f"[信息] 数据库不可用: {e}")
        traceback.print_exc()

    return users, recipes


# ═════════════════════════════════════════════════════════════
# 核心评分计算
# ═════════════════════════════════════════════════════════════

def compute_scores(engine, user_data, recipes, weight_config):
    """
    对单个用户在所有候选食谱上运行完整的推荐评分流程。

    这是 weight_sensitivity_analysis 的核心函数。
    它复用了 RecommendEngineV2 的评分流程，但使用自定义权重进行融合。

    流程：
      ① 构建用户画像 + 找相似用户
      ② 解析目标类型、疾病、过敏等约束
      ③ 遍历早/午/晚三餐的每个候选食谱：
          a. 过滤：跳过不属于该餐次的食谱 + 含过敏原的食谱
          b. 计算三个分量：CF分 / 营养ML分 / 规则护栏分
          c. 用指定权重融合：final = cf×w_cf + nut×w_nut + guard×w_guard
      ④ 每餐取 Top-3 返回

    参数：
      engine        : RecommendEngineV2 实例
      user_data     : 用户数据 {"user_id", "health_info", "diet_goal"}
      recipes       : 候选食谱列表
      weight_config : 权重配置 {"w_cf", "w_nut", "w_guard"}

    返回：
      {"breakfast": [{recipe1}, {recipe2}, {recipe3}],
       "lunch":     [{...}, {...}, {...}],
       "dinner":    [{...}, {...}, {...}]}
      每个 recipe 字典包含营养值 + 各分量分 + 最终分
    """
    user_id = user_data["user_id"]
    health_info = user_data["health_info"]
    diet_goal = user_data["diet_goal"]

    w_cf = weight_config["w_cf"]
    w_nut = weight_config["w_nut"]
    w_guard = weight_config["w_guard"]

    # ── ① 用户画像 + 相似用户（用于 CF 打分）──
    user_profile = engine._build_user_profile(health_info, diet_goal)
    similar_users = engine._find_similar_users(user_profile)

    # ── ② 解析约束条件 ──
    goal_type = engine._normalize_text(diet_goal.get("goalType", ""))
    daily_target_calories = engine._resolve_daily_energy_target(
        health_info, diet_goal, goal_type
    )
    allergies = engine._split_tokens(health_info.get("allergies", ""))
    chronic_diseases = engine._normalize_text(
        health_info.get("chronicDiseases", "")
    )

    # 存放三餐的所有评分结果（排序前）
    all_scored = {"breakfast": [], "lunch": [], "dinner": []}

    # ── ③ 遍历三餐，对每个候选食谱打分 ──
    for meal_type in ("breakfast", "lunch", "dinner"):
        # 计算该餐次的目标值
        meal_target = engine._meal_target(daily_target_calories, meal_type)
        macro_targets = engine._resolve_macro_targets(
            daily_target_calories, meal_type, diet_goal, goal_type
        )

        for recipe in recipes:
            # ── 过滤：餐次不匹配 → 跳过 ──
            inferred = recipe.get("mealType") or engine._infer_meal_type(recipe)
            if inferred != meal_type:
                continue

            # ── 过滤：含过敏原 → 跳过 ──
            if engine._contains_allergy(recipe, allergies):
                continue

            # ── 计算三个分量得分 ──

            # 分量1：协同过滤分（基于 SVD 嵌入 + 相似用户加权平均）
            model_cf_score = engine._calculate_model_cf_score(
                user_id=user_id, recipe=recipe,
                user_profile=user_profile, similar_users=similar_users
            )

            # 分量2：规则护栏分（4个维度：能量/宏量/目标/疾病适配）
            rule_guardrail_score = engine._calculate_health_score(
                recipe, meal_type, meal_target, macro_targets,
                goal_type, chronic_diseases
            )

            # 分量3：营养ML分（GBDT 预测，失败时用规则护栏分兜底）
            nutrition_feature_map = engine._build_nutrition_feature_map(
                recipe=recipe, meal_type=meal_type, meal_target=meal_target,
                macro_targets=macro_targets, goal_type=goal_type,
                chronic_diseases=chronic_diseases
            )
            nutrition_ml_score = engine._calculate_nutrition_ml_score(
                nutrition_feature_map, fallback_score=rule_guardrail_score
            )

            # ── ★核心★ 三组件加权融合（这里用实验权重替换默认权重）──
            final_score = (
                model_cf_score * w_cf +
                nutrition_ml_score * w_nut +
                rule_guardrail_score * w_guard
            )

            # 保存该食谱的完整评分信息（用于后续指标计算）
            all_scored[meal_type].append({
                "recipe_id": recipe.get("id"),
                "recipe_name": recipe.get("name", ""),
                "calories": _safe_float(
                    recipe.get("totalCalories", recipe.get("calories", 0))
                ),
                "protein": _safe_float(recipe.get("protein", 0)),
                "carbs": _safe_float(recipe.get("carbs", 0)),
                "fat": _safe_float(recipe.get("fat", 0)),
                "sodium": _safe_float(recipe.get("sodium", 0)),
                "gi": _safe_float(recipe.get("gi", recipe.get("giValue", 0))),
                # 三个分量分（保留3位小数，便于对比分析）
                "cf_score": round(model_cf_score, 3),
                "nut_score": round(nutrition_ml_score, 3),
                "guard_score": round(rule_guardrail_score, 3),
                "final_score": round(final_score, 4),
                "meal_target": meal_target,
                "macro_targets": macro_targets,
            })

    # ── ④ 每餐取 Top-3 返回 ──
    top_n = {"breakfast": 3, "lunch": 3, "dinner": 3}
    recommended = {}
    for meal_type in ("breakfast", "lunch", "dinner"):
        scored = sorted(
            all_scored[meal_type],
            key=lambda x: x["final_score"],
            reverse=True   # 从高到低排序
        )
        recommended[meal_type] = scored[:top_n[meal_type]]

    return recommended


# ═════════════════════════════════════════════════════════════
# 指标计算
# ═════════════════════════════════════════════════════════════

def compute_metrics(all_user_results, users, total_recipe_count):
    """
    汇总所有用户的推荐结果，计算7项全局评估指标。

    参数：
      all_user_results : {user_id: {"breakfast": [...], "lunch": [...], "dinner": [...]}}
      users            : 用户画像列表（用于查找慢病信息）
      total_recipe_count : 候选食谱总数（用于计算覆盖率）

    返回：7项指标字典
      - total_recommendations   : 总推荐条数（用户数 × 9 道）
      - unique_recipes          : 不重复食谱数（反映多样性）
      - coverage_rate           : 覆盖率% = 不重复数/候选总数
      - avg_match_score         : 平均最终匹配分
      - avg_calorie_deviation_pct : 平均热量偏差%（越低越好）
      - avg_protein_deviation_pct : 平均蛋白质偏差%
      - avg_carbs_deviation_pct   : 平均碳水偏差%
      - avg_fat_deviation_pct     : 平均脂肪偏差%
      - constraint_violations   : 约束违规次数
      - constraint_violation_rate : 约束违规率%
    """
    total_recipes = 0               # 推荐总条数
    total_calorie_deviation = 0.0   # 热量偏差累加
    total_protein_deviation = 0.0   # 蛋白质偏差累加
    total_carbs_deviation = 0.0     # 碳水偏差累加
    total_fat_deviation = 0.0       # 脂肪偏差累加
    avg_score_sum = 0.0             # 匹配分累加
    unique_recipes = set()          # 去重食谱ID集合（衡量多样性）
    high_sodium_count = 0           # 高血压用户 + 高钠食谱 违规计数
    high_gi_count = 0               # 糖尿病用户 + 高GI食谱 违规计数

    for user_id, meals in all_user_results.items():
        # ── 查找该用户的画像信息 ──
        user_info = None
        for u in users:
            if u["user_id"] == user_id:
                user_info = u
                break
        if user_info is None:
            continue

        # 判断该用户的慢病类型（用于约束违规检测）
        has_hypertension = "hypertension" in str(
            user_info["health_info"].get("chronicDiseases", "")
        ).lower()
        has_diabetes = "diabetes" in str(
            user_info["health_info"].get("chronicDiseases", "")
        ).lower()

        # ── 遍历该用户三餐的推荐结果 ──
        for meal_type, recipes in meals.items():
            for r in recipes:
                total_recipes += 1
                avg_score_sum += r["final_score"]
                unique_recipes.add(r["recipe_id"])

                # 热量偏差 = |实际-目标| / 目标（相对偏差）
                if r["meal_target"] > 0:
                    total_calorie_deviation += (
                        abs(r["calories"] - r["meal_target"]) / r["meal_target"]
                    )

                # 宏量营养素偏差（蛋白质/碳水/脂肪）
                macros = r["macro_targets"]
                if macros.get("protein", 0) > 0:
                    total_protein_deviation += (
                        abs(r["protein"] - macros["protein"]) / macros["protein"]
                    )
                if macros.get("carbs", 0) > 0:
                    total_carbs_deviation += (
                        abs(r["carbs"] - macros["carbs"]) / macros["carbs"]
                    )
                if macros.get("fat", 0) > 0:
                    total_fat_deviation += (
                        abs(r["fat"] - macros["fat"]) / macros["fat"]
                    )

                # ── 约束违规检测 ──
                # 高血压用户 → 钠 > 500mg 视为违规
                if has_hypertension and r["sodium"] > 500:
                    high_sodium_count += 1
                # 糖尿病用户 → GI > 60 视为违规
                if has_diabetes and r["gi"] > 60:
                    high_gi_count += 1

    if total_recipes == 0:
        return {"error": "no recipes"}

    return {
        "total_recommendations": total_recipes,
        "unique_recipes": len(unique_recipes),
        # 覆盖率 = 推荐中不重复食谱数 / 候选食谱总数
        "coverage_rate": round(
            len(unique_recipes) / max(total_recipe_count, 1) * 100, 1
        ),
        # 平均匹配分
        "avg_match_score": round(avg_score_sum / total_recipes, 4),
        # 偏差百分比（总偏差 / 推荐条数 × 100）
        "avg_calorie_deviation_pct": round(
            total_calorie_deviation / total_recipes * 100, 1
        ),
        "avg_protein_deviation_pct": round(
            total_protein_deviation / total_recipes * 100, 1
        ),
        "avg_carbs_deviation_pct": round(
            total_carbs_deviation / total_recipes * 100, 1
        ),
        "avg_fat_deviation_pct": round(
            total_fat_deviation / total_recipes * 100, 1
        ),
        "constraint_violations": high_sodium_count + high_gi_count,
        "constraint_violation_rate": round(
            (high_sodium_count + high_gi_count) / total_recipes * 100, 1
        ),
    }


# ═════════════════════════════════════════════════════════════
# 主流程
# ═════════════════════════════════════════════════════════════

def main():
    """
    权重敏感性分析主流程：

    ① 加载测试数据（数据库优先，合成回退）
    ② 初始化 RecommendEngineV2
    ③ 对6组权重配置分别运行全量评估
    ④ 输出7项指标的对比表
    ⑤ 标注各指标的最优方案
    ⑥ 输出当前方案(W5)的详细分析（含三个分量的均值）
    """
    print("=" * 72)
    print("  混合推荐权重敏感性分析")
    print("=" * 72)

    # ── ① 加载测试数据 ──
    users, recipes = load_data()
    print(f"  测试用户数: {len(users)}")
    print(f"  候选食谱数: {len(recipes)}")
    print(f"  权重方案数: {len(WEIGHT_CONFIGS)}")

    # ── ② 初始化 V2 推荐引擎 ──
    engine = RecommendEngineV2()

    # ── ③ 对每组权重运行全量分析 ──
    results = {}              # 存储每组权重的汇总指标
    all_results_detail = {}   # 存储每组权重的详细结果（用于分量分析）
    for wc in WEIGHT_CONFIGS:
        wc_label = (
            f"{wc['id']} {wc['label']} "
            f"({wc['w_cf']:.2f}, {wc['w_nut']:.2f}, {wc['w_guard']:.2f})"
        )
        print(f"\n  运行: {wc_label} ...")

        all_user_results = {}
        for user in users:
            try:
                # 对该用户在所有食谱上运行推荐评分
                rec = compute_scores(engine, user, recipes, wc)
                all_user_results[user["user_id"]] = rec
            except Exception as e:
                print(f"    用户 {user['user_id']} 出错: {e}")
                continue

        # 汇总该权重方案的所有用户结果 → 计算全局指标
        metrics = compute_metrics(all_user_results, users, len(recipes))
        metrics["label"] = wc_label
        results[wc["id"]] = metrics
        all_results_detail[wc["id"]] = all_user_results

    # ── ④ 输出对比表 ──
    print("\n" + "=" * 72)
    print("  指标对比结果")
    print("=" * 72)

    # 表头（固定列宽，方便在终端中对齐阅读）
    header = (
        f"{'方案':<22s} {'匹配分':>6s} {'热量偏差':>8s} {'蛋白偏差':>8s} "
        f"{'碳水偏差':>8s} {'脂肪偏差':>8s} {'覆盖率':>6s} {'违规率':>6s}"
    )
    print(header)
    print("-" * 72)

    # 用于追踪每项指标的最优方案
    # 格式：{指标名: (方向"max"/"min", 最优值, 方案ID)}
    best_scores = {
        "avg_match_score":            ("max", -1, ""),
        "avg_calorie_deviation_pct":  ("min", 999, ""),
        "avg_protein_deviation_pct":  ("min", 999, ""),
        "avg_carbs_deviation_pct":    ("min", 999, ""),
        "avg_fat_deviation_pct":      ("min", 999, ""),
        "coverage_rate":              ("max", -1, ""),
        "constraint_violation_rate":  ("min", 999, ""),
    }

    # 逐行输出每组权重的指标
    for wc in WEIGHT_CONFIGS:
        wid = wc["id"]
        m = results.get(wid, {})
        if not m or "error" in m:
            continue

        row = (
            f"{m['label']:<22s} "
            f"{m['avg_match_score']:>6.3f} "
            f"{m['avg_calorie_deviation_pct']:>7.1f}% "
            f"{m['avg_protein_deviation_pct']:>7.1f}% "
            f"{m['avg_carbs_deviation_pct']:>7.1f}% "
            f"{m['avg_fat_deviation_pct']:>7.1f}% "
            f"{m['coverage_rate']:>5.1f}% "
            f"{m['constraint_violation_rate']:>5.1f}%"
        )
        print(row)

        # 更新各指标的最优方案
        for key, (direction, best_val, best_label) in best_scores.items():
            val = m.get(key, 0)
            if direction == "max" and val > best_val:
                best_scores[key] = ("max", val, wid)
            elif direction == "min" and val < best_val:
                best_scores[key] = ("min", val, wid)

    # ── ⑤ 输出各指标的最优方案 ──
    print("-" * 72)
    print("  各指标最优方案:")
    metric_names = {
        "avg_match_score":            "平均匹配分",
        "avg_calorie_deviation_pct":  "热量偏差",
        "avg_protein_deviation_pct":  "蛋白偏差",
        "avg_carbs_deviation_pct":    "碳水偏差",
        "avg_fat_deviation_pct":      "脂肪偏差",
        "coverage_rate":              "覆盖率",
        "constraint_violation_rate":  "违规率",
    }
    for key, (_, _, best_id) in best_scores.items():
        for wc in WEIGHT_CONFIGS:
            if wc["id"] == best_id:
                print(f"    {metric_names[key]:<10s}: {wc['label']}")

    # ── ⑥ 输出当前方案 (W5) 的详细分析 ──
    print("\n" + "=" * 72)
    print("  当前方案 (W5, 0.45/0.35/0.20) 分析")
    print("=" * 72)
    w5 = results.get("W5", {})
    if w5 and "error" not in w5:
        print(f"    平均匹配分:       {w5.get('avg_match_score', 'N/A'):.4f}")
        print(f"    平均热量偏差:     {w5.get('avg_calorie_deviation_pct', 'N/A'):.1f}%")
        print(f"    平均蛋白质偏差:   {w5.get('avg_protein_deviation_pct', 'N/A'):.1f}%")
        print(f"    平均碳水偏差:     {w5.get('avg_carbs_deviation_pct', 'N/A'):.1f}%")
        print(f"    平均脂肪偏差:     {w5.get('avg_fat_deviation_pct', 'N/A'):.1f}%")
        print(f"    推荐覆盖率:       {w5.get('coverage_rate', 'N/A'):.1f}%")
        print(f"    约束违规率:       {w5.get('constraint_violation_rate', 'N/A'):.1f}%")

        # 提取 W5 方案下三个分量的均值
        # 这能帮助理解：在最终得分中，哪个分量贡献最大
        w5_detail = all_results_detail.get("W5", {})
        cf_scores = []
        nut_scores = []
        guard_scores = []
        for uid, meals in w5_detail.items():
            for meal_type, recs in meals.items():
                for r in recs:
                    cf_scores.append(r["cf_score"])
                    nut_scores.append(r["nut_score"])
                    guard_scores.append(r["guard_score"])

        if cf_scores:
            print(f"    CF分量均值:       {sum(cf_scores)/len(cf_scores):.3f}")
            print(f"    营养分量均值:     {sum(nut_scores)/len(nut_scores):.3f}")
            print(f"    护栏分量均值:     {sum(guard_scores)/len(guard_scores):.3f}")

            # 分量均值说明（用于答辩）：
            # - CF分量均值高 → 相似用户的偏好被有效利用
            # - 营养分量均值高 → GBDT模型学到的营养匹配规律有效
            # - 护栏分量均值相对稳定（规则计算的，不受权重影响）
            # - 最终分 = cf×0.45 + nut×0.35 + guard×0.20 会放大CF的影响

    print("\n" + "=" * 72)
    print("  分析完成")
    print("=" * 72)


if __name__ == "__main__":
    main()
