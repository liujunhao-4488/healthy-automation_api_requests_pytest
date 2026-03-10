-- =====================================================
-- 健康饮食推荐系统数据库表结构
-- =====================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS health_diet DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE health_diet;

-- =====================================================
-- 用户模块
-- =====================================================

-- 用户表
CREATE TABLE IF NOT EXISTS `user` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `username` VARCHAR(50) UNIQUE NOT NULL,
  `password` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) UNIQUE NOT NULL,
  `phone` VARCHAR(20),
  `avatar` VARCHAR(255) DEFAULT NULL,
  `status` TINYINT DEFAULT 1 COMMENT '账号状态: 0-禁用, 1-正常',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户饮食偏好表
CREATE TABLE IF NOT EXISTS `user_diet_preference` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `diet_type` VARCHAR(50) COMMENT '饮食类型: 素食、低碳水、清淡、麻辣等',
  `allergies` TEXT COMMENT '过敏原',
  `dislikes` TEXT COMMENT '不喜欢吃的食物',
  `favorites` TEXT COMMENT '喜欢吃的食物',
  `meal_frequency` INT DEFAULT 3 COMMENT '每日餐次',
  `snack_preference` TINYINT DEFAULT 1 COMMENT '是否吃零食: 0-否, 1-是',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 健康管理模块
-- =====================================================

-- 健康信息表
CREATE TABLE IF NOT EXISTS `health_info` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `age` INT COMMENT '年龄',
  `gender` VARCHAR(10) COMMENT '性别: 男/女',
  `height` DOUBLE COMMENT '身高(cm)',
  `weight` DOUBLE COMMENT '体重(kg)',
  `waist_circumference` DOUBLE COMMENT '腰围(cm)',
  `bmi` DOUBLE COMMENT 'BMI指数',
  `bmr` DOUBLE COMMENT '基础代谢率(kcal)',
  `blood_type` VARCHAR(10) COMMENT '血型',
  `blood_pressure` VARCHAR(20) COMMENT '血压',
  `blood_sugar` DOUBLE COMMENT '血糖(mmol/L)',
  `activity_level` VARCHAR(50) COMMENT '活动水平: sedentary/lightly_active/moderately_active/very_active/extra_active',
  `exercise_duration` INT COMMENT '每日运动时长(分钟)',
  `exercise_type` VARCHAR(100) COMMENT '运动类型',
  `allergies` TEXT COMMENT '过敏食物',
  `chronic_diseases` TEXT COMMENT '慢性疾病',
  `health_condition` VARCHAR(255) COMMENT '健康状况描述',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 健康信息历史记录表
CREATE TABLE IF NOT EXISTS `health_info_history` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `weight` DOUBLE COMMENT '体重(kg)',
  `bmi` DOUBLE COMMENT 'BMI指数',
  `exercise_duration` INT COMMENT '运动时长(分钟)',
  `record_date` DATE NOT NULL,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 运动记录表
CREATE TABLE IF NOT EXISTS `exercise_record` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `exercise_type` VARCHAR(50) NOT NULL COMMENT '运动类型',
  `duration` INT NOT NULL COMMENT '运动时长(分钟)',
  `calories_burned` DOUBLE COMMENT '消耗热量(kcal)',
  `intensity` VARCHAR(20) COMMENT '运动强度: low/medium/high',
  `record_date` DATE NOT NULL,
  `notes` TEXT COMMENT '备注',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 饮食目标模块
-- =====================================================

-- 饮食目标表
CREATE TABLE IF NOT EXISTS `diet_goal` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `goal_type` VARCHAR(50) NOT NULL COMMENT '目标类型: 减肥/增肌/控糖/维持健康',
  `target_weight` DOUBLE COMMENT '目标体重(kg)',
  `target_calories` DOUBLE NOT NULL COMMENT '目标每日热量(kcal)',
  `protein_ratio` DOUBLE COMMENT '蛋白质占比(%)',
  `carbs_ratio` DOUBLE COMMENT '碳水化合物占比(%)',
  `fat_ratio` DOUBLE COMMENT '脂肪占比(%)',
  `protein_target` DOUBLE COMMENT '蛋白质目标(g)',
  `carbs_target` DOUBLE COMMENT '碳水目标(g)',
  `fat_target` DOUBLE COMMENT '脂肪目标(g)',
  `water_target` INT COMMENT '每日饮水目标(ml)',
  `status` TINYINT DEFAULT 1 COMMENT '目标状态: 0-暂停, 1-进行中, 2-已完成',
  `start_date` DATE NOT NULL,
  `end_date` DATE COMMENT '目标结束日期',
  `reminder_enabled` TINYINT DEFAULT 1 COMMENT '是否开启提醒',
  `reminder_time` TIME COMMENT '每日提醒时间',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 食材管理模块
