package com.health.controller;

import com.health.dto.DietGoalDTO;
import com.health.dto.HealthInfoDTO;
import com.health.entity.DietGoal;
import com.health.entity.HealthInfo;
import com.health.entity.HealthInfoHistory;
import com.health.service.DietGoalService;
import com.health.service.HealthInfoService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;
import java.security.Principal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/health")
public class HealthInfoController {

    @Autowired
    private HealthInfoService healthInfoService;

    @Autowired
    private DietGoalService dietGoalService;

    @PostMapping("/info")
    public ResponseEntity<?> saveOrUpdateHealthInfo(@Valid @RequestBody HealthInfoDTO healthInfoDTO, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            HealthInfo healthInfo = healthInfoService.saveOrUpdateHealthInfo(userId, healthInfoDTO);
            DietGoal dietGoal = dietGoalService.getDietGoalByUserId(userId);

            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "健康信息保存成功");
            response.put("data", healthInfo);
            response.put("analysis", healthInfoService.buildHealthAnalysis(userId, healthInfo, dietGoal));
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("保存健康信息失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/info")
    public ResponseEntity<?> getHealthInfo(Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            HealthInfo healthInfo = healthInfoService.getHealthInfoByUserId(userId);
            DietGoal dietGoal = dietGoalService.getDietGoalByUserId(userId);

            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取健康信息成功");
            response.put("data", healthInfo);
            response.put("analysis", healthInfoService.buildHealthAnalysis(userId, healthInfo, dietGoal));
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取健康信息失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/history")
    public ResponseEntity<?> getHealthHistory(Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            List<HealthInfoHistory> historyList = healthInfoService.getHealthHistoryByUserId(userId);

            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取健康历史成功");
            response.put("data", historyList);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取健康历史失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/goal")
    public ResponseEntity<?> saveOrUpdateDietGoal(@Valid @RequestBody DietGoalDTO dietGoalDTO, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            DietGoal dietGoal = dietGoalService.saveOrUpdateDietGoal(userId, dietGoalDTO);

            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "饮食目标设置成功");
            response.put("data", dietGoal);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("设置饮食目标失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/goal")
    public ResponseEntity<?> getDietGoal(Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            DietGoal dietGoal = dietGoalService.getDietGoalByUserId(userId);

            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取饮食目标成功");
            response.put("data", dietGoal);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取饮食目标失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
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
