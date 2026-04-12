package com.health.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.dto.UserProfileUpdateDTO;
import com.health.entity.User;
import com.health.entity.UserDietPreference;
import com.health.mapper.UserDietPreferenceMapper;
import com.health.service.UserService;
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
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/user")
public class UserController {

    @Autowired
    private UserService userService;

    @Autowired
    private UserDietPreferenceMapper userDietPreferenceMapper;

    @GetMapping("/profile")
    public ResponseEntity<?> getProfile(Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            User user = userService.findById(Long.parseLong(principal.getName()));
            if (user == null) {
                return badRequestResponse("用户不存在");
            }
            return successResponse("获取个人资料成功", sanitizeUser(user));
        } catch (Exception e) {
            log.error("获取个人资料失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PutMapping("/profile")
    public ResponseEntity<?> updateProfile(@Valid @RequestBody UserProfileUpdateDTO profileDTO, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            User user = userService.updateProfile(Long.parseLong(principal.getName()), profileDTO);
            return successResponse("个人资料更新成功", sanitizeUser(user));
        } catch (Exception e) {
            log.error("更新个人资料失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/admin/list")
    public ResponseEntity<?> listUsers(Principal principal) {
        try {
            requireAdmin(principal);
            List<Map<String, Object>> users = userService.listUsers()
                .stream()
                .map(this::sanitizeUser)
                .collect(Collectors.toList());
            return successResponse("获取用户列表成功", users);
        } catch (Exception e) {
            log.error("获取用户列表失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PutMapping("/admin/{userId}/status")
    public ResponseEntity<?> updateUserStatus(
        @PathVariable Long userId,
        @RequestParam Integer status,
        Principal principal
    ) {
        try {
            requireAdmin(principal);
            User user = userService.updateUserStatus(userId, status);
            return successResponse("用户状态更新成功", sanitizeUser(user));
        } catch (Exception e) {
            log.error("更新用户状态失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/diet-preference")
    public ResponseEntity<?> getDietPreference(Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            UserDietPreference preference = userDietPreferenceMapper.selectOne(
                new QueryWrapper<UserDietPreference>().eq("user_id", userId).last("LIMIT 1")
            );
            if (preference == null) {
                preference = new UserDietPreference();
                preference.setUserId(userId);
                preference.setMealFrequency(3);
                preference.setSnackPreference(1);
            }
            return successResponse("获取饮食偏好成功", preference);
        } catch (Exception e) {
            log.error("获取饮食偏好失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PutMapping("/diet-preference")
    public ResponseEntity<?> updateDietPreference(@RequestBody UserDietPreference preference, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            UserDietPreference existing = userDietPreferenceMapper.selectOne(
                new QueryWrapper<UserDietPreference>().eq("user_id", userId).last("LIMIT 1")
            );

            if (existing == null) {
                preference.setId(null);
                preference.setUserId(userId);
                if (preference.getMealFrequency() == null) {
                    preference.setMealFrequency(3);
                }
                if (preference.getSnackPreference() == null) {
                    preference.setSnackPreference(1);
                }
                userDietPreferenceMapper.insert(preference);
                existing = preference;
            } else {
                existing.setDietType(preference.getDietType());
                existing.setAllergies(preference.getAllergies());
                existing.setDislikes(preference.getDislikes());
                existing.setFavorites(preference.getFavorites());
                existing.setMealFrequency(preference.getMealFrequency() == null ? existing.getMealFrequency() : preference.getMealFrequency());
                existing.setSnackPreference(preference.getSnackPreference() == null ? existing.getSnackPreference() : preference.getSnackPreference());
                userDietPreferenceMapper.updateById(existing);
            }

            return successResponse("饮食偏好更新成功", existing);
        } catch (Exception e) {
            log.error("更新饮食偏好失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
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

    private Map<String, Object> sanitizeUser(User user) {
        Map<String, Object> data = new HashMap<>();
        data.put("userId", user.getId());
        data.put("username", user.getUsername());
        data.put("email", user.getEmail());
        data.put("phone", user.getPhone());
        data.put("avatar", user.getAvatar());
        data.put("status", user.getStatus());
        data.put("createTime", user.getCreateTime());
        data.put("updateTime", user.getUpdateTime());
        data.put("role", userService.resolveRole(user));
        return data;
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
