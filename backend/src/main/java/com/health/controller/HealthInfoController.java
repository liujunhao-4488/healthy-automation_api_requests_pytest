package com.health.controller;

import com.health.dto.HealthInfoDTO;
import com.health.dto.DietGoalDTO;
import com.health.entity.HealthInfo;
import com.health.entity.DietGoal;
import com.health.service.HealthInfoService;
import com.health.service.DietGoalService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import javax.validation.Valid;
import java.security.Principal;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/health")
public class HealthInfoController {

    @Autowired
    private HealthInfoService healthInfoService;

    @Autowired
    private DietGoalService dietGoalService;

    // 保存或更新健康信息
    @PostMapping("/info")
    public ResponseEntity<?> saveOrUpdateHealthInfo(@Valid @RequestBody HealthInfoDTO healthInfoDTO, Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            HealthInfo healthInfo = healthInfoService.saveOrUpdateHealthInfo(userId, healthInfoDTO);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "健康信息保存成功");
            response.put("data", healthInfo);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("保存健康信息失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取用户健康信息
    @GetMapping("/info")
    public ResponseEntity<?> getHealthInfo(Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            HealthInfo healthInfo = healthInfoService.getHealthInfoByUserId(userId);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取健康信息成功");
            response.put("data", healthInfo);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取健康信息失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 保存或更新饮食目标
    @PostMapping("/goal")
    public ResponseEntity<?> saveOrUpdateDietGoal(@Valid @RequestBody DietGoalDTO dietGoalDTO, Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            DietGoal dietGoal = dietGoalService.saveOrUpdateDietGoal(userId, dietGoalDTO);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "饮食目标设置成功");
            response.put("data", dietGoal);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("设置饮食目标失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取用户饮食目标
    @GetMapping("/goal")
    public ResponseEntity<?> getDietGoal(Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            DietGoal dietGoal = dietGoalService.getDietGoalByUserId(userId);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取饮食目标成功");
            response.put("data", dietGoal);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取饮食目标失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

}
