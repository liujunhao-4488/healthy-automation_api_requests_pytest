SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 新增 25 个食材
-- ----------------------------
INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 43, '藜麦', '主食', NULL, 368, 14.1, 64.2, 6.1, 7.0, NULL, NULL, 53, NULL, NULL, NULL, '高蛋白高纤维全谷物', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 43 OR `name` = '藜麦');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 44, '土豆', '主食', NULL, 77, 2.0, 17.2, 0.1, 2.2, NULL, NULL, 62, NULL, NULL, NULL, '常见复合碳水食材', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 44 OR `name` = '土豆');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 45, '南瓜', '主食', NULL, 26, 1.0, 6.5, 0.1, 0.5, NULL, NULL, 75, NULL, NULL, NULL, '低脂低热量、富含胡萝卜素', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 45 OR `name` = '南瓜');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 46, '小米', '主食', NULL, 361, 11.0, 75.0, 3.1, 1.6, NULL, NULL, 71, NULL, NULL, NULL, '适合熬粥和温和饮食', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 46 OR `name` = '小米');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 47, '馒头', '主食', NULL, 223, 7.0, 47.0, 1.1, 1.3, NULL, NULL, 88, NULL, NULL, NULL, '常见中式主食', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 47 OR `name` = '馒头');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 48, '三文鱼', '肉类', NULL, 208, 20.4, 0.0, 13.4, 0.0, NULL, NULL, 0, 55, NULL, NULL, '优质蛋白和不饱和脂肪来源', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 48 OR `name` = '三文鱼');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 49, '金枪鱼', '肉类', NULL, 132, 28.0, 0.0, 1.3, 0.0, NULL, NULL, 0, 38, NULL, NULL, '低脂高蛋白海鱼', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 49 OR `name` = '金枪鱼');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 50, '瘦牛肉', '肉类', NULL, 191, 20.2, 0.0, 12.0, 0.0, NULL, NULL, 0, 58, NULL, NULL, '富含铁和优质蛋白', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 50 OR `name` = '瘦牛肉');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 51, '里脊肉', '肉类', NULL, 143, 21.0, 0.0, 6.2, 0.0, NULL, NULL, 0, 62, NULL, NULL, '相对低脂的猪肉部位', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 51 OR `name` = '里脊肉');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 52, '生菜', '蔬菜', NULL, 15, 1.4, 2.9, 0.2, 1.1, NULL, NULL, 15, NULL, NULL, NULL, '适合沙拉和轻食搭配', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 52 OR `name` = '生菜');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 53, '紫甘蓝', '蔬菜', NULL, 31, 1.4, 7.4, 0.2, 2.1, NULL, NULL, 15, NULL, NULL, NULL, '富含花青素和膳食纤维', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 53 OR `name` = '紫甘蓝');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 54, '芹菜', '蔬菜', NULL, 16, 0.8, 3.0, 0.2, 1.4, NULL, NULL, 15, NULL, NULL, NULL, '适合低盐低脂饮食', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 54 OR `name` = '芹菜');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 55, '冬瓜', '蔬菜', NULL, 11, 0.4, 2.6, 0.2, 0.7, NULL, NULL, 15, NULL, NULL, NULL, '清淡低热量，适合汤品', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 55 OR `name` = '冬瓜');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 56, '洋葱', '蔬菜', NULL, 39, 1.1, 9.3, 0.1, 1.7, NULL, NULL, 15, NULL, NULL, NULL, '常用增香蔬菜', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 56 OR `name` = '洋葱');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 57, '芦笋', '蔬菜', NULL, 20, 2.2, 3.9, 0.1, 2.1, NULL, NULL, 15, NULL, NULL, NULL, '高纤维低热量蔬菜', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 57 OR `name` = '芦笋');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 58, '蓝莓', '水果', NULL, 57, 0.7, 14.5, 0.3, 2.4, NULL, NULL, 53, NULL, NULL, NULL, '富含花青素的低热量水果', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 58 OR `name` = '蓝莓');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 59, '猕猴桃', '水果', NULL, 61, 1.1, 14.7, 0.5, 3.0, NULL, NULL, 52, NULL, NULL, NULL, '维生素 C 较丰富', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 59 OR `name` = '猕猴桃');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 60, '火龙果', '水果', NULL, 51, 1.1, 13.0, 0.2, 1.6, NULL, NULL, 48, NULL, NULL, NULL, '口感清爽，适合轻食搭配', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 60 OR `name` = '火龙果');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 61, '牛油果', '水果', NULL, 160, 2.0, 8.5, 14.7, 6.7, NULL, NULL, 10, NULL, NULL, NULL, '富含健康脂肪', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 61 OR `name` = '牛油果');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 62, '黑豆', '豆制品', NULL, 341, 21.6, 62.4, 1.4, 15.5, NULL, NULL, 30, NULL, NULL, NULL, '高蛋白高纤维豆类', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 62 OR `name` = '黑豆');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 63, '腐竹', '豆制品', NULL, 461, 44.6, 15.3, 21.7, 1.0, NULL, NULL, 30, NULL, NULL, NULL, '植物蛋白含量高', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 63 OR `name` = '腐竹');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 64, '无糖酸奶', '乳制品', NULL, 62, 3.5, 4.7, 3.2, 0.0, NULL, NULL, 35, 12, NULL, NULL, '适合控糖和轻食搭配', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 64 OR `name` = '无糖酸奶');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 65, '低脂牛奶', '乳制品', NULL, 46, 3.4, 4.8, 1.5, 0.0, NULL, NULL, 27, 6, NULL, NULL, '适合控制脂肪摄入', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 65 OR `name` = '低脂牛奶');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 66, '腰果', '坚果', NULL, 553, 18.2, 30.2, 43.8, 3.3, NULL, NULL, 22, NULL, NULL, NULL, '可少量作为加餐坚果', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 66 OR `name` = '腰果');

