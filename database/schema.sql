-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: localhost    Database: health_diet
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `article_comment`
--

DROP TABLE IF EXISTS `article_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `article_comment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `article_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_deleted` tinyint DEFAULT '0' COMMENT '是否软删除: 0-否 1-是',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `parent_id` bigint DEFAULT NULL COMMENT '父评论ID',
  `reply_to_user_id` bigint DEFAULT NULL COMMENT '回复目标用户ID',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_article_comment_article` (`article_id`) USING BTREE,
  KEY `idx_article_comment_user` (`user_id`) USING BTREE,
  CONSTRAINT `article_comment_ibfk_1` FOREIGN KEY (`article_id`) REFERENCES `health_article` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `article_comment_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `assistant_conversation`
--

DROP TABLE IF EXISTS `assistant_conversation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assistant_conversation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `summary` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `message_count` int DEFAULT '0',
  `last_message_at` datetime DEFAULT NULL,
  `is_deleted` tinyint DEFAULT '0',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_assistant_conversation_user_id` (`user_id`) USING BTREE,
  KEY `idx_assistant_conversation_last_message_at` (`last_message_at`) USING BTREE,
  CONSTRAINT `fk_assistant_conversation_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=3417 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `assistant_message`
--

DROP TABLE IF EXISTS `assistant_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assistant_message` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `conversation_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `cards_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `message_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'text',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_assistant_message_conversation_id` (`conversation_id`) USING BTREE,
  KEY `idx_assistant_message_user_id` (`user_id`) USING BTREE,
  CONSTRAINT `fk_assistant_message_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `assistant_conversation` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_assistant_message_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=7243 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `diet_goal`
--

DROP TABLE IF EXISTS `diet_goal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `diet_goal` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `goal_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标类型: 减肥/增肌/控糖/维持健康',
  `target_weight` double DEFAULT NULL COMMENT '目标体重(kg)',
  `target_calories` double NOT NULL COMMENT '目标每日热量(kcal)',
  `protein_ratio` double DEFAULT NULL COMMENT '蛋白质占比(%)',
  `carbs_ratio` double DEFAULT NULL COMMENT '碳水化合物占比(%)',
  `fat_ratio` double DEFAULT NULL COMMENT '脂肪占比(%)',
  `protein_target` double DEFAULT NULL COMMENT '蛋白质目标(g)',
  `carbs_target` double DEFAULT NULL COMMENT '碳水目标(g)',
  `fat_target` double DEFAULT NULL COMMENT '脂肪目标(g)',
  `water_target` int DEFAULT NULL COMMENT '每日饮水目标(ml)',
  `status` tinyint DEFAULT '1' COMMENT '目标状态: 0-暂停, 1-进行中, 2-已完成',
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL COMMENT '目标结束日期',
  `reminder_enabled` tinyint DEFAULT '1' COMMENT '是否开启提醒',
  `reminder_time` time DEFAULT NULL COMMENT '每日提醒时间',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`) USING BTREE,
  CONSTRAINT `diet_goal_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=400275 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `diet_record`
--

DROP TABLE IF EXISTS `diet_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `diet_record` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `record_date` date NOT NULL,
  `meal_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '餐次: breakfast/lunch/dinner/snack',
  `total_calories` double DEFAULT NULL COMMENT '总热量(kcal)',
  `total_protein` double DEFAULT NULL COMMENT '总蛋白质(g)',
  `total_carbs` double DEFAULT NULL COMMENT '总碳水(g)',
  `total_fat` double DEFAULT NULL COMMENT '总脂肪(g)',
  `notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '备注',
  `is_deleted` tinyint DEFAULT '0' COMMENT '是否软删除: 0-否 1-是',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`) USING BTREE,
  CONSTRAINT `diet_record_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=908468 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `diet_record_detail`
--

DROP TABLE IF EXISTS `diet_record_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `diet_record_detail` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `record_id` bigint NOT NULL,
  `ingredient_id` bigint DEFAULT NULL COMMENT '食材ID',
  `food_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '食物名称',
  `quantity` double NOT NULL COMMENT '用量',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '单位',
  `calories` double DEFAULT NULL COMMENT '热量(kcal)',
  `protein` double DEFAULT NULL COMMENT '蛋白质(g)',
  `carbs` double DEFAULT NULL COMMENT '碳水化合物(g)',
  `fat` double DEFAULT NULL COMMENT '脂肪(g)',
  `recipe_id` bigint DEFAULT NULL COMMENT '来源食谱ID',
  `is_custom` tinyint DEFAULT '0' COMMENT '是否自定义食材',
  `is_deleted` tinyint DEFAULT '0' COMMENT '是否软删除: 0-否 1-是',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `record_id` (`record_id`) USING BTREE,
  KEY `ingredient_id` (`ingredient_id`) USING BTREE,
  KEY `recipe_id` (`recipe_id`) USING BTREE,
  CONSTRAINT `diet_record_detail_ibfk_1` FOREIGN KEY (`record_id`) REFERENCES `diet_record` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `diet_record_detail_ibfk_2` FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `diet_record_detail_ibfk_3` FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1033835 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `health_article`
--

DROP TABLE IF EXISTS `health_article`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `health_article` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `summary` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文章摘要',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分类: 饮食指南/营养知识/减肥指南/增肌指南/饮食误区',
  `tags` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '标签(JSON数组)',
  `author` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作者',
  `suitable_for` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '适宜人群',
  `goal_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联目标: 减肥/增肌/控糖/通用',
  `read_count` int DEFAULT '0',
  `like_count` int DEFAULT '0',
  `comment_count` int DEFAULT '0' COMMENT '评论数',
  `publish_date` date DEFAULT NULL,
  `status` tinyint DEFAULT '1' COMMENT '状态: 0-草稿, 1-已发布',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2038627116093902856 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `health_info`
