package com.health.controller;

import com.health.entity.DietRecord;
import com.health.entity.DietRecordDetail;
import com.health.service.DietRecordService;
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
@RequestMapping("/record")
public class DietRecordController {

    @Autowired
    private DietRecordService dietRecordService;

    // 提交饮食记录
    @PostMapping("/submit")
    public ResponseEntity<?> submitDietRecord(@Valid @RequestBody Map<String, Object> recordData, Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            DietRecord dietRecord = dietRecordService.saveDietRecord(userId, recordData);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "饮食记录提交成功");
            response.put("data", dietRecord);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("提交饮食记录失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取用户饮食记录列表
    @GetMapping("/list")
    public ResponseEntity<?> getDietRecordList(Principal principal,
                                              @RequestParam(required = false) String startDate,
                                              @RequestParam(required = false) String endDate,
                                              @RequestParam(required = false, defaultValue = "1") Integer page,
                                              @RequestParam(required = false, defaultValue = "10") Integer pageSize) {
        try {
            Long userId = Long.parseLong(principal.getName());
            List<DietRecord> records = dietRecordService.getDietRecordsByUserId(userId, startDate, endDate, page, pageSize);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取饮食记录成功");
            response.put("data", records);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取饮食记录失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取饮食记录详情
    @GetMapping("/detail/{recordId}")
    public ResponseEntity<?> getDietRecordDetail(@PathVariable Long recordId, Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            List<DietRecordDetail> details = dietRecordService.getDietRecordDetails(recordId, userId);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取饮食记录详情成功");
            response.put("data", details);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取饮食记录详情失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取饮食摄入趋势分析
    @GetMapping("/analysis/trend")
    public ResponseEntity<?> getDietTrendAnalysis(Principal principal,
                                                 @RequestParam String startDate,
                                                 @RequestParam String endDate) {
        try {
            Long userId = Long.parseLong(principal.getName());
            Map<String, Object> analysis = dietRecordService.getDietTrendAnalysis(userId, startDate, endDate);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取饮食趋势分析成功");
            response.put("data", analysis);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取饮食趋势分析失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 删除饮食记录
    @DeleteMapping("/{recordId}")
    public ResponseEntity<?> deleteDietRecord(@PathVariable Long recordId, Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            dietRecordService.deleteDietRecord(recordId, userId);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "删除饮食记录成功");
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("删除饮食记录失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }

    // 获取饮食建议和误区提醒
    @GetMapping("/suggestions")
    public ResponseEntity<?> getDietSuggestions(Principal principal) {
        try {
            Long userId = Long.parseLong(principal.getName());
            List<String> suggestions = dietRecordService.getDietSuggestions(userId);
            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取饮食建议成功");
            response.put("data", suggestions);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取饮食建议失败: {}", e.getMessage());
            Map<String, Object> response = new HashMap<>();
            response.put("code", 400);
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        }
    }
}
