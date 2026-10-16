package com.health.service;

import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.Map;

public interface AssistantChatService {

    List<Map<String, Object>> getConversations(Long userId);

    Map<String, Object> createConversation(Long userId, Map<String, Object> payload);

    List<Map<String, Object>> getMessages(Long userId, Long conversationId);

    Map<String, Object> chat(Long userId, Map<String, Object> payload);

    /**
     * 流式聊天：把模型回答通过 SSE 边生成边推给客户端。
     *
     * 与非流式 chat 的区别**只在传输方式** ——
     * 会话创建、用户消息落库、助手消息落库、会话刷新，这些完全一样（落库仍然是一次性的，
     * 不是"边流边写库"），所以返回结构、历史记录、用例断言口径都不变。
     *
     * 事件顺序（name/data）：
     *   start → {conversationId, conversation, userMessage}
     *   delta → {text}            （0..N 次，模型分片；硬拦/报错时是整段固定文案）
     *   done  → {conversationId, conversation, assistantMessage}
     *   error → {message}         （出异常时才出现，之后流结束）
     *
     * ⚠️ 本方法是**立即返回**的：真正的推送交给内部一个独立线程跑完
     *    （Controller 必须先返回 SseEmitter，Spring 才会初始化异步上下文并开始逐段刷新）。
     */
    void chatStream(Long userId, Map<String, Object> payload, SseEmitter emitter);

    void deleteConversation(Long userId, Long conversationId);
}
