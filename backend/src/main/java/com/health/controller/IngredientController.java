package com.health.controller;

import com.health.entity.Ingredient;
import com.health.entity.User;
import com.health.service.IngredientService;
import com.health.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;
import java.security.Principal;

/**
 * 食材控制器
 */
@Slf4j
@RestController
@RequestMapping("/ingredient")
public class IngredientController {

    @Autowired
    private IngredientService ingredientService;

    @Autowired
    private UserService userService;

    // 获取所有食材
    @GetMapping("/list")
    public ResponseEntity<?> getAllIngredients() {
        try {
            List<Ingredient> ingredients = ingredientService.getAllIngredients();
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取食材列表成功");
            response.put("data", ingredients);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取食材列表失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 根据ID获取食材
    @GetMapping("/detail/{id}")
    public ResponseEntity<?> getIngredientById(@PathVariable Long id) {
        try {
            Ingredient ingredient = ingredientService.getIngredientById(id);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取食材详情成功");
            response.put("data", ingredient);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取食材详情失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 根据分类获取食材
    @GetMapping("/category/{category}")
    public ResponseEntity<?> getIngredientsByCategory(@PathVariable String category) {
        try {
            List<Ingredient> ingredients = ingredientService.getIngredientsByCategory(category);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取分类食材成功");
            response.put("data", ingredients);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取分类食材失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 搜索食材
    @GetMapping("/search")
    public ResponseEntity<?> searchIngredients(@RequestParam String keyword) {
        try {
            List<Ingredient> ingredients = ingredientService.searchIngredients(keyword);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "搜索食材成功");
            response.put("data", ingredients);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("搜索食材失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 保存食材
    @PostMapping("/save")
    public ResponseEntity<?> saveIngredient(@RequestBody Ingredient ingredient, Principal principal) {
        try {
            requireAdmin(principal);
            Ingredient savedIngredient = ingredientService.saveIngredient(ingredient);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "保存食材成功");
            response.put("data", savedIngredient);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("保存食材失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 更新食材
    @PutMapping("/update")
    public ResponseEntity<?> updateIngredient(@RequestBody Ingredient ingredient, Principal principal) {
        try {
            requireAdmin(principal);
            Ingredient updatedIngredient = ingredientService.updateIngredient(ingredient);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "更新食材成功");
            response.put("data", updatedIngredient);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("更新食材失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 删除食材
    @DeleteMapping("/delete/{id}")
    public ResponseEntity<?> deleteIngredient(@PathVariable Long id, Principal principal) {
        try {
            requireAdmin(principal);
            boolean deleted = ingredientService.deleteIngredient(id);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", deleted ? "删除食材成功" : "食材不存在");
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("删除食材失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 计算食材营养成分
    @PostMapping("/nutrition")
    public ResponseEntity<?> calculateNutrition(@RequestBody Map<String, Object> params) {
        try {
            Long ingredientId = Long.parseLong(params.get("ingredientId").toString());
            Double quantity = Double.parseDouble(params.get("quantity").toString());
            String unit = params.get("unit").toString();
            
            Map<String, Double> nutrition = ingredientService.calculateNutrition(ingredientId, quantity, unit);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "计算营养成分成功");
            response.put("data", nutrition);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("计算营养成分失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 食材替代查询
    /*
     * 2026-11-02 重写：原先这里返回硬编码的「西兰花 / 花椰菜」两条假数据，
     * ingredientName 取出来后一次都没用，而且「花椰菜」在食材库里根本不存在。
     * 现在改为按营养构成相似度真实计算，见 IngredientServiceImpl.getSubstitutes。
     *
     * 请求：{ "ingredientName": "鸡胸肉", "prompt": "低脂、低 GI", "limit": 4 }
     * 全部字段除 ingredientName 外可选。
     */
    @PostMapping("/substitute")
    public ResponseEntity<?> getIngredientSubstitute(@RequestBody Map<String, Object> params) {
        try {
            Object nameObj = params.get("ingredientName");
            if (nameObj == null || nameObj.toString().trim().isEmpty()) {
                throw new RuntimeException("请先选择需要替代的食材");
            }
            String ingredientName = nameObj.toString();

            String prompt = null;
            if (params.get("prompt") != null) {
                prompt = params.get("prompt").toString();
            }

            Integer limit = null;
            if (params.get("limit") != null) {
                try {
                    limit = Integer.parseInt(params.get("limit").toString());
                } catch (NumberFormatException ignored) {
                    // 传了非法 limit 就按默认条数处理，不因此报错
                }
            }

            List<Map<String, Object>> substitutes =
                    ingredientService.getSubstitutes(ingredientName, prompt, limit);

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

    private void requireAdmin(Principal principal) {
        if (principal == null) {
            throw new RuntimeException("未登录或登录已过期");
        }
        User user = userService.findById(Long.parseLong(principal.getName()));
        if (!userService.isAdmin(user)) {
            throw new RuntimeException("仅管理员可执行该操作");
        }
    }
}
