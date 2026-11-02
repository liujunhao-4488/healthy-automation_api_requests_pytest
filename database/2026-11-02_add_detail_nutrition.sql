-- ============================================================
-- 2026-11-02 迁移：给 diet_record_detail 补上 fiber / sugar / sodium / gi
-- ------------------------------------------------------------
-- 背景（联调实测的问题）：
--   DietRecordDetail 实体上这四个字段标了 @TableField(exist = false)，
--   MyBatis-Plus 认为库里没有这些列，insert 时直接跳过、select 也不回填。
--
--   现象：提交明细 fiber=7.77 → POST /record/submit 响应里 totalFiber=7.77
--         （内存对象是对的）→ 但重新 GET /record/list，明细 fiber 一律 0.0，
--         totalFiber 也跟着变 0。膳食纤维、糖、钠、GI 从来没进过库。
--
--   连带影响：DietRecord 的 totalFiber/totalSugar/totalSodium/totalGi 也是
--   @TableField(exist = false)，但那是**每次查询时由 fillRecordDetails()
--   从明细实时重算**的，本来就不该落库。所以只要明细存对了，汇总自动正确，
--   不需要给 diet_record 加列。
--
-- 使用方式（脚本里不用 USE，执行时指定库名）：
--   mysql -uroot -p health_diet      < 2026-11-02_add_detail_nutrition.sql
--   mysql -uroot -p health_diet_test < 2026-11-02_add_detail_nutrition.sql
--
-- 本仓库的 health_diet / health_diet_test 已于 2026-11-02 执行完毕。
-- 脚本是幂等的：已存在的列会被跳过，可以安全重复执行。
-- ============================================================

-- ---------- 幂等辅助：只在列不存在时才 ADD ----------
DROP PROCEDURE IF EXISTS `sp_add_detail_nutrition`;

DELIMITER $$
CREATE PROCEDURE `sp_add_detail_nutrition`()
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS
                 WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'diet_record_detail'
                   AND COLUMN_NAME = 'fiber') THEN
    ALTER TABLE `diet_record_detail`
      ADD COLUMN `fiber`  double DEFAULT NULL COMMENT '膳食纤维(g)' AFTER `fat`;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS
                 WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'diet_record_detail'
                   AND COLUMN_NAME = 'sugar') THEN
    ALTER TABLE `diet_record_detail`
      ADD COLUMN `sugar`  double DEFAULT NULL COMMENT '糖(g)' AFTER `fiber`;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS
                 WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'diet_record_detail'
                   AND COLUMN_NAME = 'sodium') THEN
    ALTER TABLE `diet_record_detail`
      ADD COLUMN `sodium` double DEFAULT NULL COMMENT '钠(mg)' AFTER `sugar`;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS
                 WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'diet_record_detail'
                   AND COLUMN_NAME = 'gi') THEN
    ALTER TABLE `diet_record_detail`
      ADD COLUMN `gi`     double DEFAULT NULL COMMENT '升糖指数' AFTER `sodium`;
  END IF;
END$$
DELIMITER ;

CALL `sp_add_detail_nutrition`();
DROP PROCEDURE IF EXISTS `sp_add_detail_nutrition`;

-- 老数据这四列为 NULL。若希望回填，可按 ingredient_id 从食材库推算：
-- UPDATE diet_record_detail d
--   JOIN ingredient i ON i.id = d.ingredient_id
--    SET d.fiber  = i.fiber_per_100g  * d.quantity / 100,
--        d.sugar  = i.sugar_per_100g  * d.quantity / 100,
--        d.sodium = i.sodium_per_100g * d.quantity / 100,
--        d.gi     = i.gi_value
--  WHERE d.fiber IS NULL AND d.is_deleted = 0;
-- 注：没挂 ingredient_id 的明细无法回填，保持 NULL 即可
--     （enrichDetailNutrition 会在读取时按库值补算）。

-- 验证：
-- SHOW COLUMNS FROM diet_record_detail LIKE 'fiber';
-- SHOW COLUMNS FROM diet_record_detail LIKE 'sugar';
-- SHOW COLUMNS FROM diet_record_detail LIKE 'sodium';
-- SHOW COLUMNS FROM diet_record_detail LIKE 'gi';
