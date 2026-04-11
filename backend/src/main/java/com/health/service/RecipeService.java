package com.health.service;

import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;
import java.util.List;
import java.util.Map;

/**
 * 食谱服务接口
 */
public interface RecipeService {

    /**
     * 获取所有食谱
     * @return 食谱列表
     */
    List<Recipe> getAllRecipes();

    /**
     * 根据ID获取食谱
     * @param id 食谱ID
     * @return 食谱信息
     */
    Recipe getRecipeById(Long id);

    /**
     * 获取食谱的食材列表
     * @param recipeId 食谱ID
     * @return 食材列表
     */
    List<RecipeIngredient> getRecipeIngredients(Long recipeId);

    /**
     * 获取用户自定义食谱
     * @param userId 用户ID
     * @return 食谱列表
     */
    List<Recipe> getCustomRecipes(Long userId);

    /**
     * 搜索食谱
     * @param keyword 搜索关键词
     * @return 食谱列表
     */
    List<Recipe> searchRecipes(String keyword);

    /**
     * 保存食谱
     * @param recipe 食谱信息
     * @param ingredients 食材列表
     * @return 保存后的食谱
     */
    Recipe saveRecipe(Recipe recipe, List<RecipeIngredient> ingredients);

    /**
     * 更新食谱
     * @param recipe 食谱信息
     * @param ingredients 食材列表
     * @return 更新后的食谱
     */
    Recipe updateRecipe(Recipe recipe, List<RecipeIngredient> ingredients);

    /**
     * 删除食谱
     * @param id 食谱ID
     * @return 是否删除成功
     */
    boolean deleteRecipe(Long id);

    /**
     * 分析食谱营养成分
     * @param recipeId 食谱ID
     * @return 营养成分分析
     */
    Map<String, Object> analyzeRecipeNutrition(Long recipeId);

    /**
     * 获取推荐食谱
     * @param userId 用户ID
     * @param mealType 餐型
     * @param limit 限制数量
     * @return 推荐食谱列表
     */
    List<Recipe> getRecommendedRecipes(Long userId, String mealType, int limit);

    /**
     * 获取推荐食谱（按餐型分类）
     * @param userId 用户ID
     * @param breakfastCount 早餐推荐数量
     * @param lunchCount 午餐推荐数量
     * @param dinnerCount 晚餐推荐数量
     * @return 推荐食谱映射
     */
    Map<String, List<?>> getRecommendedRecipes(Long userId, Integer breakfastCount, Integer lunchCount, Integer dinnerCount);

    /**
     * 获取食材替代建议
     * @param ingredientData 食材数据
     * @return 替代建议列表
     */
    Map<String, Object> getIngredientSubstitutes(Map<String, Object> ingredientData);

    /**
     * 根据目标获取推荐食谱
     * @param userId 用户ID
     * @param goalData 目标数据
     * @return 推荐食谱列表
     */
    List<?> getRecipesByGoal(Long userId, Map<String, Object> goalData);

    /**
     * 获取今日推荐食谱
     * @param userId 用户ID
     * @return 今日推荐食谱
     */
    Map<String, Object> getTodayRecommendedRecipes(Long userId);
}
