package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.RecipeIngredient;
import java.util.List;

/**
 * 食谱食材关联Mapper接口
 */
public interface RecipeIngredientMapper extends BaseMapper<RecipeIngredient> {

    /**
     * 根据食谱ID查询食材关联
     * @param recipeId 食谱ID
     * @return 食材关联列表
     */
    List<RecipeIngredient> selectByRecipeId(Long recipeId);

    /**
     * 根据食材ID查询食谱关联
     * @param ingredientId 食材ID
     * @return 食谱关联列表
     */
    List<RecipeIngredient> selectByIngredientId(Long ingredientId);
}
