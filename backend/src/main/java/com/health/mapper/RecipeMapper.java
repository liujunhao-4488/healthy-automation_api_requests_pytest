package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.Recipe;
import java.util.List;

/**
 * 食谱Mapper接口
 */
public interface RecipeMapper extends BaseMapper<Recipe> {

    /**
     * 查询用户自定义食谱
     * @param userId 用户ID
     * @return 食谱列表
     */
    List<Recipe> selectCustomByUserId(Long userId);

    /**
     * 根据难度查询食谱
     * @param difficulty 难度级别
     * @return 食谱列表
     */
    List<Recipe> selectByDifficulty(String difficulty);

    /**
     * 根据烹饪时间查询食谱
     * @param maxTime 最大烹饪时间
     * @return 食谱列表
     */
    List<Recipe> selectByMaxCookingTime(Integer maxTime);
}