-- =====================================================

-- 食材表
CREATE TABLE IF NOT EXISTS `ingredient` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL COMMENT '食材名称',
  `category` VARCHAR(50) NOT NULL COMMENT '分类: 主食/蔬菜/肉类/蛋类/乳制品/水果/坚果/豆制品',
  `sub_category` VARCHAR(50) COMMENT '子分类',
  `calories_per_100g` DOUBLE NOT NULL COMMENT '热量(kcal/100g)',
  `protein_per_100g` DOUBLE COMMENT '蛋白质(g/100g)',
  `carbs_per_100g` DOUBLE COMMENT '碳水化合物(g/100g)',
  `fat_per_100g` DOUBLE COMMENT '脂肪(g/100g)',
  `fiber_per_100g` DOUBLE COMMENT '膳食纤维(g/100g)',
  `sugar_per_100g` DOUBLE COMMENT '糖分(g/100g)',
  `sodium_per_100g` DOUBLE COMMENT '钠(mg/100g)',
  `gi_value` INT COMMENT '升糖指数(GI)',
  `cholesterol_per_100g` DOUBLE COMMENT '胆固醇(mg/100g)',
  `vitamin_info` TEXT COMMENT '维生素信息(JSON)',
  `mineral_info` TEXT COMMENT '矿物质信息(JSON)',
  `description` TEXT COMMENT '食材描述',
  `image_url` VARCHAR(255) COMMENT '图片URL',
  `status` TINYINT DEFAULT 1 COMMENT '状态: 0-禁用, 1-正常',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 食材替代关系表
CREATE TABLE IF NOT EXISTS `ingredient_substitute` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `ingredient_id` BIGINT NOT NULL COMMENT '原食材ID',
  `substitute_id` BIGINT NOT NULL COMMENT '替代食材ID',
  `reason` VARCHAR(255) COMMENT '替代原因',
  `nutrition_match_rate` DOUBLE COMMENT '营养匹配度(%)',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient`(`id`),
  FOREIGN KEY (`substitute_id`) REFERENCES `ingredient`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 食谱管理模块
-- =====================================================

-- 食谱表
CREATE TABLE IF NOT EXISTS `recipe` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL COMMENT '食谱名称',
  `description` TEXT COMMENT '食谱描述',
  `category` VARCHAR(50) COMMENT '食谱分类: 早餐/午餐/晚餐/加餐',
  `cuisine_type` VARCHAR(50) COMMENT '菜系',
  `cooking_time` INT COMMENT '烹饪时间(分钟)',
  `difficulty` VARCHAR(20) COMMENT '难度: 简单/中等/困难',
  `servings` INT DEFAULT 1 COMMENT '份数',
  `total_calories` DOUBLE COMMENT '总热量(kcal)',
  `calories_per_serving` DOUBLE COMMENT '每份热量(kcal)',
  `protein` DOUBLE COMMENT '蛋白质(g)',
  `carbs` DOUBLE COMMENT '碳水化合物(g)',
  `fat` DOUBLE COMMENT '脂肪(g)',
  `fiber` DOUBLE COMMENT '膳食纤维(g)',
  `instructions` TEXT NOT NULL COMMENT '烹饪步骤(JSON数组)',
  `tips` TEXT COMMENT '烹饪小贴士',
  `image_url` VARCHAR(255) COMMENT '图片URL',
  `video_url` VARCHAR(255) COMMENT '视频教程URL',
  `creator_id` BIGINT COMMENT '创建者ID',
  `is_custom` TINYINT DEFAULT 0 COMMENT '是否用户自定义: 0-系统, 1-自定义',
  `is_public` TINYINT DEFAULT 1 COMMENT '是否公开',
  `score` DOUBLE DEFAULT 5.0 COMMENT '评分',
  `score_count` INT DEFAULT 0 COMMENT '评分次数',
  `view_count` INT DEFAULT 0 COMMENT '浏览次数',
  `collect_count` INT DEFAULT 0 COMMENT '收藏次数',
  `suitable_for` VARCHAR(255) COMMENT '适宜人群',
  `goal_type` VARCHAR(50) COMMENT '适宜目标: 减肥/增肌/控糖/通用',
  `status` TINYINT DEFAULT 1 COMMENT '状态: 0-下架, 1-上架',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`creator_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 食谱食材关联表