--

DROP TABLE IF EXISTS `health_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `health_info` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `age` int DEFAULT NULL COMMENT '年龄',
  `gender` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '性别: 男/女',
  `height` double DEFAULT NULL COMMENT '身高(cm)',
  `weight` double DEFAULT NULL COMMENT '体重(kg)',
  `bmi` double DEFAULT NULL COMMENT 'BMI指数',
  `bmr` double DEFAULT NULL COMMENT '基础代谢率(kcal)',
  `blood_pressure` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '血压',
  `blood_sugar` double DEFAULT NULL COMMENT '血糖(mmol/L)',
  `activity_level` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '活动水平: sedentary/lightly_active/moderately_active/very_active/extra_active',
  `exercise_duration` int DEFAULT NULL COMMENT '每日运动时长(分钟)',
  `exercise_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '运动类型',
  `chronic_diseases` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '慢性疾病',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`) USING BTREE,
  CONSTRAINT `health_info_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=200275 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `health_info_history`
--

DROP TABLE IF EXISTS `health_info_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `health_info_history` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `weight` double DEFAULT NULL COMMENT '体重(kg)',
  `bmi` double DEFAULT NULL COMMENT 'BMI指数',
  `exercise_duration` int DEFAULT NULL COMMENT '运动时长(分钟)',
  `record_date` date NOT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`) USING BTREE,
  CONSTRAINT `health_info_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=239 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ingredient`
--

DROP TABLE IF EXISTS `ingredient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ingredient` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '食材名称',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分类: 主食/蔬菜/肉类/蛋类/乳制品/水果/坚果/豆制品',
  `sub_category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '子分类',
  `calories_per_100g` double NOT NULL COMMENT '热量(kcal/100g)',
  `protein_per_100g` double DEFAULT NULL COMMENT '蛋白质(g/100g)',
  `carbs_per_100g` double DEFAULT NULL COMMENT '碳水化合物(g/100g)',
  `fat_per_100g` double DEFAULT NULL COMMENT '脂肪(g/100g)',
  `fiber_per_100g` double DEFAULT NULL COMMENT '膳食纤维(g/100g)',
  `sugar_per_100g` double DEFAULT NULL COMMENT '糖分(g/100g)',
  `sodium_per_100g` double DEFAULT NULL COMMENT '钠(mg/100g)',
  `gi_value` int DEFAULT NULL COMMENT '升糖指数(GI)',
  `cholesterol_per_100g` double DEFAULT NULL COMMENT '胆固醇(mg/100g)',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '食材描述',
  `image_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图片URL',
  `status` tinyint DEFAULT '1' COMMENT '状态: 0-禁用, 1-正常',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=500059 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notification`
--

DROP TABLE IF EXISTS `notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息类型: diet_reminder/goal_achieved/article_recommend/warning/system',
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `related_id` bigint DEFAULT NULL COMMENT '关联ID',
  `related_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联类型: recipe/article/diet_record',
  `is_read` tinyint DEFAULT '0' COMMENT '是否已读',
  `is_deleted` tinyint DEFAULT '0' COMMENT '是否软删除: 0-否 1-是',
  `read_time` datetime DEFAULT NULL,
  `send_time` datetime DEFAULT NULL COMMENT '发送时间',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`) USING BTREE,
  CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=274 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recipe`
--

DROP TABLE IF EXISTS `recipe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipe` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '食谱名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '食谱描述',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '食谱分类: 早餐/午餐/晚餐/加餐',
  `cuisine_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '菜系',
  `cooking_time` int DEFAULT NULL COMMENT '烹饪时间(分钟)',
  `difficulty` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '难度: 简单/中等/困难',
  `servings` int DEFAULT '1' COMMENT '份数',
  `total_calories` double DEFAULT NULL COMMENT '总热量(kcal)',
  `calories_per_serving` double DEFAULT NULL COMMENT '每份热量(kcal)',
  `protein` double DEFAULT NULL COMMENT '蛋白质(g)',
  `carbs` double DEFAULT NULL COMMENT '碳水化合物(g)',
  `fat` double DEFAULT NULL COMMENT '脂肪(g)',
  `fiber` double DEFAULT NULL COMMENT '膳食纤维(g)',
  `instructions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '烹饪步骤(JSON数组)',
  `tips` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '烹饪小贴士',
  `image_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图片URL',
  `creator_id` bigint DEFAULT NULL COMMENT '创建者ID',
  `is_custom` tinyint DEFAULT '0' COMMENT '是否用户自定义: 0-系统, 1-自定义',
  `score` double DEFAULT '5' COMMENT '评分',
  `score_count` int DEFAULT '0' COMMENT '评分次数',
  `view_count` int DEFAULT '0' COMMENT '浏览次数',
  `collect_count` int DEFAULT '0' COMMENT '收藏次数',
  `suitable_for` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '适宜人群',
  `goal_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '适宜目标: 减肥/增肌/控糖/通用',
  `status` tinyint DEFAULT '1' COMMENT '状态: 0-下架, 1-上架',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `creator_id` (`creator_id`) USING BTREE,
  CONSTRAINT `recipe_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=600181 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recipe_ingredient`
--

DROP TABLE IF EXISTS `recipe_ingredient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipe_ingredient` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `recipe_id` bigint NOT NULL,
  `ingredient_id` bigint NOT NULL,
  `quantity` double NOT NULL COMMENT '用量',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '单位: g/ml/个/勺',
  `is_optional` tinyint DEFAULT '0' COMMENT '是否可选',
  `notes` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `recipe_id` (`recipe_id`) USING BTREE,
  KEY `ingredient_id` (`ingredient_id`) USING BTREE,
  CONSTRAINT `recipe_ingredient_ibfk_1` FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `recipe_ingredient_ibfk_2` FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2039952763604975618 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `avatar` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '头像URL或本地图片数据',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'user' COMMENT '???: user/admin',
  `status` tinyint DEFAULT '1' COMMENT '账号状态: 0-禁用, 1-正常',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `username` (`username`) USING BTREE,
  UNIQUE KEY `email` (`email`) USING BTREE,
  UNIQUE KEY `uk_phone` (`phone`)
) ENGINE=InnoDB AUTO_INCREMENT=101314 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_article_collect`
--

