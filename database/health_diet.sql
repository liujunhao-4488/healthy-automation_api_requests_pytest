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

 Date: 12/04/2026 20:30:32
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
-- Table structure for article_comment
-- ----------------------------
DROP TABLE IF EXISTS `article_comment`;
CREATE TABLE `article_comment`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `article_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_deleted` tinyint(4) NULL DEFAULT 0 COMMENT '是否软删除: 0-否 1-是',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `parent_id` bigint(20) NULL DEFAULT NULL COMMENT '父评论ID',
  `reply_to_user_id` bigint(20) NULL DEFAULT NULL COMMENT '回复目标用户ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_article_comment_article`(`article_id`) USING BTREE,
  INDEX `idx_article_comment_user`(`user_id`) USING BTREE,
  CONSTRAINT `article_comment_ibfk_1` FOREIGN KEY (`article_id`) REFERENCES `health_article` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `article_comment_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of article_comment
-- ----------------------------
INSERT INTO `article_comment` VALUES (1, 1, 1, '非常有用', 0, '2026-03-28 22:34:30', '2026-03-28 22:34:30', NULL, NULL);

-- ----------------------------
-- Table structure for assistant_conversation
-- ----------------------------
DROP TABLE IF EXISTS `assistant_conversation`;
CREATE TABLE `assistant_conversation`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `summary` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `message_count` int(11) NULL DEFAULT 0,
  `last_message_at` datetime NULL DEFAULT NULL,
  `is_deleted` tinyint(4) NULL DEFAULT 0,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_assistant_conversation_user_id`(`user_id`) USING BTREE,
  INDEX `idx_assistant_conversation_last_message_at`(`last_message_at`) USING BTREE,
  CONSTRAINT `fk_assistant_conversation_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of assistant_conversation
-- ----------------------------
INSERT INTO `assistant_conversation` VALUES (1, 1, '能否告诉我热量相近的替代...', '根据您的健康增重目标，为您提供几组热量相近的替代食材方案。这些方案旨在帮助您在不增加过多饱腹感的前提下，更高效地摄入热量和蛋白质，以支持健康的体重增长。  **1. 主食类替代：用杂粮饭替代白米饭** *   **替代方案**：将部分白米…', 3, '2026-04-12 16:21:01', 0, '2026-04-12 16:20:28', '2026-04-12 16:20:28');
INSERT INTO `assistant_conversation` VALUES (2, 1, 'AI 小助手会话', NULL, 0, NULL, 1, '2026-04-12 17:06:54', '2026-04-12 17:06:54');
INSERT INTO `assistant_conversation` VALUES (3, 1, 'AI 小助手会话', NULL, 0, NULL, 1, '2026-04-12 17:06:55', '2026-04-12 17:06:55');
INSERT INTO `assistant_conversation` VALUES (4, 1, 'AI 小助手会话', NULL, 0, NULL, 1, '2026-04-12 17:06:55', '2026-04-12 17:06:55');
INSERT INTO `assistant_conversation` VALUES (5, 1, 'AI 小助手会话', NULL, 0, NULL, 1, '2026-04-12 17:06:55', '2026-04-12 17:06:55');
INSERT INTO `assistant_conversation` VALUES (6, 1, 'AI 小助手会话', NULL, 0, NULL, 1, '2026-04-12 17:06:56', '2026-04-12 17:06:56');
INSERT INTO `assistant_conversation` VALUES (7, 1, '我不太喜欢鸡胸肉，有没有...', '根据你的健康增重目标和当前偏瘦的体质（BMI约17.5），晚餐的替代建议应聚焦于在保证营养均衡的前提下，**增加优质热量和蛋白质的摄入**，同时确保食物易于消化，避免影响夜间睡眠。  以下是几个具体的晚餐食材替代与搭配方案：  **1. …', 9, '2026-04-12 18:44:25', 0, '2026-04-12 18:27:58', '2026-04-12 18:27:58');

-- ----------------------------
-- Table structure for assistant_message
-- ----------------------------
DROP TABLE IF EXISTS `assistant_message`;
CREATE TABLE `assistant_message`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `conversation_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `cards_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `message_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'text',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_assistant_message_conversation_id`(`conversation_id`) USING BTREE,
  INDEX `idx_assistant_message_user_id`(`user_id`) USING BTREE,
  CONSTRAINT `fk_assistant_message_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `assistant_conversation` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_assistant_message_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of assistant_message
