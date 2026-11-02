package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.DietRecordDetail;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface DietRecordDetailMapper extends BaseMapper<DietRecordDetail> {

    // 2026-11-02 修复：这里的列清单是手写的，之前漏了 fiber / sugar / sodium / gi。
    // 后果：entity 里就算去掉 @TableField(exist=false)、库里也有列、insert 也写进去了，
    // 走 selectByRecordId 读回来依然是 null（再被 enrichDetailNutrition 兜成 0.0），
    // 表现为"写进去了但读不出来"。以后给 diet_record_detail 加列，这里要同步加。
    @Select("SELECT id, record_id, ingredient_id, food_name, quantity, unit, " +
            "calories, protein, carbs, fat, fiber, sugar, sodium, gi, " +
            "recipe_id, is_custom, is_deleted " +
            "FROM diet_record_detail " +
            "WHERE record_id = #{recordId} AND is_deleted = 0 " +
            "ORDER BY id ASC")
    List<DietRecordDetail> selectByRecordId(Long recordId);

    @Select("SELECT id, record_id, ingredient_id, food_name, quantity, unit, " +
            "calories, protein, carbs, fat, fiber, sugar, sodium, gi, " +
            "recipe_id, is_custom, is_deleted " +
            "FROM diet_record_detail " +
            "WHERE recipe_id = #{recipeId} AND is_deleted = 0 " +
            "ORDER BY id ASC")
    List<DietRecordDetail> selectByRecipeId(Long recipeId);
}
