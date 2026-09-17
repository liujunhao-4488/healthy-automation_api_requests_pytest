package com.health.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.entity.Ingredient;
import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;
import com.health.entity.User;
import com.health.entity.UserRecipeCollect;
import com.health.mapper.IngredientMapper;
import com.health.mapper.RecipeMapper;
import com.health.mapper.UserRecipeCollectMapper;
import com.health.service.RecipeService;
import com.health.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/recipe")
public class RecipeController {

    @Autowired
    private RecipeService recipeService;

    @Autowired
    private UserService userService;

    @Autowired
    private UserRecipeCollectMapper userRecipeCollectMapper;

    @Autowired
    private RecipeMapper recipeMapper;

    @Autowired
    private IngredientMapper ingredientMapper;

    @GetMapping("/list")
    public ResponseEntity<?> getAllRecipes() {
        try {
            return successResponse("获取食谱列表成功", recipeService.getAllRecipes());
        } catch (Exception e) {
            log.error("获取食谱列表失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/detail/{id}")
    public ResponseEntity<?> getRecipeById(@PathVariable Long id) {
        try {
            Map<String, Object> recipeData = new HashMap<>();
            recipeData.put("recipe", recipeService.getRecipeById(id));
            recipeData.put("ingredients", buildIngredientDetails(recipeService.getRecipeIngredients(id)));
            return successResponse("获取食谱详情成功", recipeData);
        } catch (Exception e) {
            log.error("获取食谱详情失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/custom")
    public ResponseEntity<?> getCustomRecipes(Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            return successResponse("获取自定义食谱成功", recipeService.getCustomRecipes(userId));
        } catch (Exception e) {
            log.error("获取自定义食谱失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/search")
    public ResponseEntity<?> searchRecipes(@RequestParam String keyword) {
        try {
            return successResponse("搜索食谱成功", recipeService.searchRecipes(keyword));
        } catch (Exception e) {
            log.error("搜索食谱失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/save")
    public ResponseEntity<?> saveRecipe(@RequestBody Map<String, Object> params, Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());

            Recipe recipe = new Recipe();
            recipe.setName(String.valueOf(params.get("name")));
            recipe.setDescription(String.valueOf(params.get("description")));
            recipe.setCookingTime(Integer.parseInt(params.get("cookingTime").toString()));
            recipe.setDifficulty(String.valueOf(params.get("difficulty")));
            recipe.setInstructions(String.valueOf(params.get("instructions")));
            recipe.setImageUrl(String.valueOf(params.getOrDefault("imageUrl", "")));
            recipe.setCreatorId(userId);
            recipe.setIsCustom(1);

            return successResponse("保存食谱成功", recipeService.saveRecipe(recipe, buildIngredients(params)));
        } catch (Exception e) {
            log.error("保存食谱失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PutMapping("/update")
    public ResponseEntity<?> updateRecipe(@RequestBody Map<String, Object> params, Principal principal) {
        try {
            Long recipeId = Long.parseLong(params.get("id").toString());
            requireAdminOrRecipeOwner(principal, recipeId);

            Recipe recipe = new Recipe();
            recipe.setId(recipeId);
            recipe.setName(String.valueOf(params.get("name")));
            recipe.setDescription(String.valueOf(params.get("description")));
            recipe.setCookingTime(Integer.parseInt(params.get("cookingTime").toString()));
            recipe.setDifficulty(String.valueOf(params.get("difficulty")));
            recipe.setInstructions(String.valueOf(params.get("instructions")));
            recipe.setImageUrl(String.valueOf(params.getOrDefault("imageUrl", "")));

            return successResponse("更新食谱成功", recipeService.updateRecipe(recipe, buildIngredients(params)));
        } catch (Exception e) {
            log.error("更新食谱失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @DeleteMapping("/delete/{id}")
    public ResponseEntity<?> deleteRecipe(@PathVariable Long id, Principal principal) {
        try {
            requireAdminOrRecipeOwner(principal, id);
            boolean deleted = recipeService.deleteRecipe(id);
            return successResponse(deleted ? "删除食谱成功" : "食谱不存在", deleted);
        } catch (Exception e) {
            log.error("删除食谱失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/nutrition/{id}")
    public ResponseEntity<?> analyzeRecipeNutrition(@PathVariable Long id) {
        try {
            return successResponse("分析食谱营养成功", recipeService.analyzeRecipeNutrition(id));
        } catch (Exception e) {
            log.error("分析食谱营养失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/recommend")
    public ResponseEntity<?> getRecommendedRecipes(
        @RequestParam String mealType,
        @RequestParam(defaultValue = "5") int limit,
        Principal principal
    ) {
        try {
            Long userId = Long.parseLong(principal.getName());
            return successResponse("获取推荐食谱成功", recipeService.getRecommendedRecipes(userId, mealType, limit));
        } catch (Exception e) {
            log.error("获取推荐食谱失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/collect/{recipeId}")
    public ResponseEntity<?> collectRecipe(@PathVariable Long recipeId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            QueryWrapper<UserRecipeCollect> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId).eq("recipe_id", recipeId);

            if (userRecipeCollectMapper.selectOne(wrapper) == null) {
                UserRecipeCollect collect = new UserRecipeCollect();
                collect.setUserId(userId);
                collect.setRecipeId(recipeId);
                userRecipeCollectMapper.insert(collect);
            }

            updateRecipeCollectCount(recipeId);

            Map<String, Object> data = new HashMap<>();
            data.put("collected", true);
            data.put("collectCount", getRecipeCollectCount(recipeId));
            return successResponse("收藏食谱成功", data);
        } catch (Exception e) {
            log.error("收藏食谱失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @DeleteMapping("/collect/{recipeId}")
    public ResponseEntity<?> cancelCollectRecipe(@PathVariable Long recipeId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            QueryWrapper<UserRecipeCollect> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId).eq("recipe_id", recipeId);
            userRecipeCollectMapper.delete(wrapper);
            updateRecipeCollectCount(recipeId);

            Map<String, Object> data = new HashMap<>();
            data.put("collected", false);
            data.put("collectCount", getRecipeCollectCount(recipeId));
            return successResponse("已取消收藏", data);
        } catch (Exception e) {
            log.error("取消收藏食谱失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/collect/status/{recipeId}")
    public ResponseEntity<?> getRecipeCollectStatus(@PathVariable Long recipeId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            QueryWrapper<UserRecipeCollect> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId).eq("recipe_id", recipeId);

            Map<String, Object> data = new HashMap<>();
            data.put("collected", userRecipeCollectMapper.selectCount(wrapper) > 0);
            data.put("collectCount", getRecipeCollectCount(recipeId));
            return successResponse("获取收藏状态成功", data);
        } catch (Exception e) {
            log.error("获取收藏状态失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/collect/list")
    public ResponseEntity<?> getCollectedRecipes(Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            QueryWrapper<UserRecipeCollect> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId).orderByDesc("create_time");

            List<Recipe> recipes = userRecipeCollectMapper.selectList(wrapper).stream()
                .map(item -> recipeService.getRecipeById(item.getRecipeId()))
                .filter(item -> item != null)
                .collect(Collectors.toList());
            return successResponse("获取收藏食谱成功", recipes);
        } catch (Exception e) {
            log.error("获取收藏食谱失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    private List<RecipeIngredient> buildIngredients(Map<String, Object> params) {
        List<Map<String, Object>> ingredientMaps = (List<Map<String, Object>>) params.get("ingredients");
        List<RecipeIngredient> ingredients = new ArrayList<>();
        for (Map<String, Object> ingredientMap : ingredientMaps) {
            RecipeIngredient ingredient = new RecipeIngredient();
            ingredient.setIngredientId(Long.parseLong(ingredientMap.get("ingredientId").toString()));
            ingredient.setQuantity(Double.parseDouble(ingredientMap.get("quantity").toString()));
            ingredient.setUnit(String.valueOf(ingredientMap.get("unit")));
            ingredients.add(ingredient);
        }
        return ingredients;
    }

    private List<Map<String, Object>> buildIngredientDetails(List<RecipeIngredient> recipeIngredients) {
        List<Map<String, Object>> details = new ArrayList<>();
        if (recipeIngredients == null) {
            return details;
        }

        for (RecipeIngredient recipeIngredient : recipeIngredients) {
            Ingredient ingredient = ingredientMapper.selectById(recipeIngredient.getIngredientId());
            if (ingredient == null) {
                continue;
            }

            double quantity = recipeIngredient.getQuantity() == null ? 0 : recipeIngredient.getQuantity();
            double ratio = quantity / 100.0;

            Map<String, Object> item = new HashMap<>();
            item.put("ingredientId", ingredient.getId());
            item.put("name", ingredient.getName());
            item.put("category", ingredient.getCategory());
            item.put("quantity", recipeIngredient.getQuantity());
            item.put("quantityValue", recipeIngredient.getQuantity());
            item.put("unit", recipeIngredient.getUnit());
            item.put("calories", safeValue(ingredient.getCaloriesPer100g()) * ratio);
            item.put("protein", safeValue(ingredient.getProteinPer100g()) * ratio);
            item.put("carbs", safeValue(ingredient.getCarbsPer100g()) * ratio);
            item.put("fat", safeValue(ingredient.getFatPer100g()) * ratio);
            item.put("fiber", safeValue(ingredient.getFiberPer100g()) * ratio);
            item.put("sugar", safeValue(ingredient.getSugarPer100g()) * ratio);
            item.put("sodium", safeValue(ingredient.getSodiumPer100g()) * ratio);
            item.put("gi", ingredient.getGiValue() == null ? 0 : ingredient.getGiValue());
            details.add(item);
        }

        return details;
    }

    private double safeValue(Double value) {
        return value == null ? 0 : value;
    }

    private int getRecipeCollectCount(Long recipeId) {
        QueryWrapper<UserRecipeCollect> wrapper = new QueryWrapper<>();
        wrapper.eq("recipe_id", recipeId);
        return Math.toIntExact(userRecipeCollectMapper.selectCount(wrapper));
    }

    private void updateRecipeCollectCount(Long recipeId) {
        Recipe recipe = recipeMapper.selectById(recipeId);
        if (recipe != null) {
            recipe.setCollectCount(getRecipeCollectCount(recipeId));
            recipeMapper.updateById(recipe);
        }
    }

    private void requireAdmin(Principal principal) {
        if (principal == null) {
            throw new RuntimeException("未登录或登录已过期");
        }
        User user = userService.findById(Long.parseLong(principal.getName()));
        if (!userService.isAdmin(user)) {
            throw new RuntimeException("仅管理员可执行该操作");
        }
    }

    private void requireAdminOrRecipeOwner(Principal principal, Long recipeId) {
        if (principal == null) {
            throw new RuntimeException("未登录或登录已过期");
        }

        Long userId = Long.parseLong(principal.getName());
        User user = userService.findById(userId);
        if (user != null && userService.isAdmin(user)) {
            return;
        }

        Recipe recipe = recipeMapper.selectById(recipeId);
        if (recipe == null) {
            throw new RuntimeException("食谱不存在");
        }

        if (recipe.getCreatorId() == null || !recipe.getCreatorId().equals(userId)) {
            throw new RuntimeException("仅管理员或食谱创建者可执行该操作");
        }
    }

    private ResponseEntity<?> successResponse(String message, Object data) {
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", message);
        response.put("data", data);
        return ResponseEntity.ok(response);
    }

    private ResponseEntity<Map<String, Object>> unauthorizedResponse() {
        Map<String, Object> response = new HashMap<>();
        response.put("code", 401);
        response.put("message", "未登录或登录已过期");
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
    }

    private ResponseEntity<Map<String, Object>> badRequestResponse(String message) {
        Map<String, Object> response = new HashMap<>();
        response.put("code", 400);
        response.put("message", message);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
    }
}
