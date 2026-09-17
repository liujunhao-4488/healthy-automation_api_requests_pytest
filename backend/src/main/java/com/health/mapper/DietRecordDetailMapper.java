package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.DietRecordDetail;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface DietRecordDetailMapper extends BaseMapper<DietRecordDetail> {

    @Select("SELECT id, record_id, ingredient_id, food_name, quantity, unit, " +
            "calories, protein, carbs, fat, recipe_id, is_custom, is_deleted " +
            "FROM diet_record_detail " +
            "WHERE record_id = #{recordId} AND is_deleted = 0 " +
            "ORDER BY id ASC")
    List<DietRecordDetail> selectByRecordId(Long recordId);

    @Select("SELECT id, record_id, ingredient_id, food_name, quantity, unit, " +
            "calories, protein, carbs, fat, recipe_id, is_custom, is_deleted " +
            "FROM diet_record_detail " +
            "WHERE recipe_id = #{recipeId} AND is_deleted = 0 " +
            "ORDER BY id ASC")
    List<DietRecordDetail> selectByRecipeId(Long recipeId);
}
