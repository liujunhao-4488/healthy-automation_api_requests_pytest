package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;
import com.health.entity.Ingredient;
import com.health.mapper.RecipeMapper;
import com.health.mapper.RecipeIngredientMapper;
import com.health.mapper.IngredientMapper;
import com.health.service.RecipeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.RestClientException;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;

/**
 * 食谱服务实现类
 */
@Service
public class RecipeServiceImpl implements RecipeService {

    @Autowired
    private RecipeMapper recipeMapper;

    @Autowired
    private RecipeIngredientMapper recipeIngredientMapper;

    @Autowired
    private IngredientMapper ingredientMapper;

    @Autowired
    private RestTemplate restTemplate;

    // Python算法服务的基础URL
    private static final String PYTHON_SERVICE_URL = "http://localhost:5000";

    @Override
    public List<Recipe> getAllRecipes() {
        return recipeMapper.selectList(null);
    }

    @Override
    public Recipe getRecipeById(Long id) {
        return recipeMapper.selectById(id);
    }

    @Override
    public List<RecipeIngredient> getRecipeIngredients(Long recipeId) {
        return recipeIngredientMapper.selectByRecipeId(recipeId);
    }

    @Override
    public List<Recipe> getCustomRecipes(Long userId) {
        return recipeMapper.selectCustomByUserId(userId);
    }

    @Override
    public List<Recipe> searchRecipes(String keyword) {
        QueryWrapper<Recipe> wrapper = new QueryWrapper<>();
        wrapper.like("name", keyword).or().like("description", keyword);
        return recipeMapper.selectList(wrapper);
    }

    @Transactional
    @Override
    public Recipe saveRecipe(Recipe recipe, List<RecipeIngredient> ingredients) {
        // 保存食谱
        recipeMapper.insert(recipe);
        
        // 保存食谱食材关联
        for (RecipeIngredient ingredient : ingredients) {
            ingredient.setRecipeId(recipe.getId());
            recipeIngredientMapper.insert(ingredient);
        }
        
        // 计算营养成分
        calculateRecipeNutrition(recipe);
        
        return recipe;
    }

    @Transactional
    @Override
    public Recipe updateRecipe(Recipe recipe, List<RecipeIngredient> ingredients) {
        // 更新食谱
        recipeMapper.updateById(recipe);
        
        // 删除旧的食材关联
        QueryWrapper<RecipeIngredient> wrapper = new QueryWrapper<>();
        wrapper.eq("recipe_id", recipe.getId());
        recipeIngredientMapper.delete(wrapper);
        
        // 保存新的食材关联
        for (RecipeIngredient ingredient : ingredients) {
            ingredient.setRecipeId(recipe.getId());
            recipeIngredientMapper.insert(ingredient);
        }
        
        // 重新计算营养成分
        calculateRecipeNutrition(recipe);
        
        return recipe;
    }

    @Transactional
    @Override
    public boolean deleteRecipe(Long id) {
        // 删除食材关联
        QueryWrapper<RecipeIngredient> wrapper = new QueryWrapper<>();
        wrapper.eq("recipe_id", id);
        recipeIngredientMapper.delete(wrapper);
        
        // 删除食谱
        return recipeMapper.deleteById(id) > 0;
    }

    @Override
    public Map<String, Double> analyzeRecipeNutrition(Long recipeId) {
        Recipe recipe = recipeMapper.selectById(recipeId);
        Map<String, Double> nutrition = new HashMap<>();
        
        if (recipe != null) {
            nutrition.put("totalCalories", recipe.getTotalCalories());
            nutrition.put("protein", recipe.getProtein());
            nutrition.put("carbs", recipe.getCarbs());
            nutrition.put("fat", recipe.getFat());
        }
        
        return nutrition;
    }

    @Override
    public Map<String, List<?>> getRecommendedRecipes(Long userId, Integer breakfastCount, Integer lunchCount, Integer dinnerCount) {
        Map<String, List<?>> recommendedRecipes = new HashMap<>();
        
        try {
            // 调用Python推荐服务
            Map<String, Object> requestData = new HashMap<>();
            requestData.put("userId", userId);
            requestData.put("breakfastCount", breakfastCount);
            requestData.put("lunchCount", lunchCount);
            requestData.put("dinnerCount", dinnerCount);
            
            String url = PYTHON_SERVICE_URL + "/api/recommend/recipes";
            Map<String, Object> response = restTemplate.postForObject(url, requestData, Map.class);
            
            if (response != null && response.containsKey("data")) {
                recommendedRecipes = (Map<String, List<?>>) response.get("data");
            }
        } catch (RestClientException e) {
            // 如果Python服务不可用，使用本地默认推荐
            System.out.println("Python推荐服务不可用，使用本地默认推荐: " + e.getMessage());
            recommendedRecipes.put("breakfast", getLocalRecommendedRecipes("breakfast", breakfastCount));
            recommendedRecipes.put("lunch", getLocalRecommendedRecipes("lunch", lunchCount));
            recommendedRecipes.put("dinner", getLocalRecommendedRecipes("dinner", dinnerCount));
        }
        
        return recommendedRecipes;
    }