CREATE TABLE IF NOT EXISTS `recipe_ingredient` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `recipe_id` BIGINT NOT NULL,
  `ingredient_id` BIGINT NOT NULL,
  `quantity` DOUBLE NOT NULL COMMENT '用量',
  `unit` VARCHAR(20) NOT NULL COMMENT '单位: g/ml/个/勺',
  `is_optional` TINYINT DEFAULT 0 COMMENT '是否可选',
  `notes` VARCHAR(100) COMMENT '备注',
  FOREIGN KEY (`recipe_id`) REFERENCES `recipe`(`id`),
  FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户食谱收藏表
CREATE TABLE IF NOT EXISTS `user_recipe_collect` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `recipe_id` BIGINT NOT NULL,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`),
  FOREIGN KEY (`recipe_id`) REFERENCES `recipe`(`id`),
  UNIQUE KEY `uk_user_recipe` (`user_id`, `recipe_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 饮食记录模块
-- =====================================================

-- 饮食记录表
CREATE TABLE IF NOT EXISTS `diet_record` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `record_date` DATE NOT NULL,
  `meal_type` VARCHAR(20) NOT NULL COMMENT '餐次: breakfast/lunch/dinner/snack',
  `meal_time` TIME COMMENT '实际用餐时间',
  `total_calories` DOUBLE COMMENT '总热量(kcal)',
  `total_protein` DOUBLE COMMENT '总蛋白质(g)',
  `total_carbs` DOUBLE COMMENT '总碳水(g)',
  `total_fat` DOUBLE COMMENT '总脂肪(g)',
  `total_fiber` DOUBLE COMMENT '总膳食纤维(g)',
  `water_intake` INT COMMENT '饮水量(ml)',
  `notes` TEXT COMMENT '备注',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 饮食记录详情表
