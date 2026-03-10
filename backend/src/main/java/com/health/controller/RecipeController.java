package com.health.controller;

import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;
import com.health.service.RecipeService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.List;
import java.util.HashMap;
import java.util.ArrayList;
import java.security.Principal;

/**
 * 食谱控制器
 */
@Slf4j
@RestController
@RequestMapping("/recipe")
public class RecipeController {

    @Autowired
    private RecipeService recipeService;

    // 获取所有食谱
    @GetMapping("/list")
    public ResponseEntity<?> getAllRecipes() {
        try {
            List<Recipe> recipes = recipeService.getAllRecipes();
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取食谱列表成功");
            response.put("data", recipes);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取食谱列表失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 根据ID获取食谱
    @GetMapping("/detail/{id}")
    public ResponseEntity<?> getRecipeById(@PathVariable Long id) {
        try {
            Recipe recipe = recipeService.getRecipeById(id);
            List<RecipeIngredient> ingredients = recipeService.getRecipeIngredients(id);
            Map<String, Object> recipeData = new HashMap<>();
            recipeData.put("recipe", recipe);
            recipeData.put("ingredients", ingredients);
            
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取食谱详情成功");
            response.put("data", recipeData);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取食谱详情失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取用户自定义食谱
    @GetMapping("/custom")
    public ResponseEntity<?> getCustomRecipes(Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            List<Recipe> recipes = recipeService.getCustomRecipes(userId);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取自定义食谱成功");
            response.put("data", recipes);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取自定义食谱失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 搜索食谱
    @GetMapping("/search")
    public ResponseEntity<?> searchRecipes(@RequestParam String keyword) {
        try {
            List<Recipe> recipes = recipeService.searchRecipes(keyword);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "搜索食谱成功");
            response.put("data", recipes);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("搜索食谱失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 保存食谱
    @PostMapping("/save")
    public ResponseEntity<?> saveRecipe(@RequestBody Map<String, Object> params, Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            Recipe recipe = new Recipe();
            recipe.setName(params.get("name").toString());
            recipe.setDescription(params.get("description").toString());
            recipe.setCookingTime(Integer.parseInt(params.get("cookingTime").toString()));
            recipe.setDifficulty(params.get("difficulty").toString());
            recipe.setInstructions(params.get("instructions").toString());
            recipe.setImageUrl(params.get("imageUrl").toString());
            recipe.setCreatorId(userId);
            recipe.setIsCustom(1);
            
            List<Map<String, Object>> ingredientMaps = (List<Map<String, Object>>) params.get("ingredients");
            List<RecipeIngredient> ingredients = new ArrayList<>();
            for (Map<String, Object> ingredientMap : ingredientMaps) {
                RecipeIngredient ingredient = new RecipeIngredient();
                ingredient.setIngredientId(Long.parseLong(ingredientMap.get("ingredientId").toString()));
                ingredient.setQuantity(Double.parseDouble(ingredientMap.get("quantity").toString()));
                ingredient.setUnit(ingredientMap.get("unit").toString());
                ingredients.add(ingredient);
            }
            
            Recipe savedRecipe = recipeService.saveRecipe(recipe, ingredients);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "保存食谱成功");
            response.put("data", savedRecipe);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("保存食谱失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 更新食谱
    @PutMapping("/update")
    public ResponseEntity<?> updateRecipe(@RequestBody Map<String, Object> params) {
        try {
            Recipe recipe = new Recipe();
            recipe.setId(Long.parseLong(params.get("id").toString()));
            recipe.setName(params.get("name").toString());
            recipe.setDescription(params.get("description").toString());
            recipe.setCookingTime(Integer.parseInt(params.get("cookingTime").toString()));
            recipe.setDifficulty(params.get("difficulty").toString());
            recipe.setInstructions(params.get("instructions").toString());
            recipe.setImageUrl(params.get("imageUrl").toString());
            
            List<Map<String, Object>> ingredientMaps = (List<Map<String, Object>>) params.get("ingredients");
            List<RecipeIngredient> ingredients = new ArrayList<>();
            for (Map<String, Object> ingredientMap : ingredientMaps) {
                RecipeIngredient ingredient = new RecipeIngredient();
                ingredient.setIngredientId(Long.parseLong(ingredientMap.get("ingredientId").toString()));
                ingredient.setQuantity(Double.parseDouble(ingredientMap.get("quantity").toString()));
                ingredient.setUnit(ingredientMap.get("unit").toString());
                ingredients.add(ingredient);
            }
            
            Recipe updatedRecipe = recipeService.updateRecipe(recipe, ingredients);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "更新食谱成功");
            response.put("data", updatedRecipe);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("更新食谱失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 删除食谱
    @DeleteMapping("/delete/{id}")
    public ResponseEntity<?> deleteRecipe(@PathVariable Long id) {
        try {
            boolean deleted = recipeService.deleteRecipe(id);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", deleted ? "删除食谱成功" : "食谱不存在");
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("删除食谱失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 分析食谱营养成分
    @GetMapping("/nutrition/{id}")
    public ResponseEntity<?> analyzeRecipeNutrition(@PathVariable Long id) {
        try {
            Map<String, Double> nutrition = recipeService.analyzeRecipeNutrition(id);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "分析食谱营养成分成功");
            response.put("data", nutrition);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("分析食谱营养成分失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取推荐食谱
    @GetMapping("/recommend")
    public ResponseEntity<?> getRecommendedRecipes(@RequestParam String mealType, @RequestParam(defaultValue = "5") int limit, Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            List<Recipe> recipes = recipeService.getRecommendedRecipes(userId, mealType, limit);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取推荐食谱成功");
            response.put("data", recipes);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取推荐食谱失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }
}
