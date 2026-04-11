package com.health.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.entity.DietGoal;
import com.health.entity.HealthArticle;
import com.health.entity.Notification;
import com.health.entity.User;
import com.health.mapper.DietGoalMapper;
import com.health.mapper.NotificationMapper;
import com.health.service.DietRecordService;
import com.health.service.HealthArticleService;
import com.health.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/notification")
public class NotificationController {

    @Autowired
    private NotificationMapper notificationMapper;

    @Autowired
    private DietGoalMapper dietGoalMapper;

    @Autowired
    private DietRecordService dietRecordService;

    @Autowired
    private HealthArticleService healthArticleService;

    @Autowired
    private UserService userService;

    @GetMapping("/list")
    public ResponseEntity<?> getNotifications(Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            ensureDefaultNotifications(userId);

            QueryWrapper<Notification> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId)
                .eq("is_deleted", 0)
                .orderByDesc("create_time");

            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "获取消息成功");
            response.put("data", notificationMapper.selectList(wrapper));
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取消息失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PutMapping("/read/{id}")
    public ResponseEntity<?> markAsRead(@PathVariable Long id, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            Notification notification = notificationMapper.selectById(id);
            if (notification == null || !userId.equals(notification.getUserId()) || Integer.valueOf(1).equals(notification.getIsDeleted())) {
                return badRequestResponse("消息不存在");
            }

            notification.setIsRead(1);
            notification.setReadTime(LocalDateTime.now());
            notificationMapper.updateById(notification);

            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "消息已标记为已读");
            response.put("data", notification);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("标记消息失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PutMapping("/delete/{id}")
    public ResponseEntity<?> softDelete(@PathVariable Long id, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            Notification notification = notificationMapper.selectById(id);
            if (notification == null || !userId.equals(notification.getUserId()) || Integer.valueOf(1).equals(notification.getIsDeleted())) {
                return badRequestResponse("消息不存在");
            }

            notification.setIsDeleted(1);
            notificationMapper.updateById(notification);

            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "消息已删除");
            response.put("data", notification.getId());
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("删除消息失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/admin/publish")
    public ResponseEntity<?> publishNotification(@RequestBody Map<String, Object> payload, Principal principal) {
        try {
            requireAdmin(principal);

            String title = String.valueOf(payload.getOrDefault("title", "")).trim();
            String content = String.valueOf(payload.getOrDefault("content", "")).trim();
            String type = String.valueOf(payload.getOrDefault("type", "system")).trim();
            Long targetUserId = payload.get("userId") == null ? null : Long.parseLong(payload.get("userId").toString());

            if (title.isEmpty() || content.isEmpty()) {
                return badRequestResponse("通知标题和内容不能为空");
            }

            int created = 0;
            if (targetUserId != null) {
                createNotification(targetUserId, type, title, content, null, null);
                created = 1;
            } else {
                List<User> users = userService.listUsers();
                for (User user : users) {
                    if (user.getStatus() != null && user.getStatus() == 1) {
                        createNotification(user.getId(), type, title, content, null, null);
                        created += 1;
                    }
                }
            }

            Map<String, Object> response = new HashMap<>();
            response.put("code", 200);
            response.put("message", "通知发布成功");
            response.put("data", created);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("发布通知失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    private void ensureDefaultNotifications(Long userId) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime startOfDay = now.with(LocalTime.MIN);

        if (!existsNotification(userId, "diet_reminder", startOfDay)) {
            DietGoal dietGoal = dietGoalMapper.findByUserId(userId);
            if (dietGoal != null
                && dietGoal.getReminderEnabled() != null
                && dietGoal.getReminderEnabled() == 1
                && isReminderDue(dietGoal, now.toLocalTime())) {
                String time = dietGoal.getReminderTime() == null ? "今日" : dietGoal.getReminderTime().toString();
                String goalType = dietGoal.getGoalType() == null ? "当前目标" : dietGoal.getGoalType();
                createNotification(
                    userId,
                    "diet_reminder",
                    "饮食目标提醒",
                    "你已开启饮食提醒，建议在 " + time + " 回顾并执行「" + goalType + "」计划。",
                    dietGoal.getId(),
                    "diet_goal"
                );
            }
        }

        if (!existsNotification(userId, "warning", startOfDay)) {
            List<String> suggestions = dietRecordService.getDietSuggestions(userId);
            String warning = suggestions.stream()
                .filter(item -> item != null && (item.contains("偏高") || item.contains("不足") || item.contains("较少")))
                .findFirst()
                .orElse(null);
            if (warning != null) {
                createNotification(userId, "warning", "饮食误区提醒", warning, null, "diet_record");
            }
        }

        if (!existsNotification(userId, "article_recommend", startOfDay)) {
            List<HealthArticle> articles = healthArticleService.getRecommendedArticles(userId, 1);
            if (!articles.isEmpty()) {
                HealthArticle article = articles.get(0);
                createNotification(
                    userId,
                    "article_recommend",
                    "健康知识推荐",
                    "为你推荐《" + article.getTitle() + "》，可以帮助你更好地执行当前饮食目标。",
                    article.getId(),
                    "article"
                );
            }
        }
    }

    private boolean existsNotification(Long userId, String type, LocalDateTime startTime) {
        QueryWrapper<Notification> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId)
            .eq("type", type)
            .eq("is_deleted", 0)
            .ge("create_time", startTime);
        return notificationMapper.selectCount(wrapper) > 0;
    }

    private void createNotification(Long userId, String type, String title, String content, Long relatedId, String relatedType) {
        Notification notification = new Notification();
        notification.setUserId(userId);
        notification.setType(type);
        notification.setTitle(title);
        notification.setContent(content);
        notification.setRelatedId(relatedId);
        notification.setRelatedType(relatedType);
        notification.setIsRead(0);
        notification.setIsDeleted(0);
        notification.setSendTime(LocalDateTime.now());
        notificationMapper.insert(notification);
    }

    private boolean isReminderDue(DietGoal dietGoal, LocalTime currentTime) {
        LocalTime reminderTime = dietGoal.getReminderTime();
        if (reminderTime == null) {
            return true;
        }
        return !currentTime.isBefore(reminderTime);
    }

    private void requireAdmin(Principal principal) {
        if (principal == null) {
            throw new RuntimeException("未登录或登录已过期");
        }
        User currentUser = userService.findById(Long.parseLong(principal.getName()));
        if (!userService.isAdmin(currentUser)) {
            throw new RuntimeException("无权限执行该操作");
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