    @Override
    public List<Recipe> getRecommendedRecipes(Long userId, String mealType, int limit) {
        try {
            // 调用Python推荐服务
            Map<String, Object> requestData = new HashMap<>();
            requestData.put("userId", userId);
            requestData.put("mealType", mealType);
            requestData.put("limit", limit);
            
            String url = PYTHON_SERVICE_URL + "/api/recommend/recipe";
            Map<String, Object> response = restTemplate.postForObject(url, requestData, Map.class);
            
            if (response != null && response.containsKey("data")) {
                return (List<Recipe>) response.get("data");
            }
        } catch (RestClientException e) {
            // 如果Python服务不可用，使用本地默认推荐
            System.out.println("Python推荐服务不可用，使用本地默认推荐: " + e.getMessage());
        }
        
        // 本地默认推荐
        return getLocalRecommendedRecipes(mealType, limit);
    }

    @Override
    public List<Map<String, Object>> getIngredientSubstitutes(Map<String, Object> ingredientData) {
        List<Map<String, Object>> substitutes = new ArrayList<>();
        
        try {
            // 调用Python食材替代服务
            String url = PYTHON_SERVICE_URL + "/api/ingredient/substitute";
            Map<String, Object> response = restTemplate.postForObject(url, ingredientData, Map.class);
            
            if (response != null && response.containsKey("data")) {
                substitutes = (List<Map<String, Object>>) response.get("data");
            }
        } catch (RestClientException e) {
            // 如果Python服务不可用，返回空列表
            System.out.println("Python食材替代服务不可用: " + e.getMessage());
        }
        
        return substitutes;
    }

    @Override
    public List<?> getRecipesByGoal(Long userId, Map<String, Object> goalData) {
        List<?> recipes = new ArrayList<>();
        
        try {
            // 调用Python目标推荐服务
            Map<String, Object> requestData = new HashMap<>();
            requestData.put("userId", userId);
            requestData.putAll(goalData);
            
            String url = PYTHON_SERVICE_URL + "/api/recommend/by-goal";
            Map<String, Object> response = restTemplate.postForObject(url, requestData, Map.class);
            
            if (response != null && response.containsKey("data")) {
                recipes = (List<?>) response.get("data");
            }
        } catch (RestClientException e) {
            // 如果Python服务不可用，返回空列表
            System.out.println("Python目标推荐服务不可用: " + e.getMessage());
        }
        
        return recipes;
    }

    @Override
    public Map<String, Object> getTodayRecommendedRecipes(Long userId) {
        Map<String, Object> todayRecipes = new HashMap<>();
        
        try {
            // 调用Python今日推荐服务
            Map<String, Object> requestData = new HashMap<>();
            requestData.put("userId", userId);
            
            String url = PYTHON_SERVICE_URL + "/api/recommend/today";
            Map<String, Object> response = restTemplate.postForObject(url, requestData, Map.class);
            
            if (response != null && response.containsKey("data")) {
                todayRecipes = (Map<String, Object>) response.get("data");
            }
        } catch (RestClientException e) {
            // 如果Python服务不可用，使用本地默认推荐
            System.out.println("Python今日推荐服务不可用，使用本地默认推荐: " + e.getMessage());
            todayRecipes.put("breakfast", getLocalRecommendedRecipes("breakfast", 1));
            todayRecipes.put("lunch", getLocalRecommendedRecipes("lunch", 1));
            todayRecipes.put("dinner", getLocalRecommendedRecipes("dinner", 1));
        }
        
        return todayRecipes;
    }

    /**
     * 计算食谱的营养成分
     */
    private void calculateRecipeNutrition(Recipe recipe) {
        List<RecipeIngredient> ingredients = recipeIngredientMapper.selectByRecipeId(recipe.getId());
        double totalCalories = 0;
        double totalProtein = 0;
        double totalCarbs = 0;
        double totalFat = 0;
        
        for (RecipeIngredient recipeIngredient : ingredients) {
            Ingredient ingredient = ingredientMapper.selectById(recipeIngredient.getIngredientId());
            if (ingredient != null) {
                double quantity = recipeIngredient.getQuantity();
                double ratio = quantity / 100.0;
                
                totalCalories += ingredient.getCaloriesPer100g() * ratio;
                totalProtein += ingredient.getProteinPer100g() * ratio;
                totalCarbs += ingredient.getCarbsPer100g() * ratio;
                totalFat += ingredient.getFatPer100g() * ratio;
            }
        }
        
        recipe.setTotalCalories(totalCalories);
        recipe.setProtein(totalProtein);
        recipe.setCarbs(totalCarbs);
        recipe.setFat(totalFat);
        
        recipeMapper.updateById(recipe);
    }

    /**
     * 本地默认推荐食谱
     */
    private List<Recipe> getLocalRecommendedRecipes(String mealType, int limit) {
        List<Recipe> allRecipes = recipeMapper.selectList(null);
        
        if (allRecipes.isEmpty()) {
            return new ArrayList<>();
        }
        
        return allRecipes.size() > limit ? allRecipes.subList(0, limit) : allRecipes;
    }
}
