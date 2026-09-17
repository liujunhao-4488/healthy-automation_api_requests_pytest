package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.DietRecord;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.Date;
import java.util.List;

public interface DietRecordMapper extends BaseMapper<DietRecord> {

    @Select("SELECT id, user_id, record_date, meal_type, total_calories, total_protein, total_carbs, total_fat, notes, is_deleted, create_time, update_time " +
        "FROM diet_record WHERE user_id = #{userId} AND is_deleted = 0 AND record_date = #{recordDate} ORDER BY create_time DESC")
    List<DietRecord> selectByUserIdAndDate(@Param("userId") Long userId, @Param("recordDate") Date recordDate);

    @Select("SELECT id, user_id, record_date, meal_type, total_calories, total_protein, total_carbs, total_fat, notes, is_deleted, create_time, update_time " +
        "FROM diet_record WHERE user_id = #{userId} AND is_deleted = 0 AND record_date BETWEEN #{startDate} AND #{endDate} ORDER BY record_date DESC, create_time DESC")
    List<DietRecord> selectByUserIdAndDateRange(@Param("userId") Long userId, @Param("startDate") Date startDate, @Param("endDate") Date endDate);

    @Select("SELECT id, user_id, record_date, meal_type, total_calories, total_protein, total_carbs, total_fat, notes, is_deleted, create_time, update_time " +
        "FROM diet_record WHERE user_id = #{userId} AND is_deleted = 0 AND meal_type = #{mealType} AND record_date BETWEEN #{startDate} AND #{endDate} ORDER BY record_date DESC, create_time DESC")
    List<DietRecord> selectByUserIdAndMealType(
        @Param("userId") Long userId,
        @Param("mealType") String mealType,
        @Param("startDate") Date startDate,
        @Param("endDate") Date endDate
    );
}
