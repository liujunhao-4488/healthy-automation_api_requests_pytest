package com.health.service;

import java.util.List;
import java.util.Map;

public interface AssistantChatService {

    List<Map<String, Object>> getConversations(Long userId);

    Map<String, Object> createConversation(Long userId, Map<String, Object> payload);

    List<Map<String, Object>> getMessages(Long userId, Long conversationId);

    Map<String, Object> chat(Long userId, Map<String, Object> payload);

    void deleteConversation(Long userId, Long conversationId);
}
