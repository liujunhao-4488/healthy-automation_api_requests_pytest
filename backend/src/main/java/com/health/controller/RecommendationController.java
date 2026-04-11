package com.health.controller;

import com.health.service.RecipeService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import javax.validation.Valid;
import java.security.Principal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/recommend")
public class RecommendationController {

    @Autowired
    private RecipeService recipeService;

    // 获取食谱推荐
    @GetMapping("/recipes")
    public ResponseEntity<?> getRecommendedRecipes(Principal principal,
                                                  @RequestParam(required = false, defaultValue = "3") Integer breakfastCount,
                                                  @RequestParam(required = false, defaultValue = "3") Integer lunchCount,
                                                  @RequestParam(required = false, defaultValue = "3") Integer dinnerCount) {
        try {
            Long userId = Long.parseLong(principal.getName());
            Map<String, List<?>> recommendedRecipes = recipeService.getRecommendedRecipes(userId, breakfastCount, lunchCount, dinnerCount);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取食谱推荐成功");
            response.put("data", recommendedRecipes);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取食谱推荐失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取食材替代建议
    @PostMapping("/ingredient/substitute")
    public ResponseEntity<?> getIngredientSubstitutes(Principal principal, @Valid @RequestBody Map<String, Object> ingredientData) {
        try {
            if (principal != null) {
                ingredientData.put("userId", Long.parseLong(principal.getName()));
            }
            Map<String, Object> substitutes = recipeService.getIngredientSubstitutes(ingredientData);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取食材替代建议成功");
            response.put("data", substitutes);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取食材替代建议失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 根据目标获取推荐食谱
    @PostMapping("/recipes/by-goal")
    public ResponseEntity<?> getRecipesByGoal(Principal principal,
                                            @Valid @RequestBody Map<String, Object> goalData) {
        try {
            Long userId = Long.parseLong(principal.getName());
            List<?> recipes = recipeService.getRecipesByGoal(userId, goalData);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "根据目标获取推荐食谱成功");
            response.put("data", recipes);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("根据目标获取推荐食谱失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取今日推荐食谱
    @GetMapping("/recipes/today")
    public ResponseEntity<?> getTodayRecommendedRecipes(Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            Map<String, Object> todayRecipes = recipeService.getTodayRecommendedRecipes(userId);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取今日推荐食谱成功");
            response.put("data", todayRecipes);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取今日推荐食谱失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }
}