CREATE TABLE IF NOT EXISTS `diet_record_detail` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `record_id` BIGINT NOT NULL,
  `ingredient_id` BIGINT COMMENT '食材ID',
  `food_name` VARCHAR(100) NOT NULL COMMENT '食物名称',
  `category` VARCHAR(50) COMMENT '食物分类',
  `quantity` DOUBLE NOT NULL COMMENT '用量',
  `unit` VARCHAR(20) NOT NULL COMMENT '单位',
  `calories` DOUBLE COMMENT '热量(kcal)',
  `protein` DOUBLE COMMENT '蛋白质(g)',
  `carbs` DOUBLE COMMENT '碳水化合物(g)',
  `fat` DOUBLE COMMENT '脂肪(g)',
  `fiber` DOUBLE COMMENT '膳食纤维(g)',
  `recipe_id` BIGINT COMMENT '来源食谱ID',
  `is_custom` TINYINT DEFAULT 0 COMMENT '是否自定义食材',
  FOREIGN KEY (`record_id`) REFERENCES `diet_record`(`id`),
  FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient`(`id`),
  FOREIGN KEY (`recipe_id`) REFERENCES `recipe`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 健康知识模块
-- =====================================================

-- 健康文章表
CREATE TABLE IF NOT EXISTS `health_article` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `summary` VARCHAR(500) COMMENT '文章摘要',
  `content` TEXT NOT NULL,
  `cover_image` VARCHAR(255) COMMENT '封面图',
  `category` VARCHAR(50) NOT NULL COMMENT '分类: 饮食指南/营养知识/减肥指南/增肌指南/饮食误区',
  `tags` TEXT COMMENT '标签(JSON数组)',
  `author` VARCHAR(50) COMMENT '作者',
  `suitable_for` VARCHAR(255) COMMENT '适宜人群',
  `goal_type` VARCHAR(50) COMMENT '关联目标: 减肥/增肌/控糖/通用',
  `read_count` INT DEFAULT 0,
  `like_count` INT DEFAULT 0,
  `share_count` INT DEFAULT 0,
  `publish_date` DATE,
  `status` TINYINT DEFAULT 1 COMMENT '状态: 0-草稿, 1-已发布',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户阅读记录表
CREATE TABLE IF NOT EXISTS `user_read_record` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `article_id` BIGINT NOT NULL,
  `read_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `read_duration` INT COMMENT '阅读时长(秒)',
  `is_finished` TINYINT DEFAULT 0 COMMENT '是否读完',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`),
  FOREIGN KEY (`article_id`) REFERENCES `health_article`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户文章收藏表
CREATE TABLE IF NOT EXISTS `user_article_collect` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `article_id` BIGINT NOT NULL,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`),
  FOREIGN KEY (`article_id`) REFERENCES `health_article`(`id`),
  UNIQUE KEY `uk_user_article` (`user_id`, `article_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 消息通知模块
-- =====================================================

-- 消息通知表
CREATE TABLE IF NOT EXISTS `notification` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `type` VARCHAR(30) NOT NULL COMMENT '消息类型: diet_reminder/goal_achieved/article_recommend/warning/system',
  `title` VARCHAR(100) NOT NULL,
  `content` TEXT,
  `related_id` BIGINT COMMENT '关联ID',
  `related_type` VARCHAR(30) COMMENT '关联类型: recipe/article/diet_record',
  `is_read` TINYINT DEFAULT 0 COMMENT '是否已读',
  `read_time` DATETIME,
  `send_time` DATETIME COMMENT '发送时间',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- AI推荐记录模块
-- =====================================================

-- AI推荐记录表
CREATE TABLE IF NOT EXISTS `ai_recommend_log` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `recommend_type` VARCHAR(30) NOT NULL COMMENT '推荐类型: recipe/ingredient/article',
  `input_data` TEXT COMMENT '输入数据(JSON)',
  `recommend_result` TEXT COMMENT '推荐结果(JSON)',
  `algorithm` VARCHAR(50) COMMENT '使用算法',
  `score` DOUBLE COMMENT '推荐评分',
  `is_accepted` TINYINT DEFAULT 0 COMMENT '是否采纳',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 初始数据
-- =====================================================

-- 插入初始食材数据
INSERT INTO `ingredient` (`name`, `category`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `gi_value`) VALUES
-- 主食类
('米饭', '主食', 116, 2.6, 25.6, 0.3, 0.4, 73),
('面条', '主食', 137, 3.6, 28.9, 0.7, 0.9, 55),
('全麦面包', '主食', 247, 13, 41, 3.4, 7, 50),
('燕麦', '主食', 389, 17, 66, 7, 10, 55),
('糙米', '主食', 111, 2.6, 23, 0.9, 1.8, 68),
('红薯', '主食', 86, 1.6, 20, 0.1, 3, 54),
('玉米', '主食', 96, 3.3, 21, 1.4, 2.7, 52),

-- 蛋类
('鸡蛋', '蛋类', 155, 13, 1.1, 10.6, 0, 0),
('鸭蛋', '蛋类', 180, 13, 3.1, 14, 0, 0),
('鹌鹑蛋', '蛋类', 158, 13, 0.4, 11, 0, 0),

-- 乳制品类
('牛奶', '乳制品', 42, 3.4, 5, 1, 0, 27),
('酸奶', '乳制品', 72, 2.5, 10, 2.7, 0, 48),
('奶酪', '乳制品', 328, 25, 3.5, 23, 0, 0),
('豆浆', '乳制品', 31, 3.3, 1.2, 1.7, 0.4, 34),

-- 肉类
('鸡肉', '肉类', 165, 31, 0, 3.6, 0, 0),
('鸡胸肉', '肉类', 165, 31, 0, 3.6, 0, 0),
('牛肉', '肉类', 250, 26, 0, 17, 0, 0),
('猪肉', '肉类', 337, 13.2, 2.4, 30.8, 0, 0),
('鱼肉', '肉类', 124, 20.4, 0, 4.1, 0, 0),
('虾', '肉类', 99, 24, 0.2, 0.3, 0, 0),

-- 蔬菜类
('西红柿', '蔬菜', 18, 0.9, 3.9, 0.2, 1.2, 15),
('黄瓜', '蔬菜', 15, 0.8, 3.6, 0.1, 0.5, 15),
('白菜', '蔬菜', 17, 1.5, 3.2, 0.1, 1, 15),
('胡萝卜', '蔬菜', 41, 0.9, 9.6, 0.2, 2.8, 39),
('菠菜', '蔬菜', 23, 2.9, 3.6, 0.4, 2.2, 15),
('西兰花', '蔬菜', 34, 2.8, 7, 0.4, 2.6, 15),
('茄子', '蔬菜', 25, 1.1, 6, 0.2, 1.2, 15),
('青椒', '蔬菜', 20, 0.9, 4.6, 0.2, 1.7, 15),
('蘑菇', '蔬菜', 22, 3.1, 3.3, 0.3, 1, 15),
('番茄', '蔬菜', 18, 0.9, 3.9, 0.2, 1.2, 15),

-- 水果类
('苹果', '水果', 52, 0.3, 13.8, 0.2, 2.4, 36),
('香蕉', '水果', 89, 1.1, 22.8, 0.3, 2.6, 51),
('橙子', '水果', 47, 0.9, 11.8, 0.1, 2.4, 43),
('葡萄', '水果', 69, 0.7, 18, 0.2, 1, 56),
('西瓜', '水果', 30, 0.6, 8, 0.2, 0.4, 72),
('草莓', '水果', 32, 0.7, 7.7, 0.3, 2, 40),
('梨', '水果', 57, 0.4, 14, 0.1, 3.1, 38),

-- 豆制品类
('豆腐', '豆制品', 76, 8, 1.9, 4.8, 0.3, 15),
('黄豆', '豆制品', 390, 36, 34, 16, 15, 15),

-- 坚果类
('花生', '坚果', 567, 26, 16, 49, 8.5, 14),
('核桃', '坚果', 654, 15, 14, 65, 6.7, 15),
('杏仁', '坚果', 579, 21, 22, 50, 12, 15);

-- 插入初始健康文章数据
INSERT INTO `health_article` (`title`, `summary`, `content`, `category`, `tags`, `author`, `suitable_for`, `goal_type`, `publish_date`) VALUES
('控糖饮食指南', '控糖饮食对于预防糖尿病和维持健康体重非常重要', '控糖饮食对于预防糖尿病和维持健康体重非常重要。建议减少高GI食物的摄入，选择低GI食物，如全谷物、蔬菜等。同时要注意控制每日总糖摄入量，包括蔗糖、果糖等添加糖。', '饮食指南', '["控糖", "糖尿病", "健康"]', '营养师小王', '糖尿病患者、肥胖人群', '控糖', '2024-01-01'),
('蛋白质摄入的重要性', '蛋白质是身体的重要组成部分，对于肌肉生长和修复至关重要', '蛋白质是身体的重要组成部分，对于肌肉生长和修复至关重要。建议成年人每公斤体重摄入1-1.2克蛋白质。优质蛋白质来源包括鸡胸肉、鱼、蛋、奶制品和豆制品。', '营养知识', '["蛋白质", "肌肉", "健康"]', '营养师小李', '健身人群、增肌人群', '增肌', '2024-01-02'),
('健康减肥的正确方法', '健康减肥需要合理控制饮食并结合适当的运动', '健康减肥需要合理控制饮食并结合适当的运动。建议每日热量摄入控制在基础代谢率的1.2-1.5倍，同时保证营养均衡。运动方面建议每周进行150分钟中等强度有氧运动。', '减肥指南', '["减肥", "健康", "运动"]', '健身教练小张', '肥胖人群', '减肥', '2024-01-03'),
('增肌饮食策略', '增肌需要足够的蛋白质和热量摄入，同时结合力量训练', '增肌需要足够的蛋白质和热量摄入，同时结合力量训练。建议每公斤体重摄入1.6-2.2克蛋白质，在训练后30分钟内补充蛋白质效果最佳。碳水化合物是训练能量的主要来源，也要保证充足摄入。', '增肌指南', '["增肌", "蛋白质", "力量训练"]', '健身教练小王', '健身人群', '增肌', '2024-01-04'),
('饮食误区大揭秘', '常见的饮食误区包括过度节食、偏食等，这些都会影响健康', '常见的饮食误区包括：1.过度节食导致基础代谢下降；2.只吃蔬菜水果导致蛋白质缺乏；3.不吃主食导致碳水不足；4.迷信减肥药和减肥产品。正确做法是均衡饮食，适量运动。', '饮食误区', '["误区", "健康", "饮食"]', '营养师小陈', '所有人群', '通用', '2024-01-05'),
('高血压饮食建议', '高血压患者应该如何调整饮食结构', '高血压患者应该：1.限制钠盐摄入，每日不超过5克；2.增加钾的摄入，多吃蔬菜水果；3.控制脂肪摄入，减少动物内脏；4.戒烟限酒；5.保持规律作息。', '饮食指南', '["高血压", "心血管", "饮食"]', '营养师小李', '高血压人群', '通用', '2024-01-06'),
('如何科学补水', '科学补水对于维持身体健康至关重要', '科学补水建议：1.每日饮水1500-2000ml；2.运动前半小时补充300ml水；3.运动中每15-20分钟补充100-150ml；4.运动后根据体重丢失量补充；5.养成主动喝水习惯，不要等口渴再喝。', '营养知识', '["补水", "健康", "饮水"]', '营养师小王', '所有人群', '通用', '2024-01-07');