INSERT INTO `ingredient` (`id`, `name`, `category`, `sub_category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `sugar_per_100g`, `sodium_per_100g`, `gi_value`, `cholesterol_per_100g`, `vitamin_info`, `mineral_info`, `description`, `image_url`, `status`, `create_time`, `update_time`)
SELECT 67, '开心果', '坚果', NULL, 562, 20.3, 27.2, 45.4, 10.6, NULL, NULL, 15, NULL, NULL, NULL, '富含不饱和脂肪酸和膳食纤维', NULL, 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `ingredient` WHERE `id` = 67 OR `name` = '开心果');

-- ----------------------------
-- 基础食谱数据
-- ----------------------------
INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 101, '藜麦鸡胸能量碗', '高蛋白、低负担的轻食主餐，适合减脂和塑形期。', '午餐', '轻食', 20, '简单', 1, 420, 420, 33, 36, 12, 7, '["藜麦煮熟备用","鸡胸肉煎熟切片","生菜和紫甘蓝洗净切丝","将所有食材装碗后拌匀即可"]', '可加入少量黑胡椒提升风味。', NULL, NULL, NULL, 0, 1, 4.8, 0, 0, 0, '减脂人群、健身人群', '减肥减脂', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 101 OR `name` = '藜麦鸡胸能量碗');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 102, '三文鱼牛油果沙拉', '富含优质脂肪与蛋白质，适合控脂和心血管友好型饮食。', '晚餐', '轻食', 18, '简单', 1, 450, 450, 26, 18, 28, 8, '["三文鱼煎熟切块","牛油果切丁","生菜和蓝莓洗净备用","所有食材混合后即可食用"]', '控盐饮食可不加额外沙拉酱。', NULL, NULL, NULL, 0, 1, 4.9, 0, 0, 0, '控脂降脂、老年养生', '控脂降脂', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 102 OR `name` = '三文鱼牛油果沙拉');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 103, '无糖酸奶蓝莓燕麦杯', '适合早餐和加餐的低糖高纤组合。', '早餐', '轻食', 10, '简单', 1, 290, 290, 14, 34, 9, 6, '["无糖酸奶倒入杯中","加入燕麦","放入蓝莓和少量坚果","冷藏后口感更佳"]', '控糖人群可减少水果量。', NULL, NULL, NULL, 0, 1, 4.7, 0, 0, 0, '控糖饮食、维持体重', '控糖饮食', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 103 OR `name` = '无糖酸奶蓝莓燕麦杯');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 104, '金枪鱼全麦三明治', '高蛋白便捷早餐，适合上班族和塑形期。', '早餐', '西式', 12, '简单', 1, 360, 360, 28, 31, 11, 5, '["全麦面包烘热","金枪鱼沥干后铺在面包上","加入生菜和番茄片","夹好后对半切开"]', '可搭配低脂牛奶食用。', NULL, NULL, NULL, 0, 1, 4.8, 0, 0, 0, '增肌塑形、维持体重', '增肌塑形', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 104 OR `name` = '金枪鱼全麦三明治');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 105, '瘦牛肉藜麦饭', '高蛋白主餐，适合增肌和健康增重。', '午餐', '中式', 25, '中等', 1, 520, 520, 35, 42, 18, 6, '["藜麦煮熟备用","瘦牛肉切片快炒","加入洋葱和西兰花翻炒","与藜麦搭配装盘"]', '训练日可适当增加藜麦分量。', NULL, NULL, NULL, 0, 1, 4.9, 0, 0, 0, '增肌塑形、健康增重', '健康增重', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 105 OR `name` = '瘦牛肉藜麦饭');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 106, '南瓜小米粥', '温和易消化，适合老年养生和胃口较弱人群。', '早餐', '中式', 30, '简单', 1, 240, 240, 6, 46, 2, 3, '["南瓜去皮切块","小米淘洗干净","加入适量清水熬煮","煮至软糯即可"]', '可作为清淡早餐主食。', NULL, NULL, NULL, 0, 1, 4.6, 0, 0, 0, '老年养生、控脂降脂', '老年养生', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 106 OR `name` = '南瓜小米粥');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 107, '冬瓜虾仁汤', '低热量高蛋白汤品，适合作为晚餐配菜或控脂餐。', '晚餐', '中式', 15, '简单', 1, 180, 180, 24, 8, 3, 2, '["冬瓜切片","虾仁焯水备用","锅中加水煮开后放入冬瓜","加入虾仁煮熟调味即可"]', '控压饮食注意减少盐用量。', NULL, NULL, NULL, 0, 1, 4.7, 0, 0, 0, '控压低盐、减肥减脂', '控压低盐', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 107 OR `name` = '冬瓜虾仁汤');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 108, '芦笋鸡蛋卷', '营养均衡、制作快捷，适合作为早餐或加餐。', '早餐', '中式', 10, '简单', 1, 230, 230, 16, 9, 14, 2, '["鸡蛋打散","芦笋焯水切段","平底锅煎蛋皮","卷入芦笋后切段装盘"]', '可搭配低脂牛奶增强饱腹感。', NULL, NULL, NULL, 0, 1, 4.6, 0, 0, 0, '儿童成长、维持体重', '儿童成长', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 108 OR `name` = '芦笋鸡蛋卷');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 109, '黑豆豆腐营养碗', '植物蛋白丰富，适合素食和控脂人群。', '午餐', '轻食', 22, '中等', 1, 380, 380, 24, 29, 16, 8, '["黑豆提前煮熟","豆腐切块煎至微黄","生菜和紫甘蓝铺底","混合后即可食用"]', '可加少量柠檬汁提味。', NULL, NULL, NULL, 0, 1, 4.7, 0, 0, 0, '素食偏好、控脂降脂', '控脂降脂', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 109 OR `name` = '黑豆豆腐营养碗');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 110, '里脊肉土豆配芹菜', '中式家常组合，适合日常均衡饮食。', '晚餐', '中式', 20, '简单', 1, 410, 410, 27, 32, 14, 5, '["里脊肉切片腌制","土豆切块煮熟","芹菜切段快炒","三种食材组合装盘"]', '控糖阶段可减少土豆比例。', NULL, NULL, NULL, 0, 1, 4.5, 0, 0, 0, '维持体重、家庭饮食', '维持体重', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 110 OR `name` = '里脊肉土豆配芹菜');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 111, '牛油果酸奶水果碗', '清爽型早餐，适合孕妇营养和轻食需求。', '早餐', '轻食', 8, '简单', 1, 310, 310, 11, 26, 17, 7, '["将无糖酸奶倒入碗中","牛油果切块","加入蓝莓和猕猴桃","混合后即可食用"]', '孕妇营养可搭配全麦主食一起吃。', NULL, NULL, NULL, 0, 1, 4.8, 0, 0, 0, '孕妇营养、维持体重', '孕妇营养', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 111 OR `name` = '牛油果酸奶水果碗');

INSERT INTO `recipe` (`id`, `name`, `description`, `category`, `cuisine_type`, `cooking_time`, `difficulty`, `servings`, `total_calories`, `calories_per_serving`, `protein`, `carbs`, `fat`, `fiber`, `instructions`, `tips`, `image_url`, `video_url`, `creator_id`, `is_custom`, `is_public`, `score`, `score_count`, `view_count`, `collect_count`, `suitable_for`, `goal_type`, `status`, `create_time`, `update_time`)
SELECT 112, '三文鱼藜麦温沙拉', '兼顾蛋白质和优质脂肪，适合健康增重和塑形。', '午餐', '轻食', 20, '中等', 1, 470, 470, 30, 29, 24, 6, '["藜麦煮熟保温","三文鱼煎熟切块","生菜和芦笋焯水","混合食材后趁温热食用"]', '可作为训练后恢复餐。', NULL, NULL, NULL, 0, 1, 4.9, 0, 0, 0, '增肌塑形、健康增重', '增肌塑形', 1, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM `recipe` WHERE `id` = 112 OR `name` = '三文鱼藜麦温沙拉');

-- ----------------------------
-- 食谱与食材关联
-- ----------------------------
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 50, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '藜麦鸡胸能量碗' AND i.name = '藜麦'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 120, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '藜麦鸡胸能量碗' AND i.name = '鸡胸肉'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 60, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '藜麦鸡胸能量碗' AND i.name = '生菜'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 40, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '藜麦鸡胸能量碗' AND i.name = '紫甘蓝'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 120, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '三文鱼牛油果沙拉' AND i.name = '三文鱼'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 60, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '三文鱼牛油果沙拉' AND i.name = '牛油果'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 80, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '三文鱼牛油果沙拉' AND i.name = '生菜'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 30, 'g', 1, '点缀' FROM `recipe` r, `ingredient` i
WHERE r.name = '三文鱼牛油果沙拉' AND i.name = '蓝莓'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 150, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '无糖酸奶蓝莓燕麦杯' AND i.name = '无糖酸奶'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 35, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '无糖酸奶蓝莓燕麦杯' AND i.name = '燕麦'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 50, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '无糖酸奶蓝莓燕麦杯' AND i.name = '蓝莓'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 10, 'g', 1, '少量添加' FROM `recipe` r, `ingredient` i
WHERE r.name = '无糖酸奶蓝莓燕麦杯' AND i.name = '腰果'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 80, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '金枪鱼全麦三明治' AND i.name = '金枪鱼'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 60, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '金枪鱼全麦三明治' AND i.name = '全麦面包'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 40, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '金枪鱼全麦三明治' AND i.name = '生菜'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 30, 'g', 1, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '金枪鱼全麦三明治' AND i.name = '番茄'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 60, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '瘦牛肉藜麦饭' AND i.name = '藜麦'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 120, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '瘦牛肉藜麦饭' AND i.name = '瘦牛肉'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 40, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '瘦牛肉藜麦饭' AND i.name = '洋葱'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 60, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '瘦牛肉藜麦饭' AND i.name = '西兰花'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 40, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '南瓜小米粥' AND i.name = '南瓜'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 35, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '南瓜小米粥' AND i.name = '小米'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 120, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '冬瓜虾仁汤' AND i.name = '冬瓜'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 80, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '冬瓜虾仁汤' AND i.name = '虾'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 80, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '芦笋鸡蛋卷' AND i.name = '芦笋'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 100, 'g', 0, '约两个鸡蛋' FROM `recipe` r, `ingredient` i
WHERE r.name = '芦笋鸡蛋卷' AND i.name = '鸡蛋'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 80, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '黑豆豆腐营养碗' AND i.name = '黑豆'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 120, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '黑豆豆腐营养碗' AND i.name = '豆腐'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 60, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '黑豆豆腐营养碗' AND i.name = '生菜'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 40, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '黑豆豆腐营养碗' AND i.name = '紫甘蓝'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 120, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '里脊肉土豆配芹菜' AND i.name = '里脊肉'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 100, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '里脊肉土豆配芹菜' AND i.name = '土豆'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 80, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '里脊肉土豆配芹菜' AND i.name = '芹菜'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 120, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '牛油果酸奶水果碗' AND i.name = '无糖酸奶'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 50, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '牛油果酸奶水果碗' AND i.name = '牛油果'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 40, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '牛油果酸奶水果碗' AND i.name = '蓝莓'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 60, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '牛油果酸奶水果碗' AND i.name = '猕猴桃'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 50, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '三文鱼藜麦温沙拉' AND i.name = '藜麦'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 120, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '三文鱼藜麦温沙拉' AND i.name = '三文鱼'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 60, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '三文鱼藜麦温沙拉' AND i.name = '生菜'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);
INSERT INTO `recipe_ingredient` (`recipe_id`, `ingredient_id`, `quantity`, `unit`, `is_optional`, `notes`)
SELECT r.id, i.id, 60, 'g', 0, NULL FROM `recipe` r, `ingredient` i
WHERE r.name = '三文鱼藜麦温沙拉' AND i.name = '芦笋'
AND NOT EXISTS (SELECT 1 FROM `recipe_ingredient` WHERE `recipe_id` = r.id AND `ingredient_id` = i.id);

SET FOREIGN_KEY_CHECKS = 1;
