package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.RecipeIngredient;
import org.apache.ibatis.annotations.Select;

import java.util.List;

public interface RecipeIngredientMapper extends BaseMapper<RecipeIngredient> {

    @Select("SELECT id, recipe_id, ingredient_id, quantity, unit FROM recipe_ingredient WHERE recipe_id = #{recipeId} ORDER BY id ASC")
    List<RecipeIngredient> selectByRecipeId(Long recipeId);

    @Select("SELECT id, recipe_id, ingredient_id, quantity, unit FROM recipe_ingredient WHERE ingredient_id = #{ingredientId} ORDER BY id ASC")
    List<RecipeIngredient> selectByIngredientId(Long ingredientId);
}
