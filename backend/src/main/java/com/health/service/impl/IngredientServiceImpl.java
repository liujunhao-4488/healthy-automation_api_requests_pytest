package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.entity.Ingredient;
import com.health.mapper.IngredientMapper;
import com.health.service.IngredientService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

/**
 * 食材服务实现类
 */
@Service
public class IngredientServiceImpl implements IngredientService {

    @Autowired
    private IngredientMapper ingredientMapper;

    @Override
    public List<Ingredient> getAllIngredients() {
        return ingredientMapper.selectList(null);
    }

    @Override
    public Ingredient getIngredientById(Long id) {
        return ingredientMapper.selectById(id);
    }

    @Override
    public List<Ingredient> getIngredientsByCategory(String category) {
        return ingredientMapper.selectByCategory(category);
    }

    @Override
    public List<Ingredient> searchIngredients(String keyword) {
        return ingredientMapper.selectByNameLike("%" + keyword + "%");
    }

    @Override
    public Ingredient saveIngredient(Ingredient ingredient) {
        ingredientMapper.insert(ingredient);
        return ingredient;
    }

    @Override
    public Ingredient updateIngredient(Ingredient ingredient) {
        ingredientMapper.updateById(ingredient);
        return ingredient;
    }

    @Override
    public boolean deleteIngredient(Long id) {
        return ingredientMapper.deleteById(id) > 0;
    }

    @Override
    public Map<String, Double> calculateNutrition(Long ingredientId, Double quantity, String unit) {
        Ingredient ingredient = ingredientMapper.selectById(ingredientId);
        Map<String, Double> nutrition = new HashMap<>();
        
        if (ingredient != null) {
            // 假设单位是克，转换为100克的比例
            double ratio = quantity / 100.0;
            
            nutrition.put("calories", ingredient.getCaloriesPer100g() * ratio);
            nutrition.put("protein", ingredient.getProteinPer100g() * ratio);
            nutrition.put("carbs", ingredient.getCarbsPer100g() * ratio);
            nutrition.put("fat", ingredient.getFatPer100g() * ratio);
            
            if (ingredient.getFiberPer100g() != null) {
                nutrition.put("fiber", ingredient.getFiberPer100g() * ratio);
            }
            if (ingredient.getSugarPer100g() != null) {
                nutrition.put("sugar", ingredient.getSugarPer100g() * ratio);
            }
            if (ingredient.getSodiumPer100g() != null) {
                nutrition.put("sodium", ingredient.getSodiumPer100g() * ratio);
            }
            if (ingredient.getGiValue() != null) {
                nutrition.put("gi", ingredient.getGiValue().doubleValue());
            }
        }
        
        return nutrition;
    }
}
