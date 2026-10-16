package com.health.controller;

import com.health.service.AssistantChatService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import javax.validation.Valid;
import java.io.IOException;
import java.security.Principal;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/assistant")
public class AssistantChatController {

    /**
     * SSE 连接的最长存活时间（毫秒）。0 = 永不超时，这里给个上限：
     * 万一模型那边卡死，连接不会一直挂着不放。180s 对一次问答绰绰有余。
     */
    private static final long SSE_TIMEOUT_MS = 180_000L;

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

    /**
     * 流式聊天（SSE）。
     *
     * ⚠️ **新增端点，不动 POST /assistant/chat** ——
     *    非流式那条路上有近百条用例在跑（结构 / 意图 / 安全 / 越狱），
     *    换传输方式不该逼着它们跟着改；两条路并存，客户端可以逐个切过来。
     *
     * 返回 SseEmitter：Spring 会把响应变成 text/event-stream，之后每一段都靠 emitter.send 推。
     * 客户端实际打的是 /api/assistant/chat/stream（/api 是 context-path）。
     */
    @PostMapping(value = "/chat/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chatStream(Principal principal, @Valid @RequestBody(required = false) Map<String, Object> payload) {
        SseEmitter emitter = new SseEmitter(SSE_TIMEOUT_MS);

        Long userId = null;
        if (principal != null) {
            try {
                userId = Long.parseLong(principal.getName());
            } catch (NumberFormatException exception) {
                log.warn("SSE 聊天：无法解析用户身份 {}", principal.getName());
            }
        }

        if (userId == null) {
            // 正常走不到这里 —— SecurityConfig 对 /assistant/** 要求已认证，未登录在过滤器阶段就被 401 拦掉。
            // 这是兜底：让客户端拿到一个明确的 error 事件，而不是一个永远等不到内容的空流。
            sendUnauthorizedEvent(emitter);
            return emitter;
        }

        // 注意：chatStream **立刻返回**，真正的推送在它内部的独立线程里跑。
        // 随后把 emitter 交还给 Spring —— 这一步不能省，只有返回之后
        // Spring 才会初始化异步上下文、开始逐段刷新。
        assistantChatService.chatStream(userId, payload, emitter);
        return emitter;
    }

    private void sendUnauthorizedEvent(SseEmitter emitter) {
        try {
            emitter.send(SseEmitter.event()
                .name("error")
                .data(Collections.singletonMap("message", "未登录或登录已过期"), MediaType.APPLICATION_JSON));
        } catch (IOException ignored) {
            // 客户端已断开，忽略
        } finally {
            emitter.complete();
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
