/*
 Navicat Premium Data Transfer

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 50744
 Source Host           : localhost:3306
 Source Schema         : health_diet

 Target Server Type    : MySQL
 Target Server Version : 50744
 File Encoding         : 65001

 Date: 22/03/2026 23:49:46
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for ai_recommend_log
-- ----------------------------
DROP TABLE IF EXISTS `ai_recommend_log`;
CREATE TABLE `ai_recommend_log`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `recommend_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '推荐类型: recipe/ingredient/article',
  `input_data` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '输入数据(JSON)',
  `recommend_result` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '推荐结果(JSON)',
  `algorithm` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '使用算法',
  `score` double NULL DEFAULT NULL COMMENT '推荐评分',
  `is_accepted` tinyint(4) NULL DEFAULT 0 COMMENT '是否采纳',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `ai_recommend_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_recommend_log
-- ----------------------------

-- ----------------------------
-- Table structure for diet_goal
-- ----------------------------
DROP TABLE IF EXISTS `diet_goal`;
CREATE TABLE `diet_goal`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `goal_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标类型: 减肥/增肌/控糖/维持健康',
  `target_weight` double NULL DEFAULT NULL COMMENT '目标体重(kg)',
  `target_calories` double NOT NULL COMMENT '目标每日热量(kcal)',
  `protein_ratio` double NULL DEFAULT NULL COMMENT '蛋白质占比(%)',
  `carbs_ratio` double NULL DEFAULT NULL COMMENT '碳水化合物占比(%)',
  `fat_ratio` double NULL DEFAULT NULL COMMENT '脂肪占比(%)',
  `protein_target` double NULL DEFAULT NULL COMMENT '蛋白质目标(g)',
  `carbs_target` double NULL DEFAULT NULL COMMENT '碳水目标(g)',
  `fat_target` double NULL DEFAULT NULL COMMENT '脂肪目标(g)',
  `water_target` int(11) NULL DEFAULT NULL COMMENT '每日饮水目标(ml)',
  `status` tinyint(4) NULL DEFAULT 1 COMMENT '目标状态: 0-暂停, 1-进行中, 2-已完成',
  `start_date` date NOT NULL,
  `end_date` date NULL DEFAULT NULL COMMENT '目标结束日期',
  `reminder_enabled` tinyint(4) NULL DEFAULT 1 COMMENT '是否开启提醒',
  `reminder_time` time NULL DEFAULT NULL COMMENT '每日提醒时间',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `diet_goal_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of diet_goal
-- ----------------------------
INSERT INTO `diet_goal` VALUES (1, 1, 'healthy_weight_gain', 60, 2496, 24, 48, 28, 150, 300, 78, 2600, 1, '2026-03-11', '2026-08-11', 1, '18:21:00', '2026-03-10 22:36:26', '2026-03-10 22:36:26');
INSERT INTO `diet_goal` VALUES (2, 2, 'muscle_gain', NULL, 2711, 15, 45, 25, NULL, NULL, NULL, NULL, 1, '2026-03-16', '2026-06-19', 1, NULL, '2026-03-15 22:45:53', '2026-03-15 22:45:53');

-- ----------------------------
-- Table structure for diet_record
-- ----------------------------
DROP TABLE IF EXISTS `diet_record`;
CREATE TABLE `diet_record`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `record_date` date NOT NULL,
  `meal_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '餐次: breakfast/lunch/dinner/snack',
  `meal_time` time NULL DEFAULT NULL COMMENT '实际用餐时间',
  `total_calories` double NULL DEFAULT NULL COMMENT '总热量(kcal)',
  `total_protein` double NULL DEFAULT NULL COMMENT '总蛋白质(g)',
  `total_carbs` double NULL DEFAULT NULL COMMENT '总碳水(g)',
  `total_fat` double NULL DEFAULT NULL COMMENT '总脂肪(g)',
  `total_fiber` double NULL DEFAULT NULL COMMENT '总膳食纤维(g)',
  `water_intake` int(11) NULL DEFAULT NULL COMMENT '饮水量(ml)',
  `notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '备注',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `diet_record_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of diet_record
-- ----------------------------

-- ----------------------------
-- Table structure for diet_record_detail
-- ----------------------------
DROP TABLE IF EXISTS `diet_record_detail`;
CREATE TABLE `diet_record_detail`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `record_id` bigint(20) NOT NULL,
  `ingredient_id` bigint(20) NULL DEFAULT NULL COMMENT '食材ID',
  `food_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '食物名称',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '食物分类',
  `quantity` double NOT NULL COMMENT '用量',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '单位',
  `calories` double NULL DEFAULT NULL COMMENT '热量(kcal)',
  `protein` double NULL DEFAULT NULL COMMENT '蛋白质(g)',
  `carbs` double NULL DEFAULT NULL COMMENT '碳水化合物(g)',
  `fat` double NULL DEFAULT NULL COMMENT '脂肪(g)',
  `fiber` double NULL DEFAULT NULL COMMENT '膳食纤维(g)',
  `recipe_id` bigint(20) NULL DEFAULT NULL COMMENT '来源食谱ID',
  `is_custom` tinyint(4) NULL DEFAULT 0 COMMENT '是否自定义食材',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `record_id`(`record_id`) USING BTREE,
  INDEX `ingredient_id`(`ingredient_id`) USING BTREE,
  INDEX `recipe_id`(`recipe_id`) USING BTREE,
  CONSTRAINT `diet_record_detail_ibfk_1` FOREIGN KEY (`record_id`) REFERENCES `diet_record` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `diet_record_detail_ibfk_2` FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `diet_record_detail_ibfk_3` FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of diet_record_detail
-- ----------------------------

-- ----------------------------
-- Table structure for exercise_record
-- ----------------------------
DROP TABLE IF EXISTS `exercise_record`;
CREATE TABLE `exercise_record`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `exercise_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '运动类型',
  `duration` int(11) NOT NULL COMMENT '运动时长(分钟)',
  `calories_burned` double NULL DEFAULT NULL COMMENT '消耗热量(kcal)',
  `intensity` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '运动强度: low/medium/high',
  `record_date` date NOT NULL,
  `notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '备注',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `exercise_record_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of exercise_record
-- ----------------------------

-- ----------------------------
-- Table structure for health_article
-- ----------------------------
DROP TABLE IF EXISTS `health_article`;
CREATE TABLE `health_article`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `summary` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '文章摘要',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `cover_image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '封面图',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分类: 饮食指南/营养知识/减肥指南/增肌指南/饮食误区',
  `tags` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '标签(JSON数组)',
  `author` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '作者',
  `suitable_for` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '适宜人群',
  `goal_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '关联目标: 减肥/增肌/控糖/通用',
  `read_count` int(11) NULL DEFAULT 0,
  `like_count` int(11) NULL DEFAULT 0,
  `share_count` int(11) NULL DEFAULT 0,
  `publish_date` date NULL DEFAULT NULL,
  `status` tinyint(4) NULL DEFAULT 1 COMMENT '状态: 0-草稿, 1-已发布',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of health_article
-- ----------------------------
INSERT INTO `health_article` VALUES (1, '控糖饮食指南', '控糖饮食对于预防糖尿病和维持健康体重非常重要', '控糖饮食对于预防糖尿病和维持健康体重非常重要。建议减少高GI食物的摄入，选择低GI食物，如全谷物、蔬菜等。同时要注意控制每日总糖摄入量，包括蔗糖、果糖等添加糖。', NULL, '饮食指南', '[\"控糖\", \"糖尿病\", \"健康\"]', '营养师小王', '糖尿病患者、肥胖人群', '控糖', 1, 0, 0, '2024-01-01', 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `health_article` VALUES (2, '蛋白质摄入的重要性', '蛋白质是身体的重要组成部分，对于肌肉生长和修复至关重要', '蛋白质是身体的重要组成部分，对于肌肉生长和修复至关重要。建议成年人每公斤体重摄入1-1.2克蛋白质。优质蛋白质来源包括鸡胸肉、鱼、蛋、奶制品和豆制品。', NULL, '营养知识', '[\"蛋白质\", \"肌肉\", \"健康\"]', '营养师小李', '健身人群、增肌人群', '增肌', 0, 0, 0, '2024-01-02', 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `health_article` VALUES (3, '健康减肥的正确方法', '健康减肥需要合理控制饮食并结合适当的运动', '健康减肥需要合理控制饮食并结合适当的运动。建议每日热量摄入控制在基础代谢率的1.2-1.5倍，同时保证营养均衡。运动方面建议每周进行150分钟中等强度有氧运动。', NULL, '减肥指南', '[\"减肥\", \"健康\", \"运动\"]', '健身教练小张', '肥胖人群', '减肥', 0, 0, 0, '2024-01-03', 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `health_article` VALUES (4, '增肌饮食策略', '增肌需要足够的蛋白质和热量摄入，同时结合力量训练', '增肌需要足够的蛋白质和热量摄入，同时结合力量训练。建议每公斤体重摄入1.6-2.2克蛋白质，在训练后30分钟内补充蛋白质效果最佳。碳水化合物是训练能量的主要来源，也要保证充足摄入。', NULL, '增肌指南', '[\"增肌\", \"蛋白质\", \"力量训练\"]', '健身教练小王', '健身人群', '增肌', 1, 0, 0, '2024-01-04', 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `health_article` VALUES (5, '饮食误区大揭秘', '常见的饮食误区包括过度节食、偏食等，这些都会影响健康', '常见的饮食误区包括：1.过度节食导致基础代谢下降；2.只吃蔬菜水果导致蛋白质缺乏；3.不吃主食导致碳水不足；4.迷信减肥药和减肥产品。正确做法是均衡饮食，适量运动。', NULL, '饮食误区', '[\"误区\", \"健康\", \"饮食\"]', '营养师小陈', '所有人群', '通用', 0, 0, 0, '2024-01-05', 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `health_article` VALUES (6, '高血压饮食建议', '高血压患者应该如何调整饮食结构', '高血压患者应该：1.限制钠盐摄入，每日不超过5克；2.增加钾的摄入，多吃蔬菜水果；3.控制脂肪摄入，减少动物内脏；4.戒烟限酒；5.保持规律作息。', NULL, '饮食指南', '[\"高血压\", \"心血管\", \"饮食\"]', '营养师小李', '高血压人群', '通用', 0, 0, 0, '2024-01-06', 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `health_article` VALUES (7, '如何科学补水', '科学补水对于维持身体健康至关重要', '科学补水建议：1.每日饮水1500-2000ml；2.运动前半小时补充300ml水；3.运动中每15-20分钟补充100-150ml；4.运动后根据体重丢失量补充；5.养成主动喝水习惯，不要等口渴再喝。', NULL, '营养知识', '[\"补水\", \"健康\", \"饮水\"]', '营养师小王', '所有人群', '通用', 0, 0, 0, '2024-01-07', 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');

-- ----------------------------
-- Table structure for health_info
-- ----------------------------
DROP TABLE IF EXISTS `health_info`;
CREATE TABLE `health_info`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `age` int(11) NULL DEFAULT NULL COMMENT '年龄',
  `gender` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '性别: 男/女',
  `height` double NULL DEFAULT NULL COMMENT '身高(cm)',
  `weight` double NULL DEFAULT NULL COMMENT '体重(kg)',
  `bmi` double NULL DEFAULT NULL COMMENT 'BMI指数',
  `bmr` double NULL DEFAULT NULL COMMENT '基础代谢率(kcal)',
  `blood_pressure` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '血压',
  `blood_sugar` double NULL DEFAULT NULL COMMENT '血糖(mmol/L)',
  `activity_level` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '活动水平: sedentary/lightly_active/moderately_active/very_active/extra_active',
  `exercise_duration` int(11) NULL DEFAULT NULL COMMENT '每日运动时长(分钟)',
  `exercise_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '运动类型',
  `allergies` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '过敏食物',
  `chronic_diseases` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '慢性疾病',
  `health_condition` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '健康状况描述',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `health_info_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of health_info
-- ----------------------------
INSERT INTO `health_info` VALUES (1, 1, 22, '男', 170, 50, 17.301038062283737, 1449, '120/80', 10, 'lightly_active', 20, '骑行', '', '', '', '2026-03-10 20:28:28', '2026-03-10 20:28:28');
INSERT INTO `health_info` VALUES (2, 2, 25, '男', 175, 60, 19.591836734693878, NULL, '120/80', 5, 'moderately_active', 40, '跑步', '', '', '', '2026-03-15 22:35:05', '2026-03-15 22:35:05');
INSERT INTO `health_info` VALUES (3, 3, 24, '男', 175, 65, 21.224489795918366, NULL, '120/80', 5, 'sedentary', 10, '其他', '', '', '', '2026-03-18 00:07:31', '2026-03-18 00:07:31');

-- ----------------------------
-- Table structure for health_info_history
-- ----------------------------
DROP TABLE IF EXISTS `health_info_history`;
CREATE TABLE `health_info_history`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `weight` double NULL DEFAULT NULL COMMENT '体重(kg)',
  `bmi` double NULL DEFAULT NULL COMMENT 'BMI指数',
  `exercise_duration` int(11) NULL DEFAULT NULL COMMENT '运动时长(分钟)',
  `record_date` date NOT NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `health_info_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of health_info_history
-- ----------------------------
INSERT INTO `health_info_history` VALUES (1, 1, 45, 15.570934256055365, 20, '2026-03-22', '2026-03-22 15:30:23');
INSERT INTO `health_info_history` VALUES (2, 1, 45.2, 15.640138408304502, 20, '2026-03-22', '2026-03-22 15:30:35');
INSERT INTO `health_info_history` VALUES (3, 1, 45.5, 15.743944636678203, 20, '2026-03-22', '2026-03-22 15:59:55');
INSERT INTO `health_info_history` VALUES (4, 1, 46, 15.91695501730104, 20, '2026-03-22', '2026-03-22 16:00:05');
INSERT INTO `health_info_history` VALUES (5, 1, 46.5, 16.089965397923876, 20, '2026-03-22', '2026-03-22 20:28:41');
INSERT INTO `health_info_history` VALUES (6, 1, 48, 16.60899653979239, 20, '2026-03-22', '2026-03-22 20:46:49');
INSERT INTO `health_info_history` VALUES (7, 1, 50, 17.301038062283737, 20, '2026-03-22', '2026-03-22 21:06:40');

-- ----------------------------
-- Table structure for health_record
-- ----------------------------
DROP TABLE IF EXISTS `health_record`;
CREATE TABLE `health_record`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '记录ID，主键自增',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID，关联sys_user表',
  `record_date` date NOT NULL COMMENT '记录日期',
  `weight` decimal(5, 2) NULL DEFAULT NULL COMMENT '体重，单位：公斤(kg)',
  `exercise_duration` int(11) NULL DEFAULT 0 COMMENT '运动时长，单位：分钟',
  `sleep_hours` decimal(3, 1) NULL DEFAULT NULL COMMENT '睡眠时长，单位：小时',
  `bmi` decimal(4, 1) NULL DEFAULT NULL COMMENT 'BMI指数，体重(kg)/身高(m)²',
  `bmr` int(11) NULL DEFAULT NULL COMMENT '基础代谢率，单位：kcal/天',
  `water_intake` int(11) NULL DEFAULT 0 COMMENT '饮水量，单位：毫升(ml)',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_date`(`user_id`, `record_date`) USING BTREE,
  INDEX `idx_record_date`(`record_date`) USING BTREE,
  CONSTRAINT `health_record_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '健康记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of health_record
-- ----------------------------

-- ----------------------------
-- Table structure for ingredient
-- ----------------------------
DROP TABLE IF EXISTS `ingredient`;
CREATE TABLE `ingredient`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '食材名称',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分类: 主食/蔬菜/肉类/蛋类/乳制品/水果/坚果/豆制品',
  `sub_category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '子分类',
  `calories_per_100g` double NOT NULL COMMENT '热量(kcal/100g)',
  `protein_per_100g` double NULL DEFAULT NULL COMMENT '蛋白质(g/100g)',
  `carbs_per_100g` double NULL DEFAULT NULL COMMENT '碳水化合物(g/100g)',
  `fat_per_100g` double NULL DEFAULT NULL COMMENT '脂肪(g/100g)',
  `fiber_per_100g` double NULL DEFAULT NULL COMMENT '膳食纤维(g/100g)',
  `sugar_per_100g` double NULL DEFAULT NULL COMMENT '糖分(g/100g)',
  `sodium_per_100g` double NULL DEFAULT NULL COMMENT '钠(mg/100g)',
  `gi_value` int(11) NULL DEFAULT NULL COMMENT '升糖指数(GI)',
  `cholesterol_per_100g` double NULL DEFAULT NULL COMMENT '胆固醇(mg/100g)',
  `vitamin_info` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '维生素信息(JSON)',
  `mineral_info` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '矿物质信息(JSON)',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '食材描述',
  `image_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '图片URL',
  `status` tinyint(4) NULL DEFAULT 1 COMMENT '状态: 0-禁用, 1-正常',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 43 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ingredient
-- ----------------------------
INSERT INTO `ingredient` VALUES (1, '米饭', '主食', NULL, 116, 2.6, 25.6, 0.3, 0.4, NULL, NULL, 73, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (2, '面条', '主食', NULL, 137, 3.6, 28.9, 0.7, 0.9, NULL, NULL, 55, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (3, '全麦面包', '主食', NULL, 247, 13, 41, 3.4, 7, NULL, NULL, 50, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (4, '燕麦', '主食', NULL, 389, 17, 66, 7, 10, NULL, NULL, 55, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (5, '糙米', '主食', NULL, 111, 2.6, 23, 0.9, 1.8, NULL, NULL, 68, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (6, '红薯', '主食', NULL, 86, 1.6, 20, 0.1, 3, NULL, NULL, 54, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (7, '玉米', '主食', NULL, 96, 3.3, 21, 1.4, 2.7, NULL, NULL, 52, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (8, '鸡蛋', '蛋类', NULL, 155, 13, 1.1, 10.6, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (9, '鸭蛋', '蛋类', NULL, 180, 13, 3.1, 14, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (10, '鹌鹑蛋', '蛋类', NULL, 158, 13, 0.4, 11, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (11, '牛奶', '乳制品', NULL, 42, 3.4, 5, 1, 0, NULL, NULL, 27, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (12, '酸奶', '乳制品', NULL, 72, 2.5, 10, 2.7, 0, NULL, NULL, 48, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (13, '奶酪', '乳制品', NULL, 328, 25, 3.5, 23, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (14, '豆浆', '乳制品', NULL, 31, 3.3, 1.2, 1.7, 0.4, NULL, NULL, 34, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (15, '鸡肉', '肉类', NULL, 165, 31, 0, 3.6, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (16, '鸡胸肉', '肉类', NULL, 165, 31, 0, 3.6, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (17, '牛肉', '肉类', NULL, 250, 26, 0, 17, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (18, '猪肉', '肉类', NULL, 337, 13.2, 2.4, 30.8, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (19, '鱼肉', '肉类', NULL, 124, 20.4, 0, 4.1, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (20, '虾', '肉类', NULL, 99, 24, 0.2, 0.3, 0, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (21, '西红柿', '蔬菜', NULL, 18, 0.9, 3.9, 0.2, 1.2, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (22, '黄瓜', '蔬菜', NULL, 15, 0.8, 3.6, 0.1, 0.5, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (23, '白菜', '蔬菜', NULL, 17, 1.5, 3.2, 0.1, 1, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (24, '胡萝卜', '蔬菜', NULL, 41, 0.9, 9.6, 0.2, 2.8, NULL, NULL, 39, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (25, '菠菜', '蔬菜', NULL, 23, 2.9, 3.6, 0.4, 2.2, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (26, '西兰花', '蔬菜', NULL, 34, 2.8, 7, 0.4, 2.6, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (27, '茄子', '蔬菜', NULL, 25, 1.1, 6, 0.2, 1.2, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (28, '青椒', '蔬菜', NULL, 20, 0.9, 4.6, 0.2, 1.7, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (29, '蘑菇', '蔬菜', NULL, 22, 3.1, 3.3, 0.3, 1, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (30, '番茄', '蔬菜', NULL, 18, 0.9, 3.9, 0.2, 1.2, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (31, '苹果', '水果', NULL, 52, 0.3, 13.8, 0.2, 2.4, NULL, NULL, 36, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (32, '香蕉', '水果', NULL, 89, 1.1, 22.8, 0.3, 2.6, NULL, NULL, 51, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (33, '橙子', '水果', NULL, 47, 0.9, 11.8, 0.1, 2.4, NULL, NULL, 43, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (34, '葡萄', '水果', NULL, 69, 0.7, 18, 0.2, 1, NULL, NULL, 56, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (35, '西瓜', '水果', NULL, 30, 0.6, 8, 0.2, 0.4, NULL, NULL, 72, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (36, '草莓', '水果', NULL, 32, 0.7, 7.7, 0.3, 2, NULL, NULL, 40, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (37, '梨', '水果', NULL, 57, 0.4, 14, 0.1, 3.1, NULL, NULL, 38, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (38, '豆腐', '豆制品', NULL, 76, 8, 1.9, 4.8, 0.3, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (39, '黄豆', '豆制品', NULL, 390, 36, 34, 16, 15, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (40, '花生', '坚果', NULL, 567, 26, 16, 49, 8.5, NULL, NULL, 14, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (41, '核桃', '坚果', NULL, 654, 15, 14, 65, 6.7, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (42, '杏仁', '坚果', NULL, 579, 21, 22, 50, 12, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-08 17:04:36', '2026-03-08 17:04:36');
INSERT INTO `ingredient` VALUES (43, '藜麦', '主食', NULL, 120, 4.4, 21.3, 1.9, 2.8, NULL, NULL, 53, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (44, '土豆', '主食', NULL, 77, 2, 17.2, 0.1, 2.2, NULL, NULL, 62, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (45, '南瓜', '主食', NULL, 26, 1, 6.5, 0.1, 0.5, NULL, NULL, 64, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (46, '小米', '主食', NULL, 361, 9, 75, 1.5, 1.6, NULL, NULL, 71, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (47, '馒头', '主食', NULL, 223, 7, 47, 1.1, 1.3, NULL, NULL, 88, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (48, '三文鱼', '肉类', NULL, 208, 20, 0, 13, 0, NULL, NULL, 0, 55, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (49, '金枪鱼', '肉类', NULL, 132, 28, 0, 1.3, 0, NULL, NULL, 0, 47, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (50, '瘦牛肉', '肉类', NULL, 155, 20.2, 0, 7.9, 0, NULL, NULL, 0, 58, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (51, '里脊肉', '肉类', NULL, 143, 20.5, 0, 6.2, 0, NULL, NULL, 0, 62, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (52, '生菜', '蔬菜', NULL, 16, 1.2, 2.1, 0.2, 1.1, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (53, '紫甘蓝', '蔬菜', NULL, 31, 1.4, 7.4, 0.2, 2.1, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (54, '芹菜', '蔬菜', NULL, 16, 0.8, 3.4, 0.2, 1.8, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (55, '冬瓜', '蔬菜', NULL, 12, 0.4, 2.6, 0.2, 0.7, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (56, '洋葱', '蔬菜', NULL, 40, 1.1, 9.3, 0.1, 1.7, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (57, '芦笋', '蔬菜', NULL, 20, 2.2, 3.9, 0.1, 2.1, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (58, '蓝莓', '水果', NULL, 57, 0.7, 14.5, 0.3, 2.4, NULL, NULL, 53, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (59, '猕猴桃', '水果', NULL, 61, 1.1, 14.7, 0.5, 3, NULL, NULL, 52, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (60, '火龙果', '水果', NULL, 51, 1.1, 13.3, 0.2, 1.6, NULL, NULL, 48, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (61, '牛油果', '水果', NULL, 160, 2, 8.5, 14.7, 6.7, NULL, NULL, 10, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (62, '黑豆', '豆制品', NULL, 341, 21.6, 33.7, 15, 10.2, NULL, NULL, 30, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (63, '腐竹', '豆制品', NULL, 461, 44.6, 15.3, 21.7, 1.3, NULL, NULL, 13, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (64, '无糖酸奶', '乳制品', NULL, 56, 4.8, 5.2, 1.5, 0, 4.5, 52, 36, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (65, '低脂牛奶', '乳制品', NULL, 43, 3.4, 5, 1.2, 0, 5, 45, 30, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (66, '腰果', '坚果', NULL, 553, 18.2, 30.2, 43.8, 3.3, NULL, NULL, 22, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');
INSERT INTO `ingredient` VALUES (67, '开心果', '坚果', NULL, 562, 20.3, 27.5, 45.4, 10.6, NULL, NULL, 15, NULL, NULL, NULL, NULL, NULL, 1, '2026-03-23 10:00:00', '2026-03-23 10:00:00');

-- ----------------------------
-- Table structure for ingredient_substitute
-- ----------------------------
DROP TABLE IF EXISTS `ingredient_substitute`;
CREATE TABLE `ingredient_substitute`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `ingredient_id` bigint(20) NOT NULL COMMENT '原食材ID',
  `substitute_id` bigint(20) NOT NULL COMMENT '替代食材ID',
  `reason` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '替代原因',
  `nutrition_match_rate` double NULL DEFAULT NULL COMMENT '营养匹配度(%)',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ingredient_id`(`ingredient_id`) USING BTREE,
  INDEX `substitute_id`(`substitute_id`) USING BTREE,
  CONSTRAINT `ingredient_substitute_ibfk_1` FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `ingredient_substitute_ibfk_2` FOREIGN KEY (`substitute_id`) REFERENCES `ingredient` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ingredient_substitute
-- ----------------------------

-- ----------------------------
-- Table structure for notification
-- ----------------------------
DROP TABLE IF EXISTS `notification`;
CREATE TABLE `notification`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息类型: diet_reminder/goal_achieved/article_recommend/warning/system',
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `related_id` bigint(20) NULL DEFAULT NULL COMMENT '关联ID',
  `related_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '关联类型: recipe/article/diet_record',
  `is_read` tinyint(4) NULL DEFAULT 0 COMMENT '是否已读',
  `read_time` datetime NULL DEFAULT NULL,
  `send_time` datetime NULL DEFAULT NULL COMMENT '发送时间',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of notification
-- ----------------------------

-- ----------------------------
-- Table structure for recipe
-- ----------------------------
DROP TABLE IF EXISTS `recipe`;
CREATE TABLE `recipe`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '食谱名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '食谱描述',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '食谱分类: 早餐/午餐/晚餐/加餐',
  `cuisine_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '菜系',
  `cooking_time` int(11) NULL DEFAULT NULL COMMENT '烹饪时间(分钟)',
  `difficulty` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '难度: 简单/中等/困难',
  `servings` int(11) NULL DEFAULT 1 COMMENT '份数',
  `total_calories` double NULL DEFAULT NULL COMMENT '总热量(kcal)',
  `calories_per_serving` double NULL DEFAULT NULL COMMENT '每份热量(kcal)',
  `protein` double NULL DEFAULT NULL COMMENT '蛋白质(g)',
  `carbs` double NULL DEFAULT NULL COMMENT '碳水化合物(g)',
  `fat` double NULL DEFAULT NULL COMMENT '脂肪(g)',
  `fiber` double NULL DEFAULT NULL COMMENT '膳食纤维(g)',
  `instructions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '烹饪步骤(JSON数组)',
  `tips` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '烹饪小贴士',
  `image_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '图片URL',
  `video_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '视频教程URL',
  `creator_id` bigint(20) NULL DEFAULT NULL COMMENT '创建者ID',
  `is_custom` tinyint(4) NULL DEFAULT 0 COMMENT '是否用户自定义: 0-系统, 1-自定义',
  `is_public` tinyint(4) NULL DEFAULT 1 COMMENT '是否公开',
  `score` double NULL DEFAULT 5 COMMENT '评分',
  `score_count` int(11) NULL DEFAULT 0 COMMENT '评分次数',
  `view_count` int(11) NULL DEFAULT 0 COMMENT '浏览次数',
  `collect_count` int(11) NULL DEFAULT 0 COMMENT '收藏次数',
  `suitable_for` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '适宜人群',
  `goal_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '适宜目标: 减肥/增肌/控糖/通用',
  `status` tinyint(4) NULL DEFAULT 1 COMMENT '状态: 0-下架, 1-上架',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `creator_id`(`creator_id`) USING BTREE,
  CONSTRAINT `recipe_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of recipe
-- ----------------------------

-- ----------------------------
-- Table structure for recipe_ingredient
-- ----------------------------
DROP TABLE IF EXISTS `recipe_ingredient`;
CREATE TABLE `recipe_ingredient`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `recipe_id` bigint(20) NOT NULL,
  `ingredient_id` bigint(20) NOT NULL,
  `quantity` double NOT NULL COMMENT '用量',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '单位: g/ml/个/勺',
  `is_optional` tinyint(4) NULL DEFAULT 0 COMMENT '是否可选',
  `notes` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `recipe_id`(`recipe_id`) USING BTREE,
  INDEX `ingredient_id`(`ingredient_id`) USING BTREE,
  CONSTRAINT `recipe_ingredient_ibfk_1` FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `recipe_ingredient_ibfk_2` FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of recipe_ingredient
-- ----------------------------

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `avatar` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '头像URL或本地图片数据',
  `status` tinyint(4) NULL DEFAULT 1 COMMENT '账号状态: 0-禁用, 1-正常',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username`) USING BTREE,
  UNIQUE INDEX `email`(`email`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user
-- ----------------------------
INSERT INTO `user` VALUES (1, '刘俊豪', '$2a$10$QQmxV20DzWaRkxwmyoYmCOsK8HLWduCDfAxUfkhdagdznYhDiBokS', '2311697186@qq.com', '17840529449', NULL, 1, '2026-03-10 20:27:38', '2026-03-10 20:27:38');
INSERT INTO `user` VALUES (2, '张三', '$2a$10$rs0vAkSKgVKMWWWSYojuje4dho5mfroXlf9HhF.93/MFFPqXSGvt2', '123456@qq.com', '19330406783', NULL, 1, '2026-03-15 22:34:49', '2026-03-15 22:34:49');
INSERT INTO `user` VALUES (3, '管理员', '$2a$10$e3hGOVm.MysyEXTZF1f9buOUSVNFAwaXs7IYipFHsnCBRqP3II1Fm', 'admin@qq.com', '15432145678', NULL, 1, '2026-03-18 00:07:16', '2026-03-18 00:07:16');

-- ----------------------------
-- Table structure for user_article_collect
-- ----------------------------
DROP TABLE IF EXISTS `user_article_collect`;
CREATE TABLE `user_article_collect`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `article_id` bigint(20) NOT NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_article`(`user_id`, `article_id`) USING BTREE,
  INDEX `article_id`(`article_id`) USING BTREE,
  CONSTRAINT `user_article_collect_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `user_article_collect_ibfk_2` FOREIGN KEY (`article_id`) REFERENCES `health_article` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_article_collect
-- ----------------------------

-- ----------------------------
-- Table structure for user_diet_preference
-- ----------------------------
DROP TABLE IF EXISTS `user_diet_preference`;
CREATE TABLE `user_diet_preference`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `diet_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '饮食类型: 素食、低碳水、清淡、麻辣等',
  `allergies` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '过敏原',
  `dislikes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '不喜欢吃的食物',
  `favorites` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '喜欢吃的食物',
  `meal_frequency` int(11) NULL DEFAULT 3 COMMENT '每日餐次',
  `snack_preference` tinyint(4) NULL DEFAULT 1 COMMENT '是否吃零食: 0-否, 1-是',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `user_diet_preference_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_diet_preference
-- ----------------------------

-- ----------------------------
-- Table structure for user_read_record
-- ----------------------------
DROP TABLE IF EXISTS `user_read_record`;
CREATE TABLE `user_read_record`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `article_id` bigint(20) NOT NULL,
  `read_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `read_duration` int(11) NULL DEFAULT NULL COMMENT '阅读时长(秒)',
  `is_finished` tinyint(4) NULL DEFAULT 0 COMMENT '是否读完',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  INDEX `article_id`(`article_id`) USING BTREE,
  CONSTRAINT `user_read_record_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `user_read_record_ibfk_2` FOREIGN KEY (`article_id`) REFERENCES `health_article` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_read_record
-- ----------------------------

-- ----------------------------
-- Table structure for user_recipe_collect
-- ----------------------------
DROP TABLE IF EXISTS `user_recipe_collect`;
CREATE TABLE `user_recipe_collect`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `recipe_id` bigint(20) NOT NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_recipe`(`user_id`, `recipe_id`) USING BTREE,
  INDEX `recipe_id`(`recipe_id`) USING BTREE,
  CONSTRAINT `user_recipe_collect_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `user_recipe_collect_ibfk_2` FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_recipe_collect
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