-- ----------------------------
INSERT INTO `assistant_message` VALUES (1, 1, 1, 'user', '能否告诉我热量相近的替代食材？', NULL, 'text', '2026-04-12 16:20:28');
INSERT INTO `assistant_message` VALUES (2, 1, 1, 'context', '请结合用户健康与饮食目标提供食材替换建议：\n健康评估：，年龄 22，性别 男，身高 170cm，体重 50.7kg，BMI 17.543252595155714，活动水平 轻度活动，过敏信息 --，慢性病 --\n饮食目标：，目标类型 健康增重，目标热量 2474kcal，蛋白质目标 148g，碳水目标 297g，脂肪目标 77g，水分目标 2600ml\n用户问题：能否告诉我热量相近的替代食材？\n说明：请优先给出替代食材、营养差异与使用建议。', NULL, 'context', '2026-04-12 16:20:28');
INSERT INTO `assistant_message` VALUES (3, 1, 1, 'assistant', '根据您的健康增重目标，为您提供几组热量相近的替代食材方案。这些方案旨在帮助您在不增加过多饱腹感的前提下，更高效地摄入热量和蛋白质，以支持健康的体重增长。\n\n**1. 主食类替代：用杂粮饭替代白米饭**\n*   **替代方案**：将部分白米饭替换为等量的杂粮饭（如糙米、藜麦、燕麦米混合）。\n*   **营养差异**：杂粮饭的热量与白米饭相近，但膳食纤维、B族维生素和矿物质（如镁、锌）含量显著更高。纤维有助于维持肠道健康，但初期可能增加饱腹感。\n*   **使用建议**：建议从“白米：杂粮=2:1”的比例开始，让肠胃适应。这能在保证热量摄入的同时，提升营养密度，更符合“健康增重”而非单纯“增肥”的目标。\n\n**2. 蛋白质类替代：用三文鱼替代鸡胸肉**\n*   **替代方案**：在餐单中，将100克鸡胸肉（约165千卡，31克蛋白质）替换为100克煎三文鱼（约208千卡，22克蛋白质）。\n*   **营养差异**：三文鱼热量更高，主要差异在于其富含优质脂肪（特别是Omega-3脂肪酸），而蛋白质含量略低。Omega-3有助于抗炎和维持心血管健康。\n*   **使用建议**：每周安排2-3次用三文鱼、鳕鱼等富含脂肪的鱼类替代瘦肉。这能帮助您更轻松地达到每日77克的脂肪目标，增加热量盈余，同时获取对健康至关重要的脂肪酸。\n\n**3. 加餐类替代：用混合坚果与酸奶替代单一水果**\n*   **替代方案**：将一份苹果（约95千卡）的加餐，替换为“一杯全脂希腊酸奶（约150千卡，15克蛋白质）+ 一小把混合坚果（如杏仁、核桃，约100千卡）”。\n*   **营养差异**：替代后的组合热量从95千卡提升至约250千卡，同时提供了大量的优质蛋白质、健康脂肪以及钙质。营养更为全面，增重效率更高。\n*   **使用建议**：作为下午或睡前的加餐。这种组合既能补充热量和蛋白质，促进肌肉合成，其脂肪和蛋白质带来的饱腹感也更为持久稳定，避免因饥饿导致下一餐暴食。\n\n**4. 烹饪与佐餐类替代：用健康油脂与酱料提升热量**\n*   **替代方案**：在沙拉、蒸菜或米饭中，用橄榄油、牛油果油或芝麻酱替代部分或全部低热量沙拉酱。\n*   **营养差异**：一汤匙（15ml）橄榄油约含120千卡健康的不饱和脂肪，能大幅提升菜肴的热量密度，而几乎不增加食物体积。\n*   **使用建议**：在吃蔬菜、鸡胸肉或米饭时，淋上一汤匙优质油脂或一勺芝麻酱/花生酱。这是增加每日总热量摄入最轻松、最有效的方法之一，特别适合胃口有限但需要高热量的人群。\n\n---\n\n**为什么这些替代方案适合您？**\n\n您的BMI为17.5，属于体重过轻范围，核心目标是“健康增重”。这意味着您需要创造持续的热量盈余（目标2474千卡），并确保充足的蛋白质摄入（148克/天）以增加肌肉而非纯脂肪。\n\n1.  **聚焦热量与营养密度**：上述方案都选择了在相近或更小食物体积下，提供更高热量和更丰富营养（特别是蛋白质和健康脂肪）的食材。例如，用三文鱼替代鸡胸肉、用坚果酸奶替代水果，都能在您有限的胃容量内，塞进更多“有用的”热量和营养素。\n2.  **优化宏量营养素结构**：您的脂肪目标为77克，通过引入三文鱼、坚果、优质食用油等食材，可以美味、轻松地达成脂肪摄入目标，为身体提供高能量的营养来源。同时，所有方案都兼顾了蛋白质的补充，支持增肌。\n3.  **实现可持续性**：健康的增重不是靠暴饮暴食。通过在日常饮食中做出这些聪明的“替换”和“添加”，您可以在不显著改变饮食习惯或感到过度腹胀的情况下，稳步增加热量摄入，使增重计划更容易长期坚持。\n\n请记住，在调整饮食的同时，结合适量的力量训练（如举重、自重训练），可以确保增加的热量更多地用于合成肌肉，从而实现真正健康、体态优美的增重。同时，务必达成每日2600ml的饮水目标，以支持新陈代谢。', NULL, 'text', '2026-04-12 16:21:01');
INSERT INTO `assistant_message` VALUES (4, 7, 1, 'user', '我不太喜欢鸡胸肉，有没有其他高蛋白替代？', NULL, 'text', '2026-04-12 18:27:59');
INSERT INTO `assistant_message` VALUES (5, 7, 1, 'context', '请结合用户健康与饮食目标提供食材替换建议：\n健康评估：，年龄 22，性别 男，身高 170cm，体重 50.7kg，BMI 17.543252595155714，活动水平 轻度活动，过敏信息 --，慢性病 --\n饮食目标：，目标类型 健康增重，目标热量 2474kcal，蛋白质目标 148g，碳水目标 297g，脂肪目标 77g，水分目标 2600ml\n用户问题：我不太喜欢鸡胸肉，有没有其他高蛋白替代？\n说明：请优先给出替代食材、营养差异与使用建议。', NULL, 'context', '2026-04-12 18:27:59');
INSERT INTO `assistant_message` VALUES (6, 7, 1, 'assistant', '针对您健康增重的目标，并希望寻找鸡胸肉以外的优质高蛋白替代品，我为您推荐以下几种方案。这些替代品都能有效帮助您增加热量和蛋白质摄入，同时兼顾营养密度和增重效率。\n\n### 推荐的高蛋白替代方案\n\n1.  **三文鱼（或其他富含脂肪的鱼类，如鲭鱼、鳟鱼）**\n    *   **营养差异与优势**：相比鸡胸肉（低脂高蛋白），三文鱼不仅提供优质蛋白质，还富含对心脏和大脑有益的Omega-3脂肪酸，以及更高的健康脂肪。这能显著增加每餐的热量密度，更符合您“健康增重”中需要适量增加健康脂肪摄入（目标77g/天）的需求。\n    *   **使用建议**：每周安排2-3次。可以香煎、烤箱烤制，搭配糙米和大量蔬菜，制作成营养均衡的一餐。一份150克的三文鱼排可提供约30克蛋白质和20克优质脂肪。\n\n2.  **瘦牛肉（如牛里脊、牛腱肉）**\n    *   **营养差异与优势**：瘦牛肉是蛋白质、铁、锌和维生素B12的极佳来源，尤其是血红素铁，吸收率高，有助于改善可能因体重偏低而伴随的气血不足问题。其脂肪含量高于鸡胸肉但可控，能提供更丰富的风味和满足感，促进食欲。\n    *   **使用建议**：选择肉眼可见脂肪较少的部位。可切片用于快炒（如青椒牛柳），或切块用于炖煮（如番茄炖牛腩），搭配土豆等根茎类蔬菜，能同时补充碳水化合物。\n\n3.  **鸡蛋（全蛋）**\n    *   **营养差异与优势**：鸡蛋是“完全蛋白质”的标杆，生物利用率极高。与只吃蛋白相比，**食用全蛋**对您增重更为有利，因为蛋黄富含维生素A、D、E、K以及卵磷脂和健康脂肪，能大幅提升单餐的热量和营养密度。\n    *   **使用建议**：作为最便捷的蛋白质来源，可以每天食用2-3个全蛋。做法多样：水煮蛋作为加餐，炒蛋、蛋卷作为早餐，或煎蛋加入面条、米饭中。\n\n4.  **希腊酸奶/茅屋芝士**\n    *   **营养差异与优势**：这类乳制品经过过滤，蛋白质浓度远高于普通酸奶，同时含有丰富的钙质。选择全脂版本可以额外增加健康脂肪和热量。它们口感醇厚，易于消化，非常适合作为加餐或餐后点心。\n    *   **使用建议**：希腊酸奶可以搭配坚果、蜂蜜和水果制成高蛋白零食；茅屋芝士可以涂抹在全麦面包上，或拌入沙拉中。\n\n### 为什么这些替代方案适合您？\n\n您的核心目标是**健康增重**。当前BMI为17.5，属于体重过轻范围，因此您的饮食策略需要“双管齐下”：**一是确保充足的热量盈余（目标2474大卡），二是保证足够的蛋白质摄入（目标148克）以支持肌肉合成，而非仅仅增加脂肪。**\n\n*   **针对热量需求**：鸡胸肉以“低脂高蛋白”著称，这对于减脂人群是优点，但对于需要增重的您来说，热量密度可能不足。我推荐的**三文鱼、瘦牛肉、全蛋和全脂乳制品**，在提供等量蛋白质的同时，能带来更多的健康脂肪和总体热量，帮助您更高效地达到每日热量目标。\n*   **针对营养强化**：体重过轻有时可能伴随微量营养素摄入不足。瘦牛肉补铁、锌，三文鱼补Omega-3，全蛋和乳制品补多种维生素和钙，这些都能全面提升您的营养状况，支持新陈代谢和整体健康，为健康增重打下坚实基础。\n*   **实践建议**：在采用这些替代品时，请务必将其纳入均衡的餐盘：即“优质蛋白质 + 复合碳水化合物（如糙米、燕麦、红薯）+ 大量蔬菜 + 健康脂肪”。同时，坚持每日饮水2600毫升，并配合适量的力量训练，可以最大程度地将增加的热量和蛋白质导向肌肉生长，实现健康体重的增长。\n\n希望这些具体的替代方案和建议能帮助您丰富饮食，顺利达成健康增重的目标。', NULL, 'text', '2026-04-12 18:28:23');
INSERT INTO `assistant_message` VALUES (7, 7, 1, 'user', '没有鸡胸肉怎么办', NULL, 'text', '2026-04-12 18:28:41');
INSERT INTO `assistant_message` VALUES (8, 7, 1, 'context', '请结合用户健康与饮食目标提供食材替换建议：\n健康评估：，年龄 22，性别 男，身高 170cm，体重 50.7kg，BMI 17.543252595155714，活动水平 轻度活动，过敏信息 --，慢性病 --\n饮食目标：，目标类型 健康增重，目标热量 2474kcal，蛋白质目标 148g，碳水目标 297g，脂肪目标 77g，水分目标 2600ml\n用户问题：没有鸡胸肉怎么办\n说明：请优先给出替代食材、营养差异与使用建议。', NULL, 'context', '2026-04-12 18:28:41');
INSERT INTO `assistant_message` VALUES (9, 7, 1, 'assistant', '针对您“没有鸡胸肉怎么办”的问题，结合您健康增重的目标，我为您推荐几种高蛋白、高热量的优质替代方案，以帮助您更高效地达成每日营养目标。\n\n**结论：** 您可以优先选择去皮鸡腿肉、瘦牛肉（如牛里脊）或三文鱼作为替代。如果追求便捷，也可选择金枪鱼罐头（水浸或油浸）或鸡蛋/蛋白粉。\n\n**为什么这些替代方案适合您？**\n您的BMI为17.5，属于体重过轻范围，核心目标是“健康增重”。这意味着您需要在保证充足蛋白质（每日148g）来促进肌肉合成的同时，摄入足够的热量（每日2474kcal）来增加体重。鸡胸肉的核心价值在于其“高蛋白、低脂肪”，但对于增重而言，适当提高脂肪摄入以增加热量密度是更有效的策略。因此，我推荐的替代品在提供优质蛋白的基础上，部分选项的热量或脂肪含量更高，能更好地服务于您的增重目标。\n\n**具体替代方案、营养差异与使用建议：**\n\n1.  **去皮鸡腿肉**\n    *   **营养差异**：与鸡胸肉相比，鸡腿肉的脂肪含量更高（约是鸡胸肉的2-3倍），因此热量也更高。蛋白质含量略低，但依然是优质蛋白来源。其肉质更嫩，口感更佳。\n    *   **使用建议**：这是最接近的替代品。烹饪时去皮可控制脂肪量，但保留一部分或全部鸡皮能显著增加热量摄入，非常适合您。建议采用烤、煎或炖的方式。\n\n2.  **瘦牛肉（如牛里脊、牛腱）**\n    *   **营养差异**：牛肉富含优质蛋白、肌酸和易于吸收的铁（血红素铁），对增肌和改善体能很有帮助。其脂肪含量因部位而异，选择瘦牛肉时蛋白质含量与鸡胸肉相当，但热量通常稍高，且富含B族维生素和锌。\n    *   **使用建议**：选择肉眼可见脂肪较少的部位。可以切成条状快炒、做成牛肉饼或慢炖，搭配主食一起食用，能有效提升一餐的总热量和营养密度。\n\n3.  **三文鱼等富含脂肪的鱼类**\n    *   **营养差异**：三文鱼不仅提供优质蛋白，还富含Omega-3不饱和脂肪酸（EPA和DHA），有助于抗炎和心血管健康。其热量密度高于鸡胸肉，主要来自健康脂肪，是“健康增重”的绝佳选择。\n    *   **使用建议**：每周安排2-3次。用烤箱烘烤或香煎即可，烹饪简单。搭配牛油果或橄榄油烹调，能进一步增加健康脂肪的摄入。\n\n4.  **便捷替代方案：金枪鱼罐头或鸡蛋/蛋白粉**\n    *   **营养差异与使用建议**：\n        *   **金枪鱼罐头**：**水浸罐头**蛋白质极高、脂肪和热量极低，可作为纯蛋白质补充，但您需要额外搭配健康脂肪（如拌入橄榄油、坚果或鳄梨）。**油浸罐头**则直接提供了更高的热量，更省事。\n        *   **鸡蛋**：全蛋是营养最全面的食物之一。蛋白部分几乎为纯蛋白质，蛋黄则富含脂肪、维生素和矿物质。对于增重的您，**强烈建议食用全蛋**，以获取全部营养和热量。\n        *   **蛋白粉**：乳清蛋白或植物蛋白粉是快速、便捷补充蛋白质的途径，尤其适合在加餐或训练后补充。可以将其与牛奶、香蕉、花生酱等混合制成奶昔，能轻松制作出一杯高蛋白、高热量的饮品。\n\n**总结建议**：在您的增重计划中，不必拘泥于鸡胸肉这一种食材。交替使用上述肉类、鱼类，并善用鸡蛋和蛋白粉，不仅能满足蛋白质需求，还能通过不同食物来源的脂肪和微量营养素，让饮食更丰富、可持续，从而更健康、有效地增加体重。请务必在每日饮食中搭配足量的主食（碳水）和蔬菜，以实现全面的营养均衡。', NULL, 'text', '2026-04-12 18:29:03');
INSERT INTO `assistant_message` VALUES (10, 7, 1, 'user', '我晚上要吃晚餐，有什么健康的替代建议？', NULL, 'text', '2026-04-12 18:44:03');
INSERT INTO `assistant_message` VALUES (11, 7, 1, 'context', '请结合用户健康与饮食目标提供食材替换建议：\n健康评估：，年龄 22，性别 男，身高 170cm，体重 50.7kg，BMI 17.543252595155714，活动水平 轻度活动，过敏信息 --，慢性病 --\n饮食目标：，目标类型 健康增重，目标热量 2474kcal，蛋白质目标 148g，碳水目标 297g，脂肪目标 77g，水分目标 2600ml\n用户问题：我晚上要吃晚餐，有什么健康的替代建议？\n说明：请优先给出替代食材、营养差异与使用建议。', NULL, 'context', '2026-04-12 18:44:03');
INSERT INTO `assistant_message` VALUES (12, 7, 1, 'assistant', '根据你的健康增重目标和当前偏瘦的体质（BMI约17.5），晚餐的替代建议应聚焦于在保证营养均衡的前提下，**增加优质热量和蛋白质的摄入**，同时确保食物易于消化，避免影响夜间睡眠。\n\n以下是几个具体的晚餐食材替代与搭配方案：\n\n**1. 主食替代：用杂粮饭或全麦面食替代白米饭/白面条**\n*   **替代示例**：将白米饭换成“糙米+小米+白米”混合的杂粮饭，或将普通白面条换成全麦意大利面或荞麦面。\n*   **营养差异与优势**：杂粮和全麦制品富含B族维生素、膳食纤维和矿物质，能提供更持久的能量，避免血糖快速波动。虽然热量与精制主食相近，但营养密度更高，有助于在增重的同时改善整体营养状况。\n*   **使用建议**：初期可以按1:1的比例混合精米和杂粮，让肠胃适应。搭配时，可以比平时多吃小半碗，以温和增加碳水化合物的摄入，帮助你接近每日297克的碳水目标。\n\n**2. 蛋白质来源替代：用脂肪含量稍高的优质蛋白替代纯瘦肉**\n*   **替代示例**：将鸡胸肉替换为去皮的鸡腿肉或三文鱼；将纯瘦牛肉替换为肥瘦相间的牛腩（炖煮方式）；或在菜肴中加入一些坚果（如杏仁片、碎核桃）。\n*   **营养差异与优势**：鸡腿肉、三文鱼和牛腩在提供足量蛋白质（支持肌肉合成，对你达成148克蛋白质目标至关重要）的同时，含有更多健康脂肪，能有效提升餐食的热量密度。坚果则额外提供了维生素E和矿物质。\n*   **使用建议**：烹饪时可采用蒸、炖、烤的方式，避免油炸。例如，用烤箱烤三文鱼配芦笋，或用番茄炖牛腩。每周安排2-3次鱼类，特别是深海鱼，以补充Omega-3脂肪酸。\n\n**3. 菜肴搭配升级：在蔬菜中增加“热量加成”**\n*   **替代示例**：将清炒蔬菜改为“蒜蓉橄榄油炒蔬菜”，或在蔬菜沙拉中添加牛油果、奶酪碎和水煮蛋。\n*   **营养差异与优势**：橄榄油、牛油果、奶酪是健康脂肪的优秀来源，能大幅增加一餐的总热量和满足感，而不需要增加过多的食物体积。这对于胃口可能不大的增重者来说非常高效。\n*   **使用建议**：在晚餐的蔬菜部分，用一汤匙（约15毫升）特级初榨橄榄油来烹炒或凉拌。半个牛油果或一小把奶酪碎就能为沙拉增加近百千卡的热量和丰富口感。\n\n**为什么这些替代方案特别适合你？**\n\n你的核心目标是**健康增重**，这意味着需要创造约2474千卡的每日热量盈余，并重点保障蛋白质摄入以增加肌肉而非纯脂肪。你的BMI处于偏低范围，需要营养密集且热量充足的食物。\n\n1.  **针对热量需求**：上述替代方案通过引入健康脂肪（如橄榄油、坚果、鱼类脂肪）和复合碳水化合物，在不显著增加胃部负担的前提下，巧妙地提高了晚餐的热量密度，帮助你更轻松地接近每日热量目标。\n2.  **针对蛋白质目标**：方案强调将蛋白质来源“升级”为兼顾蛋白质与热量的选项（如鸡腿肉、三文鱼），并建议在配菜中加入奶酪、鸡蛋等，能更高效地支持你达成148克的高蛋白目标，促进体重增长向瘦体重（肌肉）倾斜。\n3.  **整体健康考量**：你无过敏和慢病记录，因此选择范围较广。方案注重食材多样性和营养均衡，补充了全谷物、健康脂肪和膳食纤维，有助于在增重期间维持良好的消化代谢和整体健康。\n\n**最后提醒**：晚餐不宜过晚或过饱，建议睡前2-3小时完成。如果晚餐后仍有热量缺口，可以考虑在睡前1小时补充一小杯酸奶或一份水果，作为温和的加餐。同时，务必结合规律的力量训练，才能将多余的热量和蛋白质有效转化为肌肉，实现真正的健康增重。', NULL, 'text', '2026-04-12 18:44:25');

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
INSERT INTO `diet_goal` VALUES (1, 1, 'healthy_weight_gain', 60, 2474, 24, 48, 28, 148, 297, 77, 2600, 1, '2026-03-11', '2026-08-11', 1, '22:18:00', '2026-03-10 22:36:26', '2026-03-10 22:36:26');
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
  `is_deleted` tinyint(4) NULL DEFAULT 0 COMMENT '是否软删除: 0-否 1-是',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `diet_record_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of diet_record
-- ----------------------------
INSERT INTO `diet_record` VALUES (6, 1, '2026-03-25', 'breakfast', NULL, 0, 0, 0, 0, NULL, NULL, '由食谱推荐一键加入：金枪鱼全麦三明治', 1, '2026-03-26 00:32:47', '2026-03-26 00:38:24');
INSERT INTO `diet_record` VALUES (7, 1, '2026-03-25', 'lunch', NULL, 454.6, 33.69, 36.18000000000001, 19.31, NULL, NULL, '由食谱推荐一键加入：三文鱼藜麦温沙拉', 0, '2026-03-26 00:38:33', '2026-03-26 00:38:33');
INSERT INTO `diet_record` VALUES (8, 1, '2026-04-01', 'breakfast', NULL, 312.95, 13.37, 40.42, 11.780000000000001, NULL, NULL, '由食谱推荐一键加入：无糖酸奶蓝莓燕麦杯', 0, '2026-04-01 19:31:00', '2026-04-01 19:31:00');
INSERT INTO `diet_record` VALUES (9, 1, '2026-04-03', 'dinner', NULL, 486, 34.81999999999999, 46.440000000000005, 18.339999999999996, NULL, NULL, '由食谱推荐一键加入：瘦牛肉藜麦饭', 0, '2026-04-03 16:03:21', '2026-04-03 16:03:21');

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
  `recipe_id` bigint(20) NULL DEFAULT NULL COMMENT '来源食谱ID',
  `is_custom` tinyint(4) NULL DEFAULT 0 COMMENT '是否自定义食材',
  `is_deleted` tinyint(4) NULL DEFAULT 0 COMMENT '是否软删除: 0-否 1-是',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `record_id`(`record_id`) USING BTREE,
  INDEX `ingredient_id`(`ingredient_id`) USING BTREE,
  INDEX `recipe_id`(`recipe_id`) USING BTREE,
  CONSTRAINT `diet_record_detail_ibfk_1` FOREIGN KEY (`record_id`) REFERENCES `diet_record` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `diet_record_detail_ibfk_2` FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `diet_record_detail_ibfk_3` FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 23 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of diet_record_detail
-- ----------------------------
INSERT INTO `diet_record_detail` VALUES (7, 6, 49, '金枪鱼', NULL, 1, 'g', 0, 0, 0, 0, 104, 0, 1);
INSERT INTO `diet_record_detail` VALUES (8, 6, 3, '全麦面包', NULL, 1, 'g', 0, 0, 0, 0, 104, 0, 1);
INSERT INTO `diet_record_detail` VALUES (9, 6, 52, '生菜', NULL, 1, 'g', 0, 0, 0, 0, 104, 0, 1);
INSERT INTO `diet_record_detail` VALUES (10, 6, 30, '番茄', NULL, 1, 'g', 0, 0, 0, 0, 104, 0, 1);
INSERT INTO `diet_record_detail` VALUES (11, 7, 43, '藜麦', NULL, 50, 'g', 184, 7.05, 32.1, 3.05, 112, 0, 0);
INSERT INTO `diet_record_detail` VALUES (12, 7, 48, '三文鱼', NULL, 120, 'g', 249.6, 24.479999999999997, 0, 16.08, 112, 0, 0);
INSERT INTO `diet_record_detail` VALUES (13, 7, 52, '生菜', NULL, 60, 'g', 9, 0.84, 1.74, 0.12, 112, 0, 0);
INSERT INTO `diet_record_detail` VALUES (14, 7, 57, '芦笋', NULL, 60, 'g', 12, 1.32, 2.34, 0.06, 112, 0, 0);
INSERT INTO `diet_record_detail` VALUES (15, 8, 64, '无糖酸奶', NULL, 150, 'g', 93, 5.25, 7.050000000000001, 4.800000000000001, 103, 0, 0);
INSERT INTO `diet_record_detail` VALUES (16, 8, 4, '燕麦', NULL, 35, 'g', 136.14999999999998, 5.949999999999999, 23.099999999999998, 2.4499999999999997, 103, 0, 0);
INSERT INTO `diet_record_detail` VALUES (17, 8, 58, '蓝莓', NULL, 50, 'g', 28.5, 0.35, 7.25, 0.15, 103, 0, 0);
INSERT INTO `diet_record_detail` VALUES (18, 8, 66, '腰果', NULL, 10, 'g', 55.300000000000004, 1.82, 3.02, 4.38, 103, 0, 0);
INSERT INTO `diet_record_detail` VALUES (19, 9, 43, '藜麦', NULL, 60, 'g', 220.79999999999998, 8.459999999999999, 38.52, 3.6599999999999997, 105, 0, 0);
INSERT INTO `diet_record_detail` VALUES (20, 9, 50, '瘦牛肉', NULL, 120, 'g', 229.2, 24.24, 0, 14.399999999999999, 105, 0, 0);
INSERT INTO `diet_record_detail` VALUES (21, 9, 56, '洋葱', NULL, 40, 'g', 15.600000000000001, 0.44000000000000006, 3.7200000000000006, 0.04000000000000001, 105, 0, 0);
INSERT INTO `diet_record_detail` VALUES (22, 9, 26, '西兰花', NULL, 60, 'g', 20.4, 1.68, 4.2, 0.24, 105, 0, 0);

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
  `comment_count` int(11) NULL DEFAULT 0 COMMENT '评论数',
  `share_count` int(11) NULL DEFAULT 0,
  `publish_date` date NULL DEFAULT NULL,
  `status` tinyint(4) NULL DEFAULT 1 COMMENT '状态: 0-草稿, 1-已发布',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2038627116093902854 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of health_article
-- ----------------------------
INSERT INTO `health_article` VALUES (1, '控糖饮食指南', '控糖饮食对于预防糖尿病和维持健康体重非常重要', '控糖饮食对于预防糖尿病和维持健康体重非常重要。建议减少高GI食物的摄入，选择低GI食物，如全谷物、蔬菜等。同时要注意控制每日总糖摄入量，包括蔗糖、果糖等添加糖。', NULL, '饮食指南', '控糖，糖尿病，健康', '营养师小王', '糖尿病患者、肥胖人群', '控糖', 28, 0, 1, 0, '2024-01-01', 1, '2026-03-08 17:04:36', '2026-03-30 23:22:09');
INSERT INTO `health_article` VALUES (2, '蛋白质摄入的重要性', '蛋白质是身体的重要组成部分，对于肌肉生长和修复至关重要', '蛋白质是身体的重要组成部分，对于肌肉生长和修复至关重要。建议成年人每公斤体重摄入1-1.2克蛋白质。优质蛋白质来源包括鸡胸肉、鱼、蛋、奶制品和豆制品。', NULL, '营养知识', '蛋白质，肌肉，健康', '营养师小李', '健身人群、增肌人群', '增肌', 8, 0, 0, 0, '2024-01-02', 1, '2026-03-08 17:04:36', '2026-03-30 23:22:16');
INSERT INTO `health_article` VALUES (3, '健康减肥的正确方法', '健康减肥需要合理控制饮食并结合适当的运动', '健康减肥需要合理控制饮食并结合适当的运动。建议每日热量摄入控制在基础代谢率的1.2-1.5倍，同时保证营养均衡。运动方面建议每周进行150分钟中等强度有氧运动。', NULL, '减肥指南', '减肥，健康，运动', '健身教练小张', '肥胖人群', '减肥', 2, 0, 0, 0, '2024-01-03', 1, '2026-03-08 17:04:36', '2026-03-30 23:22:22');
INSERT INTO `health_article` VALUES (4, '增肌饮食策略', '增肌需要足够的蛋白质和热量摄入，同时结合力量训练', '增肌需要足够的蛋白质和热量摄入，同时结合力量训练。建议每公斤体重摄入1.6-2.2克蛋白质，在训练后30分钟内补充蛋白质效果最佳。碳水化合物是训练能量的主要来源，也要保证充足摄入。', NULL, '增肌指南', '增肌，蛋白质，力量训练', '健身教练小王', '健身人群', '增肌', 2, 0, 0, 0, '2024-01-04', 1, '2026-03-08 17:04:36', '2026-03-30 23:22:27');
INSERT INTO `health_article` VALUES (5, '饮食误区大揭秘', '常见的饮食误区包括过度节食、偏食等，这些都会影响健康', '常见的饮食误区包括：1.过度节食导致基础代谢下降；2.只吃蔬菜水果导致蛋白质缺乏；3.不吃主食导致碳水不足；4.迷信减肥药和减肥产品。正确做法是均衡饮食，适量运动。', NULL, '饮食误区', '误区，健康，饮食', '营养师小陈', '所有人群', '通用', 3, 0, 0, 0, '2024-01-05', 1, '2026-03-08 17:04:36', '2026-03-30 23:22:31');
INSERT INTO `health_article` VALUES (6, '高血压饮食建议', '高血压患者应该如何调整饮食结构', '高血压患者应该：1.限制钠盐摄入，每日不超过5克；2.增加钾的摄入，多吃蔬菜水果；3.控制脂肪摄入，减少动物内脏；4.戒烟限酒；5.保持规律作息。', NULL, '饮食指南', '高血压，心血管，饮食', '营养师小李', '高血压人群', '通用', 2, 0, 0, 0, '2024-01-06', 1, '2026-03-08 17:04:36', '2026-03-30 23:21:23');
INSERT INTO `health_article` VALUES (7, '如何科学补水', '科学补水对于维持身体健康至关重要', '科学补水建议：1.每日饮水1500-2000ml；2.运动前半小时补充300ml水；3.运动中每15-20分钟补充100-150ml；4.运动后根据体重丢失量补充；5.养成主动喝水习惯，不要等口渴再喝。', NULL, '营养知识', '补水，健康，饮水', '营养师小王', '所有人群', '通用', 3, 0, 0, 0, '2024-01-07', 1, '2026-03-08 17:04:36', '2026-03-30 23:21:16');
INSERT INTO `health_article` VALUES (2038627116093902850, '如何科学减肥', '如何健康减肥', '如何健康减肥', NULL, '健康知识', '减肥，健康', '刘俊豪', NULL, '减肥减脂', 1, 0, 0, 0, '2026-03-30', 1, '2026-03-30 22:39:15', '2026-03-30 22:39:15');
INSERT INTO `health_article` VALUES (2038627116093902851, '糖尿病', '糖尿病', '糖尿病', NULL, '健康知识', '糖尿病', '刘俊豪', NULL, '控糖饮食', 3, 0, 0, 0, '2026-03-30', 1, '2026-03-30 23:23:22', '2026-03-30 23:23:22');
INSERT INTO `health_article` VALUES (2038627116093902852, '大苏打', '大苏打啊啊是的', '大苏打啊啊是的', NULL, '健康知识', '健康，蛋白质、减脂，花生酱，牛肉', '刘俊豪', NULL, '维持体重', 1, 0, 0, 0, '2026-03-30', 1, '2026-03-30 23:38:56', '2026-03-30 23:38:56');
INSERT INTO `health_article` VALUES (2038627116093902853, '安德森哥特人是', '地方撒给', '地方撒给', NULL, '饮食指南', '规律，自律，健身，蛋白粉，碳水，精致碳水', '刘俊豪', NULL, '减肥减脂', 8, 1, 0, 0, '2026-03-30', 1, '2026-03-30 23:40:09', '2026-03-30 23:40:09');

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
  `chronic_diseases` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '慢性疾病',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `health_info_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of health_info
