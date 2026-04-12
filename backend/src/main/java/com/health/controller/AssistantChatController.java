package com.health.controller;

import com.health.service.AssistantChatService;
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
@RequestMapping("/assistant")
public class AssistantChatController {

    @Autowired
    private AssistantChatService assistantChatService;

    @GetMapping("/conversations")
    public ResponseEntity<?> getConversations(Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            return successResponse("获取会话列表成功", assistantChatService.getConversations(userId));
        } catch (Exception e) {
            log.error("获取会话列表失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/conversations")
    public ResponseEntity<?> createConversation(Principal principal, @Valid @RequestBody(required = false) Map<String, Object> payload) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            return successResponse("创建会话成功", assistantChatService.createConversation(userId, payload));
        } catch (Exception e) {
            log.error("创建会话失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/conversations/{conversationId}/messages")
    public ResponseEntity<?> getMessages(@PathVariable Long conversationId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            return successResponse("获取消息成功", assistantChatService.getMessages(userId, conversationId));
        } catch (Exception e) {
            log.error("获取消息失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/chat")
    public ResponseEntity<?> chat(Principal principal, @Valid @RequestBody Map<String, Object> payload) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            return successResponse("发送消息成功", assistantChatService.chat(userId, payload));
        } catch (Exception e) {
            log.error("AI 小助手聊天失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @DeleteMapping("/conversations/{conversationId}")
    public ResponseEntity<?> deleteConversation(@PathVariable Long conversationId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            assistantChatService.deleteConversation(userId, conversationId);
            return successResponse("删除会话成功", conversationId);
        } catch (Exception e) {
            log.error("删除会话失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    private ResponseEntity<Map<String, Object>> successResponse(String message, Object data) {
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
