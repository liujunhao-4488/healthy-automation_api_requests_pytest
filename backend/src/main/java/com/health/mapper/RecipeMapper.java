package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.Recipe;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;

/**
 * 食谱Mapper接口
 */
@Mapper
public interface RecipeMapper extends BaseMapper<Recipe> {

    /**
     * 查询用户自定义食谱
     * @param userId 用户ID
     * @return 食谱列表
     */
    @Select("SELECT id, name, description, category, cuisine_type, cooking_time, difficulty, servings, " +
            "total_calories, calories_per_serving, protein, carbs, fat, fiber, instructions, tips, " +
            "image_url, video_url, creator_id, is_custom, is_public, score, score_count, view_count, " +
            "collect_count, suitable_for, goal_type, status, create_time, update_time " +
            "FROM recipe " +
            "WHERE creator_id = #{userId} " +
            "AND is_custom = 1 " +
            "AND status = 1 " +
            "ORDER BY create_time DESC")
    List<Recipe> selectCustomByUserId(@Param("userId") Long userId);

    /**
     * 根据难度查询食谱
     * @param difficulty 难度级别
     * @return 食谱列表
     */
    @Select("SELECT id, name, description, category, cuisine_type, cooking_time, difficulty, servings, " +
            "total_calories, calories_per_serving, protein, carbs, fat, fiber, instructions, tips, " +
            "image_url, video_url, creator_id, is_custom, is_public, score, score_count, view_count, " +
            "collect_count, suitable_for, goal_type, status, create_time, update_time " +
            "FROM recipe " +
            "WHERE difficulty = #{difficulty} " +
            "AND status = 1 " +
            "ORDER BY create_time DESC")
    List<Recipe> selectByDifficulty(@Param("difficulty") String difficulty);

    /**
     * 根据烹饪时间查询食谱
     * @param maxTime 最大烹饪时间
     * @return 食谱列表
     */
    @Select("SELECT id, name, description, category, cuisine_type, cooking_time, difficulty, servings, " +
            "total_calories, calories_per_serving, protein, carbs, fat, fiber, instructions, tips, " +
            "image_url, video_url, creator_id, is_custom, is_public, score, score_count, view_count, " +
            "collect_count, suitable_for, goal_type, status, create_time, update_time " +
            "FROM recipe " +
            "WHERE cooking_time <= #{maxTime} " +
            "AND status = 1 " +
            "ORDER BY cooking_time ASC, create_time DESC")
    List<Recipe> selectByMaxCookingTime(@Param("maxTime") Integer maxTime);
}