DROP TABLE IF EXISTS `user_article_collect`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_article_collect` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `article_id` bigint NOT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_user_article` (`user_id`,`article_id`) USING BTREE,
  KEY `article_id` (`article_id`) USING BTREE,
  CONSTRAINT `user_article_collect_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `user_article_collect_ibfk_2` FOREIGN KEY (`article_id`) REFERENCES `health_article` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_article_like`
--

DROP TABLE IF EXISTS `user_article_like`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_article_like` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `article_id` bigint NOT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_user_article_like` (`user_id`,`article_id`) USING BTREE,
  KEY `idx_article_like_article` (`article_id`) USING BTREE,
  CONSTRAINT `user_article_like_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `user_article_like_ibfk_2` FOREIGN KEY (`article_id`) REFERENCES `health_article` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_diet_preference`
--

DROP TABLE IF EXISTS `user_diet_preference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_diet_preference` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `diet_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '饮食类型: 素食、低碳水、清淡、麻辣等',
  `allergies` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '过敏原',
  `dislikes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '不喜欢吃的食物',
  `favorites` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '喜欢吃的食物',
  `meal_frequency` int DEFAULT '3' COMMENT '每日餐次',
  `snack_preference` tinyint DEFAULT '1' COMMENT '是否吃零食: 0-否, 1-是',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`) USING BTREE,
  CONSTRAINT `user_diet_preference_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=300182 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_read_record`
--

DROP TABLE IF EXISTS `user_read_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_read_record` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `article_id` bigint NOT NULL,
  `read_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `read_duration` int DEFAULT NULL COMMENT '阅读时长(秒)',
  `is_finished` tinyint DEFAULT '0' COMMENT '是否读完',
  `scroll_percent` int DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `user_id` (`user_id`) USING BTREE,
  KEY `article_id` (`article_id`) USING BTREE,
  CONSTRAINT `user_read_record_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `user_read_record_ibfk_2` FOREIGN KEY (`article_id`) REFERENCES `health_article` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2110660531039502339 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_recipe_collect`
--

DROP TABLE IF EXISTS `user_recipe_collect`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_recipe_collect` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `recipe_id` bigint NOT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_user_recipe` (`user_id`,`recipe_id`) USING BTREE,
  KEY `recipe_id` (`recipe_id`) USING BTREE,
  CONSTRAINT `user_recipe_collect_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `user_recipe_collect_ibfk_2` FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=802276 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-23 10:50:51
