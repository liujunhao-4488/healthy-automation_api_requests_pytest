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

    /**
     * 食材替代推荐：按营养构成相似度，找出可以替换目标食材的候选。
     *
     * 2026-11-02 新增。此前 Controller 里是硬编码的「西兰花 / 花椰菜」两条假数据，
     * 无论传什么食材都返回同样结果，ingredientName 参数完全没用上。
     *
     * @param ingredientName 目标食材名（前端可能传「白米饭」，而库里的名字是「米饭」，内部做宽松匹配）
     * @param prompt         可选的目标描述，如「低脂、低 GI」，命中时会略微加权
     * @param limit          返回条数上限
     * @return 替代方案列表，每项含 name / similarity / reason 及营养字段
     */
    List<java.util.Map<String, Object>> getSubstitutes(String ingredientName, String prompt, Integer limit);
}
