package com.health.controller;

import com.health.entity.HealthArticle;
import com.health.entity.UserReadRecord;
import com.health.service.HealthArticleService;
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
@RequestMapping("/article")
public class HealthArticleController {

    @Autowired
    private HealthArticleService healthArticleService;

    // 获取健康文章列表
    @GetMapping("/list")
    public ResponseEntity<?> getHealthArticleList(@RequestParam(required = false) String category,
                                                 @RequestParam(required = false, defaultValue = "1") Integer page,
                                                 @RequestParam(required = false, defaultValue = "10") Integer pageSize) {
        try {
            List<HealthArticle> articles = healthArticleService.getHealthArticles(category, page, pageSize);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取健康文章成功");
            response.put("data", articles);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取健康文章失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取健康文章详情
    @GetMapping("/detail/{articleId}")
    public ResponseEntity<?> getHealthArticleDetail(@PathVariable Long articleId, Principal principal) {
        try {
            Long userId = null;
            if (principal != null) {
                userId = Long.parseLong(principal.getName());
            }
            HealthArticle article = healthArticleService.getHealthArticleById(articleId, userId);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取健康文章详情成功");
            response.put("data", article);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取健康文章详情失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取个性化健康文章推荐
    @GetMapping("/recommend")
    public ResponseEntity<?> getRecommendedArticles(Principal principal,
                                                  @RequestParam(required = false, defaultValue = "5") Integer limit) {
        try {
            Long userId = Long.parseLong(principal.getName());
            List<HealthArticle> articles = healthArticleService.getRecommendedArticles(userId, limit);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取个性化推荐文章成功");
            response.put("data", articles);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取个性化推荐文章失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 记录文章阅读
    @PostMapping("/read/{articleId}")
    public ResponseEntity<?> recordArticleRead(@PathVariable Long articleId, Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            UserReadRecord readRecord = healthArticleService.recordArticleRead(userId, articleId);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "记录文章阅读成功");
            response.put("data", readRecord);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("记录文章阅读失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 搜索健康文章
    @GetMapping("/search")
    public ResponseEntity<?> searchHealthArticles(@RequestParam String keyword,
                                                 @RequestParam(required = false, defaultValue = "1") Integer page,
                                                 @RequestParam(required = false, defaultValue = "10") Integer pageSize) {
        try {
            List<HealthArticle> articles = healthArticleService.searchHealthArticles(keyword, page, pageSize);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "搜索健康文章成功");
            response.put("data", articles);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("搜索健康文章失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }
}
