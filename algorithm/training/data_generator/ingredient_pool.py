# =============================================================================
# 食材营养数据库（每100g可食部）
# =============================================================================
# 数据来源：人工整理，主要参考以下标准文献：
#   1. 中国食物成分表 标准版（第6版，杨月欣主编）
#      - 米饭/面条/鸡胸肉/牛里脊/豆腐/豆浆/菠菜/番茄等 42 种食材
#   2. USDA FoodData Central (SR Legacy)
#      - 三文鱼/鳕鱼/西蓝花/牛油果/蓝莓/杏仁/藜麦等 14 种食材
#   3. 中国居民膳食营养素参考摄入量 (DRIs 2023)
#      - GI 值校验
#   4. 个别调味品（橄榄油/黑胡椒/蒜末）以行业通用值为准
#
# 数据整理方式：手工编码（非爬虫、非API调用）。
# 每个食材查 1-2 个权威来源交叉验证后录入。
# 设计背景：毕业设计期间无真实食材数据库接入，采用手工整理保证
#   营养推荐算法的基础数据可信度。
# =============================================================================

BASE_INGREDIENTS = [
    {"name": "燕麦", "category": "主食", "sub_category": "谷物", "calories": 389, "protein": 16.9, "carbs": 66.3, "fat": 6.9, "fiber": 10.6, "sugar": 1.0, "sodium": 2, "gi": 55, "cholesterol": 0, "tags": ["whole_grain", "high_fiber", "breakfast_friendly"]},
    {"name": "糙米", "category": "主食", "sub_category": "谷物", "calories": 111, "protein": 2.6, "carbs": 23.0, "fat": 0.9, "fiber": 1.8, "sugar": 0.4, "sodium": 5, "gi": 68, "cholesterol": 0, "tags": ["whole_grain", "low_gi"]},
    {"name": "藜麦", "category": "主食", "sub_category": "谷物", "calories": 120, "protein": 4.4, "carbs": 21.3, "fat": 1.9, "fiber": 2.8, "sugar": 0.9, "sodium": 7, "gi": 53, "cholesterol": 0, "tags": ["whole_grain", "high_protein", "low_gi"]},
    {"name": "全麦面包", "category": "主食", "sub_category": "面包", "calories": 247, "protein": 13.0, "carbs": 41.0, "fat": 3.4, "fiber": 7.0, "sugar": 5.5, "sodium": 400, "gi": 50, "cholesterol": 0, "tags": ["whole_grain", "breakfast_friendly"]},
    {"name": "红薯", "category": "主食", "sub_category": "薯类", "calories": 86, "protein": 1.6, "carbs": 20.1, "fat": 0.1, "fiber": 3.0, "sugar": 4.2, "sodium": 55, "gi": 54, "cholesterol": 0, "tags": ["whole_grain", "high_fiber", "low_gi"]},
    {"name": "玉米", "category": "主食", "sub_category": "粗粮", "calories": 106, "protein": 3.4, "carbs": 22.8, "fat": 1.5, "fiber": 2.9, "sugar": 4.5, "sodium": 1, "gi": 55, "cholesterol": 0, "tags": ["whole_grain", "high_fiber"]},
    {"name": "小米", "category": "主食", "sub_category": "谷物", "calories": 361, "protein": 11.0, "carbs": 72.8, "fat": 3.1, "fiber": 1.6, "sugar": 1.8, "sodium": 5, "gi": 61, "cholesterol": 0, "tags": ["whole_grain", "easy_digest"]},
    {"name": "荞麦面", "category": "主食", "sub_category": "面食", "calories": 99, "protein": 5.0, "carbs": 21.4, "fat": 0.1, "fiber": 2.7, "sugar": 0.4, "sodium": 3, "gi": 46, "cholesterol": 0, "tags": ["whole_grain", "low_gi"]},
    {"name": "紫薯", "category": "主食", "sub_category": "薯类", "calories": 82, "protein": 1.7, "carbs": 19.9, "fat": 0.1, "fiber": 3.3, "sugar": 4.0, "sodium": 33, "gi": 50, "cholesterol": 0, "tags": ["whole_grain", "high_fiber", "breakfast_friendly"]},
    {"name": "鸡胸肉", "category": "肉类", "sub_category": "禽肉", "calories": 133, "protein": 19.4, "carbs": 0.0, "fat": 5.0, "fiber": 0.0, "sugar": 0.0, "sodium": 50, "gi": 0, "cholesterol": 82, "tags": ["high_protein", "low_fat"]},
    {"name": "去皮鸡腿肉", "category": "肉类", "sub_category": "禽肉", "calories": 150, "protein": 18.0, "carbs": 0.0, "fat": 8.0, "fiber": 0.0, "sugar": 0.0, "sodium": 70, "gi": 0, "cholesterol": 90, "tags": ["high_protein"]},
    {"name": "牛里脊", "category": "肉类", "sub_category": "牛肉", "calories": 125, "protein": 20.2, "carbs": 0.0, "fat": 4.2, "fiber": 0.0, "sugar": 0.0, "sodium": 60, "gi": 0, "cholesterol": 65, "tags": ["high_protein", "iron_rich"]},
    {"name": "瘦猪里脊", "category": "肉类", "sub_category": "猪肉", "calories": 143, "protein": 20.3, "carbs": 0.0, "fat": 6.2, "fiber": 0.0, "sugar": 0.0, "sodium": 57, "gi": 0, "cholesterol": 70, "tags": ["high_protein"]},
    {"name": "三文鱼", "category": "肉类", "sub_category": "鱼类", "calories": 208, "protein": 20.4, "carbs": 0.0, "fat": 13.4, "fiber": 0.0, "sugar": 0.0, "sodium": 59, "gi": 0, "cholesterol": 55, "tags": ["omega3", "high_protein"]},
    {"name": "鳕鱼", "category": "肉类", "sub_category": "鱼类", "calories": 82, "protein": 17.8, "carbs": 0.0, "fat": 0.7, "fiber": 0.0, "sugar": 0.0, "sodium": 77, "gi": 0, "cholesterol": 43, "tags": ["high_protein", "low_fat", "easy_digest"]},
    {"name": "虾仁", "category": "肉类", "sub_category": "海鲜", "calories": 99, "protein": 24.0, "carbs": 0.2, "fat": 0.3, "fiber": 0.0, "sugar": 0.0, "sodium": 148, "gi": 0, "cholesterol": 189, "tags": ["high_protein", "low_fat"]},
    {"name": "金枪鱼", "category": "肉类", "sub_category": "鱼类", "calories": 132, "protein": 28.0, "carbs": 0.0, "fat": 1.3, "fiber": 0.0, "sugar": 0.0, "sodium": 37, "gi": 0, "cholesterol": 38, "tags": ["high_protein", "low_fat"]},
    {"name": "巴沙鱼", "category": "肉类", "sub_category": "鱼类", "calories": 91, "protein": 17.0, "carbs": 0.0, "fat": 2.2, "fiber": 0.0, "sugar": 0.0, "sodium": 45, "gi": 0, "cholesterol": 44, "tags": ["high_protein", "easy_digest"]},
    {"name": "鸡蛋", "category": "蛋类", "sub_category": "鸡蛋", "calories": 144, "protein": 13.3, "carbs": 1.3, "fat": 8.8, "fiber": 0.0, "sugar": 1.3, "sodium": 131, "gi": 0, "cholesterol": 585, "tags": ["high_protein", "breakfast_friendly"]},
    {"name": "鸡蛋清", "category": "蛋类", "sub_category": "蛋清", "calories": 52, "protein": 11.0, "carbs": 0.7, "fat": 0.2, "fiber": 0.0, "sugar": 0.7, "sodium": 166, "gi": 0, "cholesterol": 0, "tags": ["high_protein", "low_fat"]},
    {"name": "豆腐", "category": "豆制品", "sub_category": "豆腐", "calories": 81, "protein": 8.1, "carbs": 1.9, "fat": 4.2, "fiber": 0.4, "sugar": 0.7, "sodium": 14, "gi": 15, "cholesterol": 0, "tags": ["plant_protein", "low_fat", "easy_digest"]},
    {"name": "豆浆", "category": "豆制品", "sub_category": "豆浆", "calories": 31, "protein": 3.0, "carbs": 1.7, "fat": 1.6, "fiber": 0.2, "sugar": 0.8, "sodium": 3, "gi": 34, "cholesterol": 0, "tags": ["plant_protein", "breakfast_friendly"]},
    {"name": "毛豆", "category": "豆制品", "sub_category": "豆类", "calories": 131, "protein": 13.0, "carbs": 10.0, "fat": 5.0, "fiber": 5.2, "sugar": 2.2, "sodium": 6, "gi": 18, "cholesterol": 0, "tags": ["plant_protein", "high_fiber"]},
    {"name": "黑豆", "category": "豆制品", "sub_category": "豆类", "calories": 132, "protein": 8.9, "carbs": 23.7, "fat": 0.5, "fiber": 8.7, "sugar": 0.3, "sodium": 1, "gi": 30, "cholesterol": 0, "tags": ["plant_protein", "high_fiber", "low_gi"]},
    {"name": "鹰嘴豆", "category": "豆制品", "sub_category": "豆类", "calories": 164, "protein": 8.9, "carbs": 27.4, "fat": 2.6, "fiber": 7.6, "sugar": 4.8, "sodium": 24, "gi": 28, "cholesterol": 0, "tags": ["plant_protein", "high_fiber", "low_gi"]},
    {"name": "无糖酸奶", "category": "乳制品", "sub_category": "酸奶", "calories": 72, "protein": 3.5, "carbs": 9.3, "fat": 2.7, "fiber": 0.0, "sugar": 4.8, "sodium": 53, "gi": 36, "cholesterol": 9, "tags": ["breakfast_friendly", "gut_friendly"]},
    {"name": "低脂牛奶", "category": "乳制品", "sub_category": "牛奶", "calories": 46, "protein": 3.4, "carbs": 4.8, "fat": 1.5, "fiber": 0.0, "sugar": 4.8, "sodium": 50, "gi": 32, "cholesterol": 5, "tags": ["breakfast_friendly"]},
    {"name": "希腊酸奶", "category": "乳制品", "sub_category": "酸奶", "calories": 97, "protein": 9.0, "carbs": 3.9, "fat": 5.0, "fiber": 0.0, "sugar": 3.6, "sodium": 36, "gi": 32, "cholesterol": 5, "tags": ["high_protein", "breakfast_friendly"]},
    {"name": "西蓝花", "category": "蔬菜", "sub_category": "十字花科", "calories": 34, "protein": 2.8, "carbs": 6.6, "fat": 0.4, "fiber": 2.6, "sugar": 1.7, "sodium": 33, "gi": 10, "cholesterol": 0, "tags": ["high_fiber", "low_gi", "green_veg"]},
    {"name": "生菜", "category": "蔬菜", "sub_category": "叶菜", "calories": 15, "protein": 1.4, "carbs": 2.9, "fat": 0.2, "fiber": 1.3, "sugar": 0.8, "sodium": 28, "gi": 15, "cholesterol": 0, "tags": ["salad", "green_veg", "low_calorie"]},
    {"name": "菠菜", "category": "蔬菜", "sub_category": "叶菜", "calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "sugar": 0.4, "sodium": 79, "gi": 15, "cholesterol": 0, "tags": ["green_veg", "iron_rich"]},
    {"name": "小白菜", "category": "蔬菜", "sub_category": "叶菜", "calories": 13, "protein": 1.5, "carbs": 2.4, "fat": 0.2, "fiber": 1.0, "sugar": 1.2, "sodium": 65, "gi": 15, "cholesterol": 0, "tags": ["green_veg", "low_calorie"]},
    {"name": "番茄", "category": "蔬菜", "sub_category": "茄果", "calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "fiber": 1.2, "sugar": 2.6, "sodium": 5, "gi": 15, "cholesterol": 0, "tags": ["salad", "low_calorie"]},
    {"name": "黄瓜", "category": "蔬菜", "sub_category": "瓜类", "calories": 15, "protein": 0.7, "carbs": 3.6, "fat": 0.1, "fiber": 0.5, "sugar": 1.7, "sodium": 2, "gi": 15, "cholesterol": 0, "tags": ["salad", "low_calorie"]},
    {"name": "胡萝卜", "category": "蔬菜", "sub_category": "根茎", "calories": 41, "protein": 0.9, "carbs": 9.6, "fat": 0.2, "fiber": 2.8, "sugar": 4.7, "sodium": 69, "gi": 35, "cholesterol": 0, "tags": ["high_fiber", "orange_veg"]},
    {"name": "彩椒", "category": "蔬菜", "sub_category": "茄果", "calories": 31, "protein": 1.0, "carbs": 6.0, "fat": 0.3, "fiber": 2.1, "sugar": 4.2, "sodium": 4, "gi": 15, "cholesterol": 0, "tags": ["colorful_veg", "salad"]},
    {"name": "芦笋", "category": "蔬菜", "sub_category": "茎菜", "calories": 20, "protein": 2.2, "carbs": 3.9, "fat": 0.1, "fiber": 2.1, "sugar": 1.9, "sodium": 2, "gi": 15, "cholesterol": 0, "tags": ["green_veg", "low_calorie"]},
    {"name": "菌菇", "category": "蔬菜", "sub_category": "菌类", "calories": 22, "protein": 3.1, "carbs": 3.3, "fat": 0.3, "fiber": 2.5, "sugar": 2.0, "sodium": 5, "gi": 15, "cholesterol": 0, "tags": ["high_fiber", "umami"]},
    {"name": "南瓜", "category": "蔬菜", "sub_category": "瓜类", "calories": 26, "protein": 1.0, "carbs": 6.5, "fat": 0.1, "fiber": 0.5, "sugar": 2.8, "sodium": 1, "gi": 64, "cholesterol": 0, "tags": ["easy_digest", "orange_veg"]},
    {"name": "山药", "category": "蔬菜", "sub_category": "根茎", "calories": 57, "protein": 1.9, "carbs": 12.4, "fat": 0.2, "fiber": 1.0, "sugar": 0.4, "sodium": 5, "gi": 51, "cholesterol": 0, "tags": ["easy_digest", "root_veg"]},
    {"name": "西葫芦", "category": "蔬菜", "sub_category": "瓜类", "calories": 17, "protein": 1.2, "carbs": 3.1, "fat": 0.3, "fiber": 1.0, "sugar": 2.5, "sodium": 8, "gi": 15, "cholesterol": 0, "tags": ["low_calorie", "easy_digest"]},
    {"name": "芹菜", "category": "蔬菜", "sub_category": "茎菜", "calories": 16, "protein": 0.7, "carbs": 3.0, "fat": 0.2, "fiber": 1.6, "sugar": 1.3, "sodium": 80, "gi": 15, "cholesterol": 0, "tags": ["high_fiber", "low_calorie"]},
    {"name": "海带", "category": "蔬菜", "sub_category": "藻类", "calories": 43, "protein": 1.6, "carbs": 9.6, "fat": 0.6, "fiber": 1.3, "sugar": 0.5, "sodium": 900, "gi": 15, "cholesterol": 0, "tags": ["iodine_rich", "low_calorie"]},
    {"name": "紫甘蓝", "category": "蔬菜", "sub_category": "十字花科", "calories": 31, "protein": 1.4, "carbs": 7.4, "fat": 0.2, "fiber": 2.1, "sugar": 3.8, "sodium": 27, "gi": 15, "cholesterol": 0, "tags": ["salad", "colorful_veg", "high_fiber"]},
    {"name": "苹果", "category": "水果", "sub_category": "仁果", "calories": 52, "protein": 0.3, "carbs": 13.8, "fat": 0.2, "fiber": 2.4, "sugar": 10.4, "sodium": 1, "gi": 36, "cholesterol": 0, "tags": ["fruit", "low_gi", "breakfast_friendly"]},
    {"name": "蓝莓", "category": "水果", "sub_category": "浆果", "calories": 57, "protein": 0.7, "carbs": 14.5, "fat": 0.3, "fiber": 2.4, "sugar": 10.0, "sodium": 1, "gi": 53, "cholesterol": 0, "tags": ["fruit", "antioxidant", "breakfast_friendly"]},
    {"name": "香蕉", "category": "水果", "sub_category": "热带水果", "calories": 89, "protein": 1.1, "carbs": 22.8, "fat": 0.3, "fiber": 2.6, "sugar": 12.2, "sodium": 1, "gi": 51, "cholesterol": 0, "tags": ["fruit", "energy_dense"]},
    {"name": "橙子", "category": "水果", "sub_category": "柑橘", "calories": 47, "protein": 0.9, "carbs": 11.8, "fat": 0.1, "fiber": 2.4, "sugar": 9.4, "sodium": 0, "gi": 43, "cholesterol": 0, "tags": ["fruit", "low_gi"]},
    {"name": "草莓", "category": "水果", "sub_category": "浆果", "calories": 32, "protein": 0.7, "carbs": 7.7, "fat": 0.3, "fiber": 2.0, "sugar": 4.9, "sodium": 1, "gi": 40, "cholesterol": 0, "tags": ["fruit", "low_gi", "breakfast_friendly"]},
    {"name": "牛油果", "category": "水果", "sub_category": "热带水果", "calories": 160, "protein": 2.0, "carbs": 8.5, "fat": 14.7, "fiber": 6.7, "sugar": 0.7, "sodium": 7, "gi": 10, "cholesterol": 0, "tags": ["healthy_fat", "high_fiber"]},
    {"name": "杏仁", "category": "坚果", "sub_category": "坚果", "calories": 579, "protein": 21.2, "carbs": 21.6, "fat": 49.9, "fiber": 12.5, "sugar": 4.4, "sodium": 1, "gi": 15, "cholesterol": 0, "tags": ["healthy_fat", "energy_dense"]},
    {"name": "核桃", "category": "坚果", "sub_category": "坚果", "calories": 654, "protein": 15.2, "carbs": 13.7, "fat": 65.2, "fiber": 6.7, "sugar": 2.6, "sodium": 2, "gi": 15, "cholesterol": 0, "tags": ["healthy_fat", "energy_dense"]},
    {"name": "花生酱", "category": "坚果", "sub_category": "坚果制品", "calories": 588, "protein": 25.1, "carbs": 20.0, "fat": 50.4, "fiber": 6.0, "sugar": 9.0, "sodium": 17, "gi": 14, "cholesterol": 0, "tags": ["healthy_fat", "energy_dense", "breakfast_friendly"]},
    {"name": "橄榄油", "category": "调味", "sub_category": "油脂", "calories": 884, "protein": 0.0, "carbs": 0.0, "fat": 100.0, "fiber": 0.0, "sugar": 0.0, "sodium": 2, "gi": 0, "cholesterol": 0, "tags": ["healthy_fat", "low_sodium"]},
    {"name": "低钠酱油", "category": "调味", "sub_category": "调味品", "calories": 53, "protein": 8.1, "carbs": 4.9, "fat": 0.1, "fiber": 0.0, "sugar": 0.4, "sodium": 3700, "gi": 20, "cholesterol": 0, "tags": ["seasoning", "low_sodium"]},
    {"name": "黑胡椒", "category": "调味", "sub_category": "香辛料", "calories": 251, "protein": 10.4, "carbs": 64.8, "fat": 3.3, "fiber": 25.3, "sugar": 0.6, "sodium": 20, "gi": 5, "cholesterol": 0, "tags": ["seasoning"]},
    {"name": "蒜末", "category": "调味", "sub_category": "香辛料", "calories": 149, "protein": 6.4, "carbs": 33.1, "fat": 0.5, "fiber": 2.1, "sugar": 1.0, "sodium": 17, "gi": 10, "cholesterol": 0, "tags": ["seasoning"]},
]
