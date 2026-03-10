package com.health.service;

import com.health.entity.Ingredient;
import java.util.List;

/**
 * 食材服务接口
 */
public interface IngredientService {

    /**
     * 获取所有食材
     * @return 食材列表
     */
    List<Ingredient> getAllIngredients();

    /**
     * 根据ID获取食材
     * @param id 食材ID
     * @return 食材信息
     */
    Ingredient getIngredientById(Long id);

    /**
     * 根据分类获取食材
     * @param category 食材分类
     * @return 食材列表
     */
    List<Ingredient> getIngredientsByCategory(String category);

    /**
     * 搜索食材
     * @param keyword 搜索关键词
     * @return 食材列表
     */
    List<Ingredient> searchIngredients(String keyword);

    /**
     * 保存食材
     * @param ingredient 食材信息
     * @return 保存后的食材
     */
    Ingredient saveIngredient(Ingredient ingredient);

    /**
     * 更新食材
     * @param ingredient 食材信息
     * @return 更新后的食材
     */
    Ingredient updateIngredient(Ingredient ingredient);

    /**
     * 删除食材
     * @param id 食材ID
     * @return 是否删除成功
     */
    boolean deleteIngredient(Long id);

    /**
     * 计算食材的营养成分
     * @param ingredientId 食材ID
     * @param quantity 数量
     * @param unit 单位
     * @return 营养成分映射
     */
    java.util.Map<String, Double> calculateNutrition(Long ingredientId, Double quantity, String unit);
}