-- ----------------------------
INSERT INTO `health_info` VALUES (1, 1, 22, '男', 170, 50.7, 17.543252595155714, 1459, '120/80', 10, 'lightly_active', 20, '骑行', '', '2026-03-10 20:28:28', '2026-03-10 20:28:28');
INSERT INTO `health_info` VALUES (2, 2, 25, '男', 175, 60, 19.591836734693878, NULL, '120/80', 5, 'moderately_active', 40, '跑步', '', '2026-03-15 22:35:05', '2026-03-15 22:35:05');
INSERT INTO `health_info` VALUES (3, 3, 24, '男', 175, 65, 21.224489795918366, NULL, '120/80', 5, 'sedentary', 10, '其他', '', '2026-03-18 00:07:31', '2026-03-18 00:07:31');

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
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

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
INSERT INTO `health_info_history` VALUES (8, 1, 50.5, 17.474048442906575, 20, '2026-03-23', '2026-03-23 23:02:54');
INSERT INTO `health_info_history` VALUES (9, 1, 50.7, 17.543252595155714, 20, '2026-03-23', '2026-03-23 23:03:35');

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
) ENGINE = InnoDB AUTO_INCREMENT = 68 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

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
INSERT INTO `ingredient` VALUES (43, '藜麦', '主食', NULL, 368, 14.1, 64.2, 6.1, 7, NULL, NULL, 53, NULL, NULL, NULL, '高蛋白高纤维全谷物', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (44, '土豆', '主食', NULL, 77, 2, 17.2, 0.1, 2.2, NULL, NULL, 62, NULL, NULL, NULL, '常见复合碳水食材', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (45, '南瓜', '主食', NULL, 26, 1, 6.5, 0.1, 0.5, NULL, NULL, 75, NULL, NULL, NULL, '低脂低热量、富含胡萝卜素', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (46, '小米', '主食', NULL, 361, 11, 75, 3.1, 1.6, NULL, NULL, 71, NULL, NULL, NULL, '适合熬粥和温和饮食', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (47, '馒头', '主食', NULL, 223, 7, 47, 1.1, 1.3, NULL, NULL, 88, NULL, NULL, NULL, '常见中式主食', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (48, '三文鱼', '肉类', NULL, 208, 20.4, 0, 13.4, 0, NULL, NULL, 0, 55, NULL, NULL, '优质蛋白和不饱和脂肪来源', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (49, '金枪鱼', '肉类', NULL, 132, 28, 0, 1.3, 0, NULL, NULL, 0, 38, NULL, NULL, '低脂高蛋白海鱼', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (50, '瘦牛肉', '肉类', NULL, 191, 20.2, 0, 12, 0, NULL, NULL, 0, 58, NULL, NULL, '富含铁和优质蛋白', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (51, '里脊肉', '肉类', NULL, 143, 21, 0, 6.2, 0, NULL, NULL, 0, 62, NULL, NULL, '相对低脂的猪肉部位', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (52, '生菜', '蔬菜', NULL, 15, 1.4, 2.9, 0.2, 1.1, NULL, NULL, 15, NULL, NULL, NULL, '适合沙拉和轻食搭配', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (53, '紫甘蓝', '蔬菜', NULL, 31, 1.4, 7.4, 0.2, 2.1, NULL, NULL, 15, NULL, NULL, NULL, '富含花青素和膳食纤维', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (54, '芹菜', '蔬菜', NULL, 16, 0.8, 3, 0.2, 1.4, NULL, NULL, 15, NULL, NULL, NULL, '适合低盐低脂饮食', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (55, '冬瓜', '蔬菜', NULL, 11, 0.4, 2.6, 0.2, 0.7, NULL, NULL, 15, NULL, NULL, NULL, '清淡低热量，适合汤品', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (56, '洋葱', '蔬菜', NULL, 39, 1.1, 9.3, 0.1, 1.7, NULL, NULL, 15, NULL, NULL, NULL, '常用增香蔬菜', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (57, '芦笋', '蔬菜', NULL, 20, 2.2, 3.9, 0.1, 2.1, NULL, NULL, 15, NULL, NULL, NULL, '高纤维低热量蔬菜', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (58, '蓝莓', '水果', NULL, 57, 0.7, 14.5, 0.3, 2.4, NULL, NULL, 53, NULL, NULL, NULL, '富含花青素的低热量水果', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (59, '猕猴桃', '水果', NULL, 61, 1.1, 14.7, 0.5, 3, NULL, NULL, 52, NULL, NULL, NULL, '维生素 C 较丰富', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (60, '火龙果', '水果', NULL, 51, 1.1, 13, 0.2, 1.6, NULL, NULL, 48, NULL, NULL, NULL, '口感清爽，适合轻食搭配', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (61, '牛油果', '水果', NULL, 160, 2, 8.5, 14.7, 6.7, NULL, NULL, 10, NULL, NULL, NULL, '富含健康脂肪', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (62, '黑豆', '豆制品', NULL, 341, 21.6, 62.4, 1.4, 15.5, NULL, NULL, 30, NULL, NULL, NULL, '高蛋白高纤维豆类', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (63, '腐竹', '豆制品', NULL, 461, 44.6, 15.3, 21.7, 1, NULL, NULL, 30, NULL, NULL, NULL, '植物蛋白含量高', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (64, '无糖酸奶', '乳制品', NULL, 62, 3.5, 4.7, 3.2, 0, NULL, NULL, 35, 12, NULL, NULL, '适合控糖和轻食搭配', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (65, '低脂牛奶', '乳制品', NULL, 46, 3.4, 4.8, 1.5, 0, NULL, NULL, 27, 6, NULL, NULL, '适合控制脂肪摄入', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (66, '腰果', '坚果', NULL, 553, 18.2, 30.2, 43.8, 3.3, NULL, NULL, 22, NULL, NULL, NULL, '可少量作为加餐坚果', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `ingredient` VALUES (67, '开心果', '坚果', NULL, 562, 20.3, 27.2, 45.4, 10.6, NULL, NULL, 15, NULL, NULL, NULL, '富含不饱和脂肪酸和膳食纤维', NULL, 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');

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
  `is_deleted` tinyint(4) NULL DEFAULT 0 COMMENT '是否软删除: 0-否 1-是',
  `read_time` datetime NULL DEFAULT NULL,
  `send_time` datetime NULL DEFAULT NULL COMMENT '发送时间',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 36 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of notification
-- ----------------------------
INSERT INTO `notification` VALUES (1, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 18:21 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 1, '2026-03-23 23:29:12', '2026-03-23 23:28:10', '2026-03-23 23:28:10');
INSERT INTO `notification` VALUES (2, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 1, '2026-03-24 21:56:00', '2026-03-23 23:28:10', '2026-03-23 23:28:10');
INSERT INTO `notification` VALUES (3, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 18:21 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 1, '2026-03-24 21:43:53', '2026-03-24 21:43:32', '2026-03-24 21:43:31');
INSERT INTO `notification` VALUES (4, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 1, '2026-03-24 21:55:59', '2026-03-24 21:43:32', '2026-03-24 21:43:31');
INSERT INTO `notification` VALUES (5, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 1, '2026-03-25 23:45:14', '2026-03-25 21:36:53', '2026-03-25 21:36:53');
INSERT INTO `notification` VALUES (6, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 22:18 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 1, '2026-03-25 23:45:14', '2026-03-25 23:16:14', '2026-03-25 23:16:14');
INSERT INTO `notification` VALUES (7, 1, 'warning', '饮食误区提醒', '⚠️ 蛋白质摄入不足，建议增加蛋奶肉类的摄入', NULL, 'diet_record', 1, 1, '2026-03-25 23:45:13', '2026-03-25 23:34:46', '2026-03-25 23:34:46');
INSERT INTO `notification` VALUES (8, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 1, '2026-03-26 00:04:59', '2026-03-26 00:00:05', '2026-03-26 00:00:04');
INSERT INTO `notification` VALUES (9, 1, 'warning', '饮食误区提醒', '⚠️ 蛋白质摄入不足，建议增加蛋奶肉类的摄入', NULL, 'diet_record', 1, 1, '2026-03-26 00:04:59', '2026-03-26 00:01:47', '2026-03-26 00:01:47');
INSERT INTO `notification` VALUES (10, 1, 'warning', '饮食误区提醒', '蛋白质摄入不足，建议增加蛋奶肉豆类食物', NULL, 'diet_record', 1, 1, '2026-03-28 22:35:24', '2026-03-28 20:40:55', '2026-03-28 20:40:55');
INSERT INTO `notification` VALUES (11, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 1, '2026-03-28 22:35:25', '2026-03-28 20:40:55', '2026-03-28 20:40:55');
INSERT INTO `notification` VALUES (12, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 22:18 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 1, '2026-03-28 22:35:23', '2026-03-28 22:33:24', '2026-03-28 22:33:24');
INSERT INTO `notification` VALUES (13, 1, 'warning', '饮食误区提醒', '蛋白质摄入不足，建议增加蛋奶肉豆类食物', NULL, 'diet_record', 1, 1, '2026-03-30 22:25:37', '2026-03-30 21:35:19', '2026-03-30 21:35:18');
INSERT INTO `notification` VALUES (14, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 1, '2026-03-30 22:25:36', '2026-03-30 21:35:19', '2026-03-30 21:35:19');
INSERT INTO `notification` VALUES (15, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 22:18 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 1, '2026-03-30 22:25:36', '2026-03-30 22:21:12', '2026-03-30 22:21:12');
INSERT INTO `notification` VALUES (16, 1, 'warning', '饮食误区提醒', '蛋白质摄入不足，建议增加蛋奶肉豆类食物', NULL, 'diet_record', 1, 1, '2026-03-31 21:08:07', '2026-03-31 00:06:18', '2026-03-31 00:06:17');
INSERT INTO `notification` VALUES (17, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 1, '2026-03-31 21:08:07', '2026-03-31 00:06:18', '2026-03-31 00:06:17');
INSERT INTO `notification` VALUES (18, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 22:18 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 1, '2026-04-01 20:27:02', '2026-03-31 22:20:03', '2026-03-31 22:20:03');
INSERT INTO `notification` VALUES (19, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 0, '2026-04-01 20:27:02', '2026-04-01 19:08:02', '2026-04-01 19:08:02');
INSERT INTO `notification` VALUES (20, 1, 'warning', '饮食误区提醒', '蛋白质摄入不足，建议增加蛋奶肉豆类食物', NULL, 'diet_record', 1, 1, '2026-04-01 20:27:02', '2026-04-01 19:31:02', '2026-04-01 19:31:02');
INSERT INTO `notification` VALUES (21, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 22:18 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 1, '2026-04-01 23:38:28', '2026-04-01 23:27:40', '2026-04-01 23:27:40');
INSERT INTO `notification` VALUES (22, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 22:18 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 0, '2026-04-02 22:47:27', '2026-04-01 23:38:36', '2026-04-01 23:38:36');
INSERT INTO `notification` VALUES (23, 1, 'warning', '饮食误区提醒', '蛋白质摄入不足，建议增加蛋奶肉豆类食物', NULL, 'diet_record', 1, 0, '2026-04-02 22:47:27', '2026-04-01 23:38:37', '2026-04-01 23:38:36');
INSERT INTO `notification` VALUES (24, 1, 'warning', '饮食误区提醒', '蛋白质摄入不足，建议增加蛋奶肉豆类食物', NULL, 'diet_record', 1, 0, '2026-04-02 22:47:27', '2026-04-02 21:39:41', '2026-04-02 21:39:41');
INSERT INTO `notification` VALUES (25, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 0, '2026-04-02 22:47:27', '2026-04-02 21:39:41', '2026-04-02 21:39:41');
INSERT INTO `notification` VALUES (26, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 22:18 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 0, '2026-04-02 22:47:27', '2026-04-02 22:32:25', '2026-04-02 22:32:24');
INSERT INTO `notification` VALUES (27, 1, 'warning', '饮食误区提醒', '蛋白质摄入不足，建议增加蛋奶肉豆类食物', NULL, 'diet_record', 1, 0, '2026-04-06 04:27:41', '2026-04-03 13:55:47', '2026-04-03 13:55:46');
INSERT INTO `notification` VALUES (28, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 0, '2026-04-06 04:27:41', '2026-04-03 13:55:47', '2026-04-03 13:55:46');
INSERT INTO `notification` VALUES (29, 1, 'warning', '饮食误区提醒', '蛋白质摄入不足，建议增加蛋奶肉豆类食物', NULL, 'diet_record', 1, 0, '2026-04-06 04:27:41', '2026-04-05 13:40:51', '2026-04-05 13:40:51');
INSERT INTO `notification` VALUES (30, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 0, '2026-04-06 04:27:41', '2026-04-05 13:40:51', '2026-04-05 13:40:51');
INSERT INTO `notification` VALUES (31, 1, 'warning', '饮食误区提醒', '蛋白质摄入不足，建议增加蛋奶肉豆类食物', NULL, 'diet_record', 1, 0, '2026-04-06 04:27:41', '2026-04-06 04:26:43', '2026-04-06 04:26:43');
INSERT INTO `notification` VALUES (32, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 0, '2026-04-06 04:27:41', '2026-04-06 04:26:43', '2026-04-06 04:26:43');
INSERT INTO `notification` VALUES (33, 1, 'diet_reminder', '饮食目标提醒', '你已开启饮食提醒，建议在 22:18 回顾并执行「healthy_weight_gain」计划。', 1, 'diet_goal', 1, 0, '2026-04-12 18:22:43', '2026-04-11 22:40:52', '2026-04-11 22:40:52');
INSERT INTO `notification` VALUES (34, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 0, '2026-04-12 18:22:43', '2026-04-11 22:40:52', '2026-04-11 22:40:52');
INSERT INTO `notification` VALUES (35, 1, 'article_recommend', '健康知识推荐', '为你推荐《控糖饮食指南》，可以帮助你更好地执行当前饮食目标。', 1, 'article', 1, 0, '2026-04-12 18:22:43', '2026-04-12 12:20:57', '2026-04-12 12:20:57');

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
) ENGINE = InnoDB AUTO_INCREMENT = 114 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of recipe
-- ----------------------------
INSERT INTO `recipe` VALUES (101, '藜麦鸡胸能量碗', '高蛋白、低负担的轻食主餐，适合减脂和塑形期。', '午餐', '轻食', 20, '简单', 1, 420, 420, 33, 36, 12, 7, '[\"藜麦煮熟备用\",\"鸡胸肉煎熟切片\",\"生菜和紫甘蓝洗净切丝\",\"将所有食材装碗后拌匀即可\"]', '可加入少量黑胡椒提升风味。', NULL, NULL, NULL, 0, 1, 4.8, 0, 0, 0, '减脂人群、健身人群', '减肥减脂', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (102, '三文鱼牛油果沙拉', '富含优质脂肪与蛋白质，适合控脂和心血管友好型饮食。', '晚餐', '轻食', 18, '简单', 1, 450, 450, 26, 18, 28, 8, '[\"三文鱼煎熟切块\",\"牛油果切丁\",\"生菜和蓝莓洗净备用\",\"所有食材混合后即可食用\"]', '控盐饮食可不加额外沙拉酱。', NULL, NULL, NULL, 0, 1, 4.9, 0, 0, 0, '控脂降脂、老年养生', '控脂降脂', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (103, '无糖酸奶蓝莓燕麦杯', '适合早餐和加餐的低糖高纤组合。', '早餐', '轻食', 10, '简单', 1, 290, 290, 14, 34, 9, 6, '[\"无糖酸奶倒入杯中\",\"加入燕麦\",\"放入蓝莓和少量坚果\",\"冷藏后口感更佳\"]', '控糖人群可减少水果量。', NULL, NULL, NULL, 0, 1, 4.7, 0, 0, 0, '控糖饮食、维持体重', '控糖饮食', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (104, '金枪鱼全麦三明治', '高蛋白便捷早餐，适合上班族和塑形期。', '早餐', '西式', 12, '简单', 1, 360, 360, 28, 31, 11, 5, '[\"全麦面包烘热\",\"金枪鱼沥干后铺在面包上\",\"加入生菜和番茄片\",\"夹好后对半切开\"]', '可搭配低脂牛奶食用。', NULL, NULL, NULL, 0, 1, 4.8, 0, 0, 0, '增肌塑形、维持体重', '增肌塑形', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (105, '瘦牛肉藜麦饭', '高蛋白主餐，适合增肌和健康增重。', '午餐', '中式', 25, '中等', 1, 520, 520, 35, 42, 18, 6, '[\"藜麦煮熟备用\",\"瘦牛肉切片快炒\",\"加入洋葱和西兰花翻炒\",\"与藜麦搭配装盘\"]', '训练日可适当增加藜麦分量。', NULL, NULL, NULL, 0, 1, 4.9, 0, 0, 1, '增肌塑形、健康增重', '健康增重', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (106, '南瓜小米粥', '温和易消化，适合老年养生和胃口较弱人群。', '早餐', '中式', 30, '简单', 1, 240, 240, 6, 46, 2, 3, '[\"南瓜去皮切块\",\"小米淘洗干净\",\"加入适量清水熬煮\",\"煮至软糯即可\"]', '可作为清淡早餐主食。', NULL, NULL, NULL, 0, 1, 4.6, 0, 0, 0, '老年养生、控脂降脂', '老年养生', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (107, '冬瓜虾仁汤', '低热量高蛋白汤品，适合作为晚餐配菜或控脂餐。', '晚餐', '中式', 15, '简单', 1, 180, 180, 24, 8, 3, 2, '[\"冬瓜切片\",\"虾仁焯水备用\",\"锅中加水煮开后放入冬瓜\",\"加入虾仁煮熟调味即可\"]', '控压饮食注意减少盐用量。', NULL, NULL, NULL, 0, 1, 4.7, 0, 0, 0, '控压低盐、减肥减脂', '控压低盐', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (108, '芦笋鸡蛋卷', '营养均衡、制作快捷，适合作为早餐或加餐。', '早餐', '中式', 10, '简单', 1, 230, 230, 16, 9, 14, 2, '[\"鸡蛋打散\",\"芦笋焯水切段\",\"平底锅煎蛋皮\",\"卷入芦笋后切段装盘\"]', '可搭配低脂牛奶增强饱腹感。', NULL, NULL, NULL, 0, 1, 4.6, 0, 0, 0, '儿童成长、维持体重', '儿童成长', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (109, '黑豆豆腐营养碗', '植物蛋白丰富，适合素食和控脂人群。', '午餐', '轻食', 22, '中等', 1, 380, 380, 24, 29, 16, 8, '[\"黑豆提前煮熟\",\"豆腐切块煎至微黄\",\"生菜和紫甘蓝铺底\",\"混合后即可食用\"]', '可加少量柠檬汁提味。', NULL, NULL, NULL, 0, 1, 4.7, 0, 0, 0, '素食偏好、控脂降脂', '控脂降脂', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (110, '里脊肉土豆配芹菜', '中式家常组合，适合日常均衡饮食。', '晚餐', '中式', 20, '简单', 1, 410, 410, 27, 32, 14, 5, '[\"里脊肉切片腌制\",\"土豆切块煮熟\",\"芹菜切段快炒\",\"三种食材组合装盘\"]', '控糖阶段可减少土豆比例。', NULL, NULL, NULL, 0, 1, 4.5, 0, 0, 0, '维持体重、家庭饮食', '维持体重', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (111, '牛油果酸奶水果碗', '清爽型早餐，适合孕妇营养和轻食需求。', '早餐', '轻食', 8, '简单', 1, 310, 310, 11, 26, 17, 7, '[\"将无糖酸奶倒入碗中\",\"牛油果切块\",\"加入蓝莓和猕猴桃\",\"混合后即可食用\"]', '孕妇营养可搭配全麦主食一起吃。', NULL, NULL, NULL, 0, 1, 4.8, 0, 0, 0, '孕妇营养、维持体重', '孕妇营养', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (112, '三文鱼藜麦温沙拉', '兼顾蛋白质和优质脂肪，适合健康增重和塑形。', '午餐', '轻食', 20, '中等', 1, 470, 470, 30, 29, 24, 6, '[\"藜麦煮熟保温\",\"三文鱼煎熟切块\",\"生菜和芦笋焯水\",\"混合食材后趁温热食用\"]', '可作为训练后恢复餐。', NULL, NULL, NULL, 0, 1, 4.9, 0, 0, 0, '增肌塑形、健康增重', '增肌塑形', 1, '2026-03-24 21:40:37', '2026-03-24 21:40:37');
INSERT INTO `recipe` VALUES (113, '西红柿炒鸡蛋', '西红柿鸡蛋', NULL, NULL, 15, '简单', 1, 164, NULL, 13.45, 3.05, 10.7, NULL, '洗干净下锅，翻炒均匀', NULL, '', NULL, 1, 1, 1, 5, 0, 0, 0, NULL, NULL, 1, '2026-04-03 14:26:53', '2026-04-03 14:26:54');

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
) ENGINE = InnoDB AUTO_INCREMENT = 2039952763604975618 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of recipe_ingredient
-- ----------------------------
INSERT INTO `recipe_ingredient` VALUES (1, 101, 43, 50, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (2, 101, 16, 120, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (3, 101, 52, 60, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (4, 101, 53, 40, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (5, 102, 48, 120, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (6, 102, 61, 60, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (7, 102, 52, 80, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (8, 102, 58, 30, 'g', 1, '点缀');
INSERT INTO `recipe_ingredient` VALUES (9, 103, 64, 150, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (10, 103, 4, 35, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (11, 103, 58, 50, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (12, 103, 66, 10, 'g', 1, '少量添加');
INSERT INTO `recipe_ingredient` VALUES (13, 104, 49, 80, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (14, 104, 3, 60, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (15, 104, 52, 40, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (16, 104, 30, 30, 'g', 1, NULL);
INSERT INTO `recipe_ingredient` VALUES (17, 105, 43, 60, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (18, 105, 50, 120, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (19, 105, 56, 40, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (20, 105, 26, 60, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (21, 106, 45, 40, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (22, 106, 46, 35, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (23, 107, 55, 120, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (24, 107, 20, 80, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (25, 108, 57, 80, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (26, 108, 8, 100, 'g', 0, '约两个鸡蛋');
INSERT INTO `recipe_ingredient` VALUES (27, 109, 62, 80, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (28, 109, 38, 120, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (29, 109, 52, 60, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (30, 109, 53, 40, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (31, 110, 51, 120, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (32, 110, 44, 100, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (33, 110, 54, 80, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (34, 111, 64, 120, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (35, 111, 61, 50, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (36, 111, 58, 40, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (37, 111, 59, 60, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (38, 112, 43, 50, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (39, 112, 48, 120, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (40, 112, 52, 60, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (41, 112, 57, 60, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (2039952763567226881, 113, 8, 100, 'g', 0, NULL);
INSERT INTO `recipe_ingredient` VALUES (2039952763604975617, 113, 21, 50, 'g', 0, NULL);

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
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'user' COMMENT '???: user/admin',
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
INSERT INTO `user` VALUES (1, '刘俊豪', '$2a$10$QQmxV20DzWaRkxwmyoYmCOsK8HLWduCDfAxUfkhdagdznYhDiBokS', '2311697186@qq.com', '17840529449', 'data:image/jpeg;base64,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', 'user', 1, '2026-03-10 20:27:38', '2026-03-10 20:27:38');
INSERT INTO `user` VALUES (2, '张三', '$2a$10$rs0vAkSKgVKMWWWSYojuje4dho5mfroXlf9HhF.93/MFFPqXSGvt2', '123456@qq.com', '19330406783', NULL, 'user', 1, '2026-03-15 22:34:49', '2026-03-15 22:34:49');
INSERT INTO `user` VALUES (3, '管理员', '$2a$10$e3hGOVm.MysyEXTZF1f9buOUSVNFAwaXs7IYipFHsnCBRqP3II1Fm', 'admin@qq.com', '15432145678', NULL, 'admin', 1, '2026-03-18 00:07:16', '2026-04-12 13:28:45');

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
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_article_collect
-- ----------------------------
INSERT INTO `user_article_collect` VALUES (1, 1, 1, '2026-03-24 22:07:22');
INSERT INTO `user_article_collect` VALUES (2, 1, 2, '2026-03-24 22:08:06');
INSERT INTO `user_article_collect` VALUES (3, 1, 3, '2026-03-24 22:08:17');
INSERT INTO `user_article_collect` VALUES (4, 1, 4, '2026-03-24 22:08:21');
INSERT INTO `user_article_collect` VALUES (5, 1, 5, '2026-03-24 22:08:24');

-- ----------------------------
-- Table structure for user_article_like
-- ----------------------------
DROP TABLE IF EXISTS `user_article_like`;
CREATE TABLE `user_article_like`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `article_id` bigint(20) NOT NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_article_like`(`user_id`, `article_id`) USING BTREE,
  INDEX `idx_article_like_article`(`article_id`) USING BTREE,
  CONSTRAINT `user_article_like_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `user_article_like_ibfk_2` FOREIGN KEY (`article_id`) REFERENCES `health_article` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_article_like
-- ----------------------------
INSERT INTO `user_article_like` VALUES (1, 1, 2038627116093902853, '2026-04-03 16:40:58');

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
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_recipe_collect
-- ----------------------------
INSERT INTO `user_recipe_collect` VALUES (1, 1, 105, '2026-03-31 22:52:12');

SET FOREIGN_KEY_CHECKS = 1;
