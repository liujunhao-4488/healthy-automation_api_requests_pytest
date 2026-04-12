package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.health.entity.AssistantConversation;
import com.health.entity.AssistantMessage;
import com.health.mapper.AssistantConversationMapper;
import com.health.mapper.AssistantMessageMapper;
import com.health.service.AssistantChatService;
import com.health.service.RecipeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AssistantChatServiceImpl implements AssistantChatService {

    private static final String DEFAULT_CONVERSATION_TITLE = "AI 助手会话";
    private static final int TITLE_PREVIEW_LENGTH = 12;
    private static final int MAX_SUMMARY_LENGTH = 120;

    @Autowired
    private AssistantConversationMapper assistantConversationMapper;

    @Autowired
    private AssistantMessageMapper assistantMessageMapper;

    @Autowired
    private RecipeService recipeService;

    @Autowired
    private ObjectMapper objectMapper;

    @Override
    public List<Map<String, Object>> getConversations(Long userId) {
        QueryWrapper<AssistantConversation> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId)
            .eq("is_deleted", 0)
            .orderByDesc("last_message_at")
            .orderByDesc("update_time")
            .orderByDesc("id");

        List<Map<String, Object>> conversations = new ArrayList<>();
        for (AssistantConversation conversation : assistantConversationMapper.selectList(wrapper)) {
            normalizeConversationTitle(conversation);
            conversations.add(toConversationMap(conversation));
        }
        return conversations;
    }

    @Override
    @Transactional
    public Map<String, Object> createConversation(Long userId, Map<String, Object> payload) {
        String requestedTitle = payload == null ? null : String.valueOf(payload.getOrDefault("title", "")).trim();

        AssistantConversation conversation = new AssistantConversation();
        conversation.setUserId(userId);
        conversation.setTitle(resolveConversationTitle(requestedTitle, null));
        conversation.setSummary(null);
        conversation.setMessageCount(0);
        conversation.setLastMessageAt(null);
        conversation.setIsDeleted(0);
        assistantConversationMapper.insert(conversation);
        return toConversationMap(assistantConversationMapper.selectById(conversation.getId()));
    }

    @Override
    public List<Map<String, Object>> getMessages(Long userId, Long conversationId) {
        AssistantConversation conversation = requireConversation(userId, conversationId);

        QueryWrapper<AssistantMessage> wrapper = new QueryWrapper<>();
        wrapper.eq("conversation_id", conversation.getId())
            .eq("user_id", userId)
            .orderByAsc("id");

        List<Map<String, Object>> messages = new ArrayList<>();
        for (AssistantMessage message : assistantMessageMapper.selectList(wrapper)) {
            messages.add(toMessageMap(message));
        }
        return messages;
    }

    @Override
    @Transactional
    public Map<String, Object> chat(Long userId, Map<String, Object> payload) {
        if (payload == null) {
            throw new RuntimeException("聊天请求不能为空");
        }

        String rawPrompt = readText(payload.get("rawPrompt"));
        if (rawPrompt.isEmpty()) {
            rawPrompt = readText(payload.get("prompt"));
        }
        if (rawPrompt.isEmpty()) {
            throw new RuntimeException("请输入聊天内容");
        }

        String promptWithContext = readText(payload.get("prompt"));
        Long conversationId = toLong(payload.get("conversationId"));

        AssistantConversation conversation = conversationId == null
            ? createConversationEntity(userId, rawPrompt)
            : requireConversation(userId, conversationId);

        boolean hasMessages = conversation.getMessageCount() != null && conversation.getMessageCount() > 0;
        if (!hasMessages) {
            conversation.setTitle(resolveConversationTitle(conversation.getTitle(), rawPrompt));
        }

        AssistantMessage userMessage = saveMessage(conversation.getId(), userId, "user", rawPrompt, null, "text");

        AssistantMessage contextMessage = null;
        if (!promptWithContext.isEmpty() && !promptWithContext.equals(rawPrompt)) {
            contextMessage = saveMessage(conversation.getId(), userId, "context", promptWithContext, null, "context");
        }

        Map<String, Object> request = new HashMap<>(payload);
        request.put("userId", userId);
        request.put("rawPrompt", rawPrompt);
        request.put("ingredientName", rawPrompt);
        request.put("prompt", promptWithContext.isEmpty() ? rawPrompt : promptWithContext);

        Map<String, Object> assistantResult = recipeService.getIngredientSubstitutes(request);
        AssistantMessage assistantMessage = saveAssistantReply(conversation.getId(), userId, assistantResult);

        refreshConversation(conversation, rawPrompt, assistantMessage.getContent());

        Map<String, Object> result = new HashMap<>();
        result.put("conversationId", conversation.getId());
        result.put("conversation", toConversationMap(conversation));
        result.put("userMessage", toMessageMap(userMessage));
        result.put("contextMessage", contextMessage == null ? null : toMessageMap(contextMessage));
        result.put("assistantMessage", toMessageMap(assistantMessage));
        return result;
    }

    @Override
    @Transactional
    public void deleteConversation(Long userId, Long conversationId) {
        AssistantConversation conversation = requireConversation(userId, conversationId);
        conversation.setIsDeleted(1);
        assistantConversationMapper.updateById(conversation);
    }

    private AssistantConversation createConversationEntity(Long userId, String rawPrompt) {
        AssistantConversation conversation = new AssistantConversation();
        conversation.setUserId(userId);
        conversation.setTitle(resolveConversationTitle(null, rawPrompt));
        conversation.setSummary(null);
        conversation.setMessageCount(0);
        conversation.setLastMessageAt(null);
        conversation.setIsDeleted(0);
        assistantConversationMapper.insert(conversation);
        return assistantConversationMapper.selectById(conversation.getId());
    }

    private AssistantConversation requireConversation(Long userId, Long conversationId) {
        if (conversationId == null) {
            throw new RuntimeException("会话不存在");
        }

        AssistantConversation conversation = assistantConversationMapper.selectById(conversationId);
        if (conversation == null
            || !userId.equals(conversation.getUserId())
            || Integer.valueOf(1).equals(conversation.getIsDeleted())) {
            throw new RuntimeException("会话不存在或无权访问");
        }
        return conversation;
    }

    private void normalizeConversationTitle(AssistantConversation conversation) {
        if (conversation == null) {
            return;
        }

        QueryWrapper<AssistantMessage> wrapper = new QueryWrapper<>();
        wrapper.eq("conversation_id", conversation.getId())
            .eq("user_id", conversation.getUserId())
            .eq("role", "user")
            .orderByAsc("id")
            .last("LIMIT 1");

        AssistantMessage firstUserMessage = assistantMessageMapper.selectOne(wrapper);
        if (firstUserMessage == null) {
            return;
        }

        String nextTitle = trimTitle(firstUserMessage.getContent());
        if (!nextTitle.isEmpty() && !nextTitle.equals(conversation.getTitle())) {
            conversation.setTitle(nextTitle);
            assistantConversationMapper.updateById(conversation);
        }
    }

    private AssistantMessage saveAssistantReply(Long conversationId, Long userId, Map<String, Object> assistantResult) {
        String mode = assistantResult == null ? "" : readText(assistantResult.get("mode"));
        String text = assistantResult == null ? "" : readText(assistantResult.get("text"));
        List<Map<String, Object>> cards = extractCards(assistantResult);

        if (text.isEmpty() && cards.isEmpty()) {
            text = "暂时没有生成可用的建议，请稍后再试。";
        }

        String messageType = "cards".equalsIgnoreCase(mode) || !cards.isEmpty() ? "cards" : "text";
        return saveMessage(conversationId, userId, "assistant", text, cards, messageType);
    }

    private AssistantMessage saveMessage(
        Long conversationId,
        Long userId,
        String role,
        String content,
        List<Map<String, Object>> cards,
        String messageType
    ) {
        AssistantMessage message = new AssistantMessage();
        message.setConversationId(conversationId);
        message.setUserId(userId);
        message.setRole(role);
        message.setContent(content);
        message.setCardsJson(serializeCards(cards));
        message.setMessageType(messageType);
        assistantMessageMapper.insert(message);
        return assistantMessageMapper.selectById(message.getId());
    }

    private void refreshConversation(AssistantConversation conversation, String rawPrompt, String assistantReply) {
        QueryWrapper<AssistantMessage> countWrapper = new QueryWrapper<>();
        countWrapper.eq("conversation_id", conversation.getId())
            .eq("user_id", conversation.getUserId());

        conversation.setMessageCount(Math.toIntExact(assistantMessageMapper.selectCount(countWrapper)));
        conversation.setLastMessageAt(LocalDateTime.now());
        conversation.setSummary(resolveSummary(assistantReply, rawPrompt));
        assistantConversationMapper.updateById(conversation);
    }

    private Map<String, Object> toConversationMap(AssistantConversation conversation) {
        Map<String, Object> data = new HashMap<>();
        data.put("id", conversation.getId());
        data.put("title", conversation.getTitle());
        data.put("summary", conversation.getSummary());
        data.put("messageCount", conversation.getMessageCount() == null ? 0 : conversation.getMessageCount());
        data.put("lastMessageAt", conversation.getLastMessageAt());
        data.put("createTime", conversation.getCreateTime());
        data.put("updateTime", conversation.getUpdateTime());
        return data;
    }

    private Map<String, Object> toMessageMap(AssistantMessage message) {
        Map<String, Object> data = new HashMap<>();
        data.put("id", message.getId());
        data.put("role", message.getRole());
        data.put("text", message.getContent());
        data.put("messageType", readText(message.getMessageType()));
        data.put("cards", deserializeCards(message.getCardsJson()));
        data.put("createTime", message.getCreateTime());
        return data;
    }

    private List<Map<String, Object>> extractCards(Map<String, Object> assistantResult) {
        if (assistantResult == null) {
            return new ArrayList<>();
        }

        Object cardsObj = assistantResult.get("cards");
        if (cardsObj instanceof List) {
            return castCards((List<?>) cardsObj);
        }

        Object dataObj = assistantResult.get("data");
        if (dataObj instanceof List) {
            return castCards((List<?>) dataObj);
        }
        return new ArrayList<>();
    }

    private List<Map<String, Object>> castCards(List<?> rawCards) {
        List<Map<String, Object>> cards = new ArrayList<>();
        for (Object rawCard : rawCards) {
            if (rawCard instanceof Map) {
                cards.add(new HashMap<>((Map<String, Object>) rawCard));
            }
        }
        return cards;
    }

    private List<Map<String, Object>> deserializeCards(String cardsJson) {
        if (cardsJson == null || cardsJson.trim().isEmpty()) {
            return new ArrayList<>();
        }
        try {
            return objectMapper.readValue(cardsJson, new TypeReference<List<Map<String, Object>>>() {
            });
        } catch (Exception ignored) {
            return new ArrayList<>();
        }
    }

    private String serializeCards(List<Map<String, Object>> cards) {
        if (cards == null || cards.isEmpty()) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(cards);
        } catch (Exception ignored) {
            return null;
        }
    }

    private String resolveConversationTitle(String requestedTitle, String fallbackPrompt) {
        String candidate = readText(requestedTitle);
        if (candidate.isEmpty() || DEFAULT_CONVERSATION_TITLE.equals(candidate)) {
            candidate = readText(fallbackPrompt);
        }
        if (candidate.isEmpty()) {
            candidate = DEFAULT_CONVERSATION_TITLE;
        }
        return trimTitle(candidate);
    }

    private String resolveSummary(String assistantReply, String rawPrompt) {
        String candidate = readText(assistantReply);
        if (candidate.isEmpty()) {
            candidate = readText(rawPrompt);
        }
        return candidate.isEmpty() ? null : trimToLength(candidate.replace("\n", " "), MAX_SUMMARY_LENGTH);
    }

    private String trimToLength(String value, int maxLength) {
        String text = readText(value);
        if (text.length() <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength - 1) + "…";
    }

    private String trimTitle(String value) {
        String text = readText(value);
        if (text.length() <= TITLE_PREVIEW_LENGTH) {
            return text;
        }
        return text.substring(0, TITLE_PREVIEW_LENGTH) + "...";
    }

    private String readText(Object value) {
        if (value == null) {
            return "";
        }
        return String.valueOf(value).trim();
    }

    private Long toLong(Object value) {
        if (value instanceof Number) {
            return ((Number) value).longValue();
        }
        if (value instanceof String) {
            String text = ((String) value).trim();
            if (!text.isEmpty()) {
                try {
                    return Long.parseLong(text);
                } catch (NumberFormatException ignored) {
                    return null;
                }
            }
        }
        return null;
    }
}
