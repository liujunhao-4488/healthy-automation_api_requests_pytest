package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.health.entity.DietGoal;
import com.health.entity.HealthInfo;
import com.health.entity.Ingredient;
import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;
import com.health.entity.UserDietPreference;
import com.health.mapper.DietGoalMapper;
import com.health.mapper.HealthInfoMapper;
import com.health.mapper.IngredientMapper;
import com.health.mapper.RecipeIngredientMapper;
import com.health.mapper.RecipeMapper;
import com.health.mapper.UserDietPreferenceMapper;
import com.health.service.RecipeService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

@Service
@Slf4j
public class RecipeServiceImpl implements RecipeService {

    private static final String PYTHON_SERVICE_URL = "http://localhost:5000";

    @Value("${deepseek.api-key:}")
    private String deepSeekApiKey;

    @Value("${deepseek.base-url:https://api.deepseek.com}")
    private String deepSeekBaseUrl;

    @Value("${deepseek.model:deepseek-chat}")
    private String deepSeekModel;

    @Autowired
    private RecipeMapper recipeMapper;

    @Autowired
    private RecipeIngredientMapper recipeIngredientMapper;

    @Autowired
    private IngredientMapper ingredientMapper;

    @Autowired
    private HealthInfoMapper healthInfoMapper;

    @Autowired
    private DietGoalMapper dietGoalMapper;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private UserDietPreferenceMapper userDietPreferenceMapper;

    @Autowired
    private ObjectMapper objectMapper;

    @Override
    public List<Recipe> getAllRecipes() {
        return recipeMapper.selectList(null);
    }

    @Override
    public Recipe getRecipeById(Long id) {
        return recipeMapper.selectById(id);
    }

    @Override
    public List<RecipeIngredient> getRecipeIngredients(Long recipeId) {
        return recipeIngredientMapper.selectByRecipeId(recipeId);
    }

    @Override
    public List<Recipe> getCustomRecipes(Long userId) {
        return recipeMapper.selectCustomByUserId(userId);
    }

    @Override
    public List<Recipe> searchRecipes(String keyword) {
        QueryWrapper<Recipe> wrapper = new QueryWrapper<>();
        wrapper.like("name", keyword).or().like("description", keyword);
        return recipeMapper.selectList(wrapper);
    }

    @Transactional
    @Override
    public Recipe saveRecipe(Recipe recipe, List<RecipeIngredient> ingredients) {
        recipeMapper.insert(recipe);
        for (RecipeIngredient ingredient : ingredients) {
            ingredient.setRecipeId(recipe.getId());
            recipeIngredientMapper.insert(ingredient);
        }
        calculateRecipeNutrition(recipe);
        return recipe;
    }

    @Transactional
    @Override
    public Recipe updateRecipe(Recipe recipe, List<RecipeIngredient> ingredients) {
        recipeMapper.updateById(recipe);

        QueryWrapper<RecipeIngredient> wrapper = new QueryWrapper<>();
        wrapper.eq("recipe_id", recipe.getId());
        recipeIngredientMapper.delete(wrapper);

        for (RecipeIngredient ingredient : ingredients) {
            ingredient.setRecipeId(recipe.getId());
            recipeIngredientMapper.insert(ingredient);
        }

        calculateRecipeNutrition(recipe);
        return recipe;
    }

    @Transactional
    @Override
    public boolean deleteRecipe(Long id) {
        QueryWrapper<RecipeIngredient> wrapper = new QueryWrapper<>();
        wrapper.eq("recipe_id", id);
        recipeIngredientMapper.delete(wrapper);
        return recipeMapper.deleteById(id) > 0;
    }

    @Override
    public Map<String, Object> analyzeRecipeNutrition(Long recipeId) {
        Recipe recipe = recipeMapper.selectById(recipeId);
        Map<String, Object> nutrition = new HashMap<>();

        if (recipe != null) {
            double totalCalories = safeDouble(recipe.getTotalCalories());
            double protein = safeDouble(recipe.getProtein());
            double carbs = safeDouble(recipe.getCarbs());
            double fat = safeDouble(recipe.getFat());

            nutrition.put("totalCalories", totalCalories);
            nutrition.put("protein", protein);
            nutrition.put("carbs", carbs);
            nutrition.put("fat", fat);
            nutrition.put("score", calculateNutritionScore(totalCalories, protein, carbs, fat));
            nutrition.put("analysis", buildNutritionAnalysis(totalCalories, protein, carbs, fat));
            nutrition.put("suggestion", buildNutritionSuggestion(totalCalories, protein, carbs, fat));
        }

        return nutrition;
    }

    private double calculateNutritionScore(double totalCalories, double protein, double carbs, double fat) {
        double score = 60;

        if (totalCalories >= 250 && totalCalories <= 700) {
            score += 10;
        } else if (totalCalories > 0) {
            score += 4;
        }

        if (protein >= 20) {
            score += 12;
        } else if (protein >= 12) {
            score += 8;
        } else if (protein > 0) {
            score += 4;
        }

        if (carbs >= 20 && carbs <= 80) {
            score += 8;
        } else if (carbs > 0) {
            score += 4;
        }

        if (fat <= 25) {
            score += 10;
        } else if (fat <= 35) {
            score += 6;
        } else {
            score += 2;
        }

        return Math.min(100, Math.max(0, score));
    }

    private String buildNutritionAnalysis(double totalCalories, double protein, double carbs, double fat) {
        List<String> parts = new ArrayList<>();

        if (totalCalories <= 0) {
            return "暂未统计出该食谱的有效营养数据。";
        }

        parts.add("该食谱总热量约为 " + formatNutritionNumber(totalCalories) + " kcal。");

        if (protein >= 20) {
            parts.add("蛋白质含量较高，适合作为优质蛋白补充。");
        } else if (protein >= 10) {
            parts.add("蛋白质含量中等，能提供一定饱腹感和营养支持。");
        } else {
            parts.add("蛋白质含量偏低，如作为正餐建议搭配额外蛋白来源。");
        }

        if (fat > 25) {
            parts.add("脂肪含量偏高，整体能量密度较高。");
        } else if (fat > 0) {
            parts.add("脂肪控制相对平稳，整体结构较均衡。");
        }

        if (carbs >= 50) {
            parts.add("碳水化合物较充足，适合作为日常主餐能量来源。");
        } else if (carbs >= 20) {
            parts.add("碳水化合物适中，适合多数日常搭配场景。");
        }

        return String.join("", parts);
    }

    private String buildNutritionSuggestion(double totalCalories, double protein, double carbs, double fat) {
        if (totalCalories <= 0) {
            return "建议先完善食材用量和营养数据，再进行分析。";
        }

        List<String> parts = new ArrayList<>();

        if (protein < 15) {
            parts.add("可适当增加鸡蛋、瘦肉、鱼虾、豆制品等高蛋白食材，提高整体蛋白质量。");
        }
        if (fat > 25) {
            parts.add("建议减少额外油脂或高脂配料，烹饪时优先选择蒸、煮、炖等方式。");
        }
        if (carbs < 20) {
            parts.add("如作为正餐，可搭配米饭、全麦面、土豆等主食，提升能量和饱腹感。");
        }
        if (parts.isEmpty()) {
            parts.add("整体营养结构较均衡，可结合个人目标继续微调食材比例和烹饪方式。");
        }

        return String.join("", parts);
    }

    private String formatNutritionNumber(double value) {
        return Math.abs(value - Math.rint(value)) < 0.001
            ? String.valueOf((int) Math.rint(value))
            : String.format(Locale.ROOT, "%.1f", value);
    }

    @Override
    public Map<String, List<?>> getRecommendedRecipes(Long userId, Integer breakfastCount, Integer lunchCount, Integer dinnerCount) {
        Map<String, List<?>> recommendedRecipes = new HashMap<>();
        HealthInfo healthInfo = healthInfoMapper.findByUserId(userId);
        DietGoal dietGoal = dietGoalMapper.findByUserId(userId);

        try {
            Map<String, Object> requestData = new HashMap<>();
            requestData.put("userId", userId);
            requestData.put("breakfastCount", breakfastCount);
            requestData.put("lunchCount", lunchCount);
            requestData.put("dinnerCount", dinnerCount);
            requestData.put("healthInfo", buildHealthInfoPayload(healthInfo));
            requestData.put("dietGoal", buildDietGoalPayload(dietGoal));
            requestData.put("candidateRecipes", buildAlgorithmCandidates());

            String url = PYTHON_SERVICE_URL + "/api/recommend/recipes";
            Map<String, Object> response = restTemplate.postForObject(url, requestData, Map.class);
            if (response != null && response.containsKey("data")) {
                return (Map<String, List<?>>) response.get("data");
            }
        } catch (RestClientException ignored) {
        }

        List<Map<String, Object>> breakfast = getLocalRecommendedRecipes(userId, "breakfast", breakfastCount);
        List<Map<String, Object>> lunch = getLocalRecommendedRecipes(userId, "lunch", lunchCount);
        List<Map<String, Object>> dinner = getLocalRecommendedRecipes(userId, "dinner", dinnerCount);

        recommendedRecipes.put("breakfast", breakfast);
        recommendedRecipes.put("lunch", lunch);
        recommendedRecipes.put("dinner", dinner);
        return recommendedRecipes;
    }

    @Override
    public List<Recipe> getRecommendedRecipes(Long userId, String mealType, int limit) {
        List<Map<String, Object>> localRecommendations = getLocalRecommendedRecipes(userId, mealType, limit);
        if (!localRecommendations.isEmpty()) {
            List<Recipe> recipes = new ArrayList<>();
            for (Map<String, Object> item : localRecommendations) {
                Object id = item.get("id");
                if (id instanceof Number) {
                    Recipe recipe = recipeMapper.selectById(((Number) id).longValue());
                    if (recipe != null) {
                        recipes.add(recipe);
                    }
                }
            }
            if (!recipes.isEmpty()) {
                return recipes;
            }
        }

        try {
            Map<String, Object> requestData = new HashMap<>();
            requestData.put("userId", userId);
            requestData.put("mealType", mealType);
            requestData.put("limit", limit);

            String url = PYTHON_SERVICE_URL + "/api/recommend/recipe";
            Map<String, Object> response = restTemplate.postForObject(url, requestData, Map.class);
            if (response != null && response.containsKey("data")) {
                return (List<Recipe>) response.get("data");
            }
        } catch (RestClientException ignored) {
        }

        return new ArrayList<>();
    }

    @Override
    public Map<String, Object> getIngredientSubstitutes(Map<String, Object> ingredientData) {
        Map<String, Object> deepSeekResult = getDeepSeekIngredientAssistantResult(ingredientData);
        if (deepSeekResult != null && !deepSeekResult.isEmpty()) {
            return deepSeekResult;
        }

        List<Map<String, Object>> substitutes = new ArrayList<>();
        try {
            String url = PYTHON_SERVICE_URL + "/api/ingredient/substitute";
            Map<String, Object> response = restTemplate.postForObject(url, ingredientData, Map.class);
            if (response != null && response.containsKey("data") && response.get("data") instanceof List) {
                substitutes = (List<Map<String, Object>>) response.get("data");
            }
        } catch (RestClientException ignored) {
        }

        if (substitutes.isEmpty()) {
            substitutes.addAll(buildLocalAssistantCards(ingredientData));
        }

        return buildAssistantTextResult(buildLocalAssistantReply(ingredientData, substitutes), "local");
    }

    private Map<String, Object> getDeepSeekIngredientAssistantResult(Map<String, Object> ingredientData) {
        if (deepSeekApiKey == null || deepSeekApiKey.trim().isEmpty()) {
            return null;
        }

        String question = extractIngredientQuestion(ingredientData);
        if (question.isEmpty()) {
            return null;
        }

        Long userId = null;
        Object userIdObj = ingredientData.get("userId");
        if (userIdObj instanceof Number) {
            userId = ((Number) userIdObj).longValue();
        } else if (userIdObj instanceof String) {
            try {
                userId = Long.parseLong((String) userIdObj);
            } catch (NumberFormatException ignored) {
            }
        }

        HealthInfo healthInfo = userId == null ? null : healthInfoMapper.findByUserId(userId);
        DietGoal dietGoal = userId == null ? null : dietGoalMapper.findByUserId(userId);
        UserDietPreference preference = userId == null ? null : userDietPreferenceMapper.selectOne(
            new QueryWrapper<UserDietPreference>().eq("user_id", userId).last("LIMIT 1")
        );
        Map<String, Object> healthInfoPayload = extractMap(ingredientData.get("healthInfo"));
        Map<String, Object> dietGoalPayload = extractMap(ingredientData.get("dietGoal"));
        String assistantContext = buildIngredientAssistantContext(healthInfo, dietGoal, preference, healthInfoPayload, dietGoalPayload);

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setBearerAuth(deepSeekApiKey.trim());

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", deepSeekModel);
            requestBody.put("temperature", 0.6);

            List<Map<String, String>> messages = new ArrayList<>();
            messages.add(buildMessage(
                "system",
                "你是一位专业的食材小助手。请根据用户当前健康状况、饮食目标、过敏和慢病信息，"
                    + "优先给出 3 个更合适的替代食材建议。请严格返回 JSON 数组，"
                    + "每个元素包含 name、similarity、nutrition_difference、usage_suggestion 四个字段。"
                    + "similarity 使用“高 / 适中 / 一般”之一，不要输出 markdown。"
            ));
            messages.add(buildMessage("system", assistantContext));
            messages.clear();
            messages.add(buildMessage("system", buildIngredientAssistantSystemPrompt()));
            messages.add(buildMessage("system", assistantContext));
            messages.add(buildMessage("user", buildIngredientAssistantNaturalUserPrompt(question, assistantContext)));
            requestBody.put("messages", messages);

            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(requestBody, headers);
            ResponseEntity<Map> responseEntity = restTemplate.postForEntity(
                deepSeekBaseUrl + "/chat/completions",
                requestEntity,
                Map.class
            );

            return parseDeepSeekSubstitutes(responseEntity.getBody(), question);
        } catch (Exception exception) {
            log.error("DeepSeek 食材小助手调用失败: {}", exception.getMessage(), exception);
            return null;
        }
    }

    private String buildIngredientAssistantContext(HealthInfo healthInfo, DietGoal dietGoal, UserDietPreference preference) {
        StringBuilder context = new StringBuilder("以下是用户当前信息。");
        if (healthInfo != null) {
            context.append(" 年龄=").append(valueOrDash(healthInfo.getAge()));
            context.append("，性别=").append(valueOrDash(healthInfo.getGender()));
            context.append("，身高=").append(valueOrDash(healthInfo.getHeight())).append("cm");
            context.append("，体重=").append(valueOrDash(healthInfo.getWeight())).append("kg");
            context.append("，BMI=").append(valueOrDash(healthInfo.getBmi()));
            context.append("，基础代谢=").append(valueOrDash(healthInfo.getBmr())).append("kcal");
            context.append("，活动水平=").append(valueOrDash(healthInfo.getActivityLevel()));
            context.append("，慢性疾病=").append(valueOrDash(healthInfo.getChronicDiseases())).append("。");
        }
        if (preference != null) {
            context.append(" 饮食偏好中的过敏/忌口=").append(valueOrDash(preference.getAllergies())).append("。");
        }
        if (dietGoal != null) {
            context.append(" 当前饮食目标=").append(valueOrDash(dietGoal.getGoalType()));
            context.append("，目标热量=").append(valueOrDash(dietGoal.getTargetCalories())).append("kcal");
            context.append("，蛋白质目标=").append(valueOrDash(dietGoal.getProteinTarget())).append("g");
            context.append("，碳水目标=").append(valueOrDash(dietGoal.getCarbsTarget())).append("g");
            context.append("，脂肪目标=").append(valueOrDash(dietGoal.getFatTarget())).append("g");
            context.append("，饮水目标=").append(valueOrDash(dietGoal.getWaterTarget())).append("ml。");
        }
        context.append(" 请在回答时优先考虑饮食偏好中的过敏/忌口、慢性疾病、目标热量和宏量营养素方向。");
        return context.toString();
    }

    private String buildIngredientAssistantContext(
        HealthInfo healthInfo,
        DietGoal dietGoal,
        UserDietPreference preference,
        Map<String, Object> healthInfoPayload,
        Map<String, Object> dietGoalPayload
    ) {
        if ((healthInfoPayload != null && !healthInfoPayload.isEmpty()) || (dietGoalPayload != null && !dietGoalPayload.isEmpty()) || preference != null) {
            StringBuilder context = new StringBuilder("以下是用户当前信息。");
            if (healthInfoPayload != null && !healthInfoPayload.isEmpty()) {
                context.append(" 健康档案：")
                    .append("年龄=").append(valueOrDash(readPayloadValue(healthInfoPayload, "age")))
                    .append("，性别=").append(valueOrDash(readPayloadValue(healthInfoPayload, "gender")))
                    .append("，身高=").append(valueOrDash(readPayloadValue(healthInfoPayload, "height"))).append("cm")
                    .append("，体重=").append(valueOrDash(readPayloadValue(healthInfoPayload, "weight"))).append("kg")
                    .append("，BMI=").append(valueOrDash(readPayloadValue(healthInfoPayload, "bmi")))
                    .append("，基础代谢=").append(valueOrDash(readPayloadValue(healthInfoPayload, "bmr"))).append("kcal")
                    .append("，活动水平=").append(valueOrDash(readPayloadValue(healthInfoPayload, "activityLevel")))
                    .append("，慢病情况=").append(valueOrDash(readPayloadValue(healthInfoPayload, "chronicDiseases")))
                    .append("。");
            }
            if (preference != null) {
                context.append(" 饮食偏好：")
                    .append("过敏/忌口=").append(valueOrDash(preference.getAllergies()))
                    .append("，不喜欢食物=").append(valueOrDash(preference.getDislikes()))
                    .append("。");
            }
            if (dietGoalPayload != null && !dietGoalPayload.isEmpty()) {
                context.append(" 饮食目标：")
                    .append("目标类型=").append(valueOrDash(readPayloadValue(dietGoalPayload, "goalType")))
                    .append("，目标热量=").append(valueOrDash(readPayloadValue(dietGoalPayload, "targetCalories"))).append("kcal")
                    .append("，蛋白质目标=").append(valueOrDash(readPayloadValue(dietGoalPayload, "proteinTarget"))).append("g")
                    .append("，碳水目标=").append(valueOrDash(readPayloadValue(dietGoalPayload, "carbsTarget"))).append("g")
                    .append("，脂肪目标=").append(valueOrDash(readPayloadValue(dietGoalPayload, "fatTarget"))).append("g")
                    .append("，饮水目标=").append(valueOrDash(readPayloadValue(dietGoalPayload, "waterTarget"))).append("ml")
                    .append("。");
            }
            context.append(" 请在回答时优先考虑饮食偏好中的过敏/忌口、慢性疾病、目标热量和宏量营养素方向。");
            return context.toString();
        }
        return buildIngredientAssistantContext(healthInfo, dietGoal, preference);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> extractMap(Object value) {
        if (value instanceof Map) {
            return (Map<String, Object>) value;
        }
        return null;
    }

    private Object readPayloadValue(Map<String, Object> payload, String key) {
        if (payload == null) {
            return null;
        }
        return payload.get(key);
    }

    private String valueOrDash(Object value) {
        if (value == null) {
            return "--";
        }
        String text = String.valueOf(value).trim();
        return text.isEmpty() ? "--" : text;
    }

    private Map<String, String> buildMessage(String role, String content) {
        Map<String, String> message = new HashMap<>();
        message.put("role", role);
        message.put("content", content);
        return message;
    }

    private String buildIngredientAssistantSystemPrompt() {
        return "你是一位专业的食材替代与饮食搭配助手。"
            + "请结合用户当前健康档案、饮食目标、饮食偏好中的过敏/忌口和慢性病信息，用自然、专业、清晰的中文直接回答问题。"
            + "回答时优先先给结论，再解释为什么适合该用户。"
            + "如果合适，可以分点给出 2 到 4 个替代方案，并说明营养差异和使用建议。"
            + "不要返回 JSON，不要返回代码块，也不要用字段名模板式输出。";
    }

    private String buildIngredientAssistantNaturalUserPrompt(String question, String assistantContext) {
        return "请结合以下用户信息回答食材替代问题。\n"
            + assistantContext + "\n"
            + "用户问题：" + question + "\n"
            + "要求：先直接回答这个问题，再说明为什么这些替代方案适合该用户当前身体状况和饮食目标。"
            + "请用自然语言分段回答，不要返回 JSON。";
    }

    private Map<String, Object> parseDeepSeekSubstitutes(Map responseBody, String question) {
        if (responseBody == null) {
            return null;
        }

        Object choicesObj = responseBody.get("choices");
        if (!(choicesObj instanceof List) || ((List<?>) choicesObj).isEmpty()) {
            return null;
        }

        Object firstChoice = ((List<?>) choicesObj).get(0);
        if (!(firstChoice instanceof Map)) {
            return null;
        }

        Object messageObj = ((Map<?, ?>) firstChoice).get("message");
        if (!(messageObj instanceof Map)) {
            return null;
        }

        Object contentObj = ((Map<?, ?>) messageObj).get("content");
        if (!(contentObj instanceof String)) {
            return null;
        }

        String content = ((String) contentObj).trim();
        if (content.isEmpty()) {
            return null;
        }

        try {
            JsonNode node = objectMapper.readTree(extractJsonContent(content));
            if (node.isArray()) {
                return buildAssistantTextResult(formatArrayReply(node), "deepseek");
            }
            if (node.isObject()) {
                return buildAssistantTextResult(formatObjectReply(node), "deepseek");
            }
        } catch (Exception ignored) {
        }

        String text = content;
        if (text.startsWith("```")) {
            text = text.replace("```json", "").replace("```", "").trim();
        }
        if (text.startsWith("{") || text.startsWith("[")) {
            text = "AI 已返回建议，但自动格式化失败。以下是原始回复：\n" + text;
        }
        return buildAssistantTextResult(text, "deepseek");
    }

    private Map<String, Object> buildAssistantTextResult(String text, String source) {
        Map<String, Object> result = new HashMap<>();
        result.put("mode", "text");
        result.put("text", text == null ? "" : text.trim());
        result.put("source", source);
        return result;
    }

    private String buildLocalAssistantReply(Map<String, Object> ingredientData, List<Map<String, Object>> cards) {
        String question = extractIngredientQuestion(ingredientData);
        if (cards == null || cards.isEmpty()) {
            return "暂时没有生成合适的替代建议，请换个问法再试试。";
        }

        StringBuilder builder = new StringBuilder();
        builder.append("结合你当前的健康档案和饮食目标，");
        if (!question.isEmpty()) {
            builder.append("关于“").append(question).append("”，");
        }
        builder.append("可以优先参考以下替代方案：\n\n");

        for (int index = 0; index < cards.size(); index++) {
            Map<String, Object> card = cards.get(index);
            String name = valueOrDash(card.get("name"));
            String similarity = valueOrDash(card.get("similarity"));
            String nutritionDifference = valueOrDash(card.get("nutrition_difference"));
            String usageSuggestion = valueOrDash(card.get("usage_suggestion"));

            builder.append(index + 1).append(". ").append(name);
            if (!"--".equals(similarity)) {
                builder.append("（匹配度：").append(similarity).append("）");
            }
            builder.append("\n");

            if (!"--".equals(nutritionDifference)) {
                builder.append("营养差异：").append(nutritionDifference).append("\n");
            }
            if (!"--".equals(usageSuggestion)) {
                builder.append("使用建议：").append(usageSuggestion).append("\n");
            }
            builder.append("\n");
        }

        builder.append("如果你愿意，我还可以继续按你当前目标帮你细化到早餐、午餐或晚餐的具体搭配。");
        return builder.toString().trim();
    }

    private String formatObjectReply(JsonNode node) {
        List<String> sections = new ArrayList<>();
        String answer = node.path("answer").asText("").trim();
        String reason = node.path("reason").asText("").trim();

        if (!answer.isEmpty()) {
            sections.add(answer);
        }
        if (!reason.isEmpty()) {
            sections.add("为什么适合你：\n" + reason);
        }

        JsonNode alternatives = node.path("alternatives");
        if (alternatives.isArray() && alternatives.size() > 0) {
            sections.add("可优先参考这些替代方案：\n" + formatAlternatives(alternatives));
        }

        return String.join("\n\n", sections).trim();
    }

    private String formatArrayReply(JsonNode arrayNode) {
        if (arrayNode == null || !arrayNode.isArray() || arrayNode.size() == 0) {
            return "";
        }
        return "可优先参考这些替代方案：\n" + formatAlternatives(arrayNode);
    }

    private String formatAlternatives(JsonNode alternatives) {
        List<String> lines = new ArrayList<>();
        int index = 1;
        for (JsonNode item : alternatives) {
            String name = item.path("name").asText("替代方案");
            String similarity = item.path("similarity").asText("").trim();
            String nutritionDifference = item.path("nutrition_difference").asText("").trim();
            String usageSuggestion = item.path("usage_suggestion").asText("").trim();

            StringBuilder block = new StringBuilder();
            block.append(index++).append(". ").append(name);
            if (!similarity.isEmpty()) {
                block.append("（匹配度：").append(similarity).append("）");
            }
            if (!nutritionDifference.isEmpty()) {
                block.append("\n营养差异：").append(nutritionDifference);
            }
            if (!usageSuggestion.isEmpty()) {
                block.append("\n使用建议：").append(usageSuggestion);
            }
            lines.add(block.toString());
        }
        return String.join("\n\n", lines);
    }

    private String extractJsonContent(String content) {
        int arrayStart = content.indexOf('[');
        int arrayEnd = content.lastIndexOf(']');
        if (arrayStart >= 0 && arrayEnd > arrayStart) {
            return content.substring(arrayStart, arrayEnd + 1);
        }

        int objectStart = content.indexOf('{');
        int objectEnd = content.lastIndexOf('}');
        if (objectStart >= 0 && objectEnd > objectStart) {
            return content.substring(objectStart, objectEnd + 1);
        }
        return content;
    }

    private String extractIngredientQuestion(Map<String, Object> ingredientData) {
        if (ingredientData == null) {
            return "";
        }

        Object prompt = ingredientData.get("prompt");
        if (prompt instanceof String && !((String) prompt).trim().isEmpty()) {
            return ((String) prompt).trim();
        }

        Object ingredientName = ingredientData.get("ingredientName");
        if (ingredientName instanceof String && !((String) ingredientName).trim().isEmpty()) {
            return ((String) ingredientName).trim();
        }

        Object ingredient = ingredientData.get("ingredient");
        if (ingredient instanceof String && !((String) ingredient).trim().isEmpty()) {
            return ((String) ingredient).trim();
        }

        return "";
    }

    private List<Map<String, Object>> buildLocalAssistantCards(Map<String, Object> ingredientData) {
        String question = extractIngredientQuestion(ingredientData).toLowerCase(Locale.ROOT);
        Long userId = null;
        Object userIdObj = ingredientData.get("userId");
        if (userIdObj instanceof Number) {
            userId = ((Number) userIdObj).longValue();
        } else if (userIdObj instanceof String) {
            try {
                userId = Long.parseLong((String) userIdObj);
            } catch (NumberFormatException ignored) {
            }
        }

        HealthInfo healthInfo = userId == null ? null : healthInfoMapper.findByUserId(userId);
        DietGoal dietGoal = userId == null ? null : dietGoalMapper.findByUserId(userId);
        UserDietPreference preference = userId == null ? null : userDietPreferenceMapper.selectOne(
            new QueryWrapper<UserDietPreference>().eq("user_id", userId).last("LIMIT 1")
        );
        String goalType = dietGoal == null ? "" : String.valueOf(dietGoal.getGoalType()).toLowerCase(Locale.ROOT);
        String allergies = preference == null || preference.getAllergies() == null ? "" : preference.getAllergies().toLowerCase(Locale.ROOT);

        List<Map<String, Object>> cards = new ArrayList<>();

        if (containsAny(question, "鸡胸肉", "鸡肉")) {
            addAssistantCard(cards, "去皮鸡腿肉", "高", "脂肪略高于鸡胸肉，但蛋白质接近，热量稍高。", buildUsageSuggestion(goalType, "可煎、烤或炖煮，适合作为主菜补充优质蛋白。"));
            if (!containsAny(allergies, "牛", "牛肉")) {
                addAssistantCard(cards, "瘦牛肉（如里脊）", "适中", "蛋白质含量高，富含铁和锌，脂肪略高。", buildUsageSuggestion(goalType, "适合切片快炒或做牛肉饼，能提升蛋白质和热量摄入。"));
            }
            addAssistantCard(cards, "老豆腐", "一般", "植物蛋白较稳定，脂肪较低，但单次蛋白密度不如肉类。", buildUsageSuggestion(goalType, "适合与鸡蛋或主食搭配，做成煎豆腐或豆腐炒菜。"));
        } else if (containsAny(question, "牛奶", "乳糖")) {
            if (!containsAny(allergies, "豆")) {
                addAssistantCard(cards, "强化豆奶", "高", "蛋白质接近牛奶，无乳糖，更适合乳糖不耐受人群。", buildUsageSuggestion(goalType, "可直接替代牛奶饮用，也适合搭配燕麦或全麦面包。"));
            }
            addAssistantCard(cards, "无乳糖牛奶", "高", "营养构成与普通牛奶接近，但乳糖已被分解。", buildUsageSuggestion(goalType, "如果只是乳糖不耐受，优先选择无乳糖版本最方便。"));
            addAssistantCard(cards, "无糖酸奶（低乳糖或无乳糖）", "适中", "发酵后乳糖更低，蛋白质和钙含量也较稳定。", buildUsageSuggestion(goalType, "适合作为早餐或加餐，帮助补充蛋白质和热量。"));
        } else if (containsAny(question, "海鲜", "海虾", "虾", "鱼")) {
            addAssistantCard(cards, "鸡蛋", "高", "蛋白质优质、过敏风险通常低于海鲜，做法灵活。", buildUsageSuggestion(goalType, "可做蒸蛋、炒蛋或蛋饼，搭配蔬菜和主食使用。"));
            addAssistantCard(cards, "鸡胸肉", "高", "蛋白质高、脂肪较低，适合多数饮食目标。", buildUsageSuggestion(goalType, "适合煎、煮、烤，作为海鲜的直接蛋白替代。"));
            if (!containsAny(allergies, "豆")) {
                addAssistantCard(cards, "豆腐", "适中", "植物蛋白稳定，口感清淡，适合做配菜或主菜。", buildUsageSuggestion(goalType, "可与蔬菜同炒或炖煮，提升餐盘搭配多样性。"));
            }
        } else if (containsAny(question, "搭配", "晚餐", "午餐", "早餐")) {
            addAssistantCard(cards, "鸡蛋", "高", "蛋白质吸收率高，适合快速补充优质蛋白。", buildUsageSuggestion(goalType, "可与现有蔬菜或豆制品一起搭配成主菜。"));
            addAssistantCard(cards, "豆腐", "适中", "植物蛋白和水分充足，适合做成清炒、炖煮或煎制菜肴。", buildUsageSuggestion(goalType, "适合和西兰花、鸡蛋、主食搭配做成均衡一餐。"));
            addAssistantCard(cards, "糙米或全麦主食", "适中", "能补充碳水化合物和额外热量，让一餐更完整。", buildUsageSuggestion(goalType, "如果目标是增重或维持体重，建议搭配主食一起吃。"));
        }

        if (cards.isEmpty()) {
            addAssistantCard(cards, "鸡蛋", "适中", "优质蛋白来源稳定，适合多数替代场景。", buildUsageSuggestion(goalType, "可作为常见食材的基础替代，和蔬菜、主食组合食用。"));
            addAssistantCard(cards, "豆腐", "适中", "植物蛋白温和，适合清淡和家常搭配。", buildUsageSuggestion(goalType, "适合作为家常替代方案，提升蛋白质来源多样性。"));
            addAssistantCard(cards, "糙米", "一般", "可补充碳水和部分膳食纤维，帮助完善整体能量结构。", buildUsageSuggestion(goalType, "如果你问的是整餐搭配，这类主食通常需要一起考虑。"));
        }

        return cards;
    }

    private void addAssistantCard(List<Map<String, Object>> cards, String name, String similarity, String nutritionDifference, String usageSuggestion) {
        Map<String, Object> card = new HashMap<>();
        card.put("name", name);
        card.put("similarity", similarity);
        card.put("nutrition_difference", nutritionDifference);
        card.put("usage_suggestion", usageSuggestion);
        cards.add(card);
    }

    private boolean containsAny(String source, String... keywords) {
        if (source == null || source.isEmpty()) {
            return false;
        }
        for (String keyword : keywords) {
            if (keyword != null && !keyword.isEmpty() && source.contains(keyword.toLowerCase(Locale.ROOT))) {
                return true;
            }
        }
        return false;
    }

    private String buildUsageSuggestion(String goalType, String defaultSuggestion) {
        if (goalType == null) {
            return defaultSuggestion;
        }
        if (containsAny(goalType, "减脂", "减肥", "fat_loss")) {
            return defaultSuggestion + " 更适合控制总热量和脂肪摄入。";
        }
        if (containsAny(goalType, "增肌", "塑形", "muscle")) {
            return defaultSuggestion + " 有助于补充蛋白质并支持肌肉恢复。";
        }
        if (containsAny(goalType, "控糖", "blood_sugar")) {
            return defaultSuggestion + " 建议搭配低 GI 主食并控制额外糖分。";
        }
        if (containsAny(goalType, "增重", "weight_gain")) {
            return defaultSuggestion + " 可以适当增加主食或健康脂肪，帮助提高总热量。";
        }
        return defaultSuggestion;
    }

    @Override
    public List<?> getRecipesByGoal(Long userId, Map<String, Object> goalData) {
        List<?> recipes = new ArrayList<>();

        try {
            Map<String, Object> requestData = new HashMap<>();
            requestData.put("userId", userId);
            requestData.putAll(goalData);

            String url = PYTHON_SERVICE_URL + "/api/recommend/by-goal";
            Map<String, Object> response = restTemplate.postForObject(url, requestData, Map.class);
            if (response != null && response.containsKey("data")) {
                recipes = (List<?>) response.get("data");
            }
        } catch (RestClientException ignored) {
        }

        return recipes;
    }

    @Override
    public Map<String, Object> getTodayRecommendedRecipes(Long userId) {
        return new HashMap<>(getRecommendedRecipes(userId, 1, 1, 1));
    }

    private void calculateRecipeNutrition(Recipe recipe) {
        List<RecipeIngredient> ingredients = recipeIngredientMapper.selectByRecipeId(recipe.getId());
        double totalCalories = 0;
        double totalProtein = 0;
        double totalCarbs = 0;
        double totalFat = 0;

        for (RecipeIngredient recipeIngredient : ingredients) {
            Ingredient ingredient = ingredientMapper.selectById(recipeIngredient.getIngredientId());
            if (ingredient != null) {
                double quantity = safeDouble(recipeIngredient.getQuantity());
                double ratio = quantity / 100.0;

                totalCalories += safeDouble(ingredient.getCaloriesPer100g()) * ratio;
                totalProtein += safeDouble(ingredient.getProteinPer100g()) * ratio;
                totalCarbs += safeDouble(ingredient.getCarbsPer100g()) * ratio;
                totalFat += safeDouble(ingredient.getFatPer100g()) * ratio;
            }
        }

        recipe.setTotalCalories(totalCalories);
        recipe.setProtein(totalProtein);
        recipe.setCarbs(totalCarbs);
        recipe.setFat(totalFat);

        recipeMapper.updateById(recipe);
    }

    private List<Map<String, Object>> getLocalRecommendedRecipes(Long userId, String mealType, int limit) {
        List<Recipe> allRecipes = recipeMapper.selectList(
            new QueryWrapper<Recipe>().orderByDesc("score").orderByDesc("collect_count").orderByDesc("view_count")
        );
        if (allRecipes.isEmpty()) {
            return new ArrayList<>();
        }

        HealthInfo healthInfo = healthInfoMapper.findByUserId(userId);
        DietGoal dietGoal = dietGoalMapper.findByUserId(userId);
        UserDietPreference preference = userDietPreferenceMapper.selectOne(
            new QueryWrapper<UserDietPreference>().eq("user_id", userId).last("LIMIT 1")
        );
        double mealTargetCalories = resolveMealTargetCalories(healthInfo, dietGoal, mealType);
        MacroProfile macroProfile = resolveMacroProfile(dietGoal);

        List<Map<String, Object>> scoredRecipes = new ArrayList<>();
        for (Recipe recipe : allRecipes) {
            if (isExcludedByPreferences(recipe, healthInfo, preference)) {
                continue;
            }

            double matchScore = calculateRecipeScore(recipe, mealType, mealTargetCalories, macroProfile, healthInfo, dietGoal, preference);
            if (matchScore <= 0) {
                continue;
            }

            scoredRecipes.add(buildRecipePayload(recipe, mealType, mealTargetCalories, healthInfo, dietGoal, preference, matchScore));
        }

        Collections.sort(scoredRecipes, new Comparator<Map<String, Object>>() {
            @Override
            public int compare(Map<String, Object> left, Map<String, Object> right) {
                Double leftScore = toDouble(left.get("matchScore"));
                Double rightScore = toDouble(right.get("matchScore"));
                return rightScore.compareTo(leftScore);
            }
        });

        if (scoredRecipes.size() > limit) {
            return new ArrayList<>(scoredRecipes.subList(0, limit));
        }
        return scoredRecipes;
    }

    private Map<String, Object> buildRecipePayload(
        Recipe recipe,
        String mealType,
        double mealTargetCalories,
        HealthInfo healthInfo,
        DietGoal dietGoal,
        UserDietPreference preference,
        double matchScore
    ) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("id", recipe.getId());
        payload.put("name", recipe.getName());
        payload.put("description", recipe.getDescription());
        payload.put("difficulty", recipe.getDifficulty());
        payload.put("cookingTime", recipe.getCookingTime());
        payload.put("totalCalories", safeDouble(recipe.getTotalCalories()));
        payload.put("protein", safeDouble(recipe.getProtein()));
        payload.put("carbs", safeDouble(recipe.getCarbs()));
        payload.put("fat", safeDouble(recipe.getFat()));
        payload.put("fiber", safeDouble(recipe.getFiber()));
        payload.put("mealType", mealType);
        payload.put("matchScore", Math.round(matchScore));
        payload.put("targetCalories", Math.round(mealTargetCalories));
        payload.put("tags", buildTags(recipe, mealType, healthInfo, dietGoal));
        payload.put("recommendationReason", buildRecommendationReason(recipe, mealType, mealTargetCalories, healthInfo, dietGoal, preference));
        payload.put("ingredients", buildIngredientPayload(recipe.getId()));
        payload.put("steps", splitInstructions(recipe.getInstructions()));
        return payload;
    }

    private List<Map<String, Object>> buildIngredientPayload(Long recipeId) {
        List<Map<String, Object>> ingredientPayload = new ArrayList<>();
        List<RecipeIngredient> recipeIngredients = recipeIngredientMapper.selectByRecipeId(recipeId);

        for (RecipeIngredient recipeIngredient : recipeIngredients) {
            Ingredient ingredient = ingredientMapper.selectById(recipeIngredient.getIngredientId());
            if (ingredient == null) {
                continue;
            }
            Map<String, Object> item = new HashMap<>();
            item.put("id", ingredient.getId());
            item.put("name", ingredient.getName());
            item.put("ingredientId", ingredient.getId());
            item.put("quantityValue", recipeIngredient.getQuantity());
            item.put("unit", recipeIngredient.getUnit());
            item.put("quantity", formatQuantity(recipeIngredient.getQuantity(), recipeIngredient.getUnit()));
            double ratio = safeDouble(recipeIngredient.getQuantity()) / 100.0;
            item.put("calories", safeDouble(ingredient.getCaloriesPer100g()) * ratio);
            item.put("protein", safeDouble(ingredient.getProteinPer100g()) * ratio);
            item.put("carbs", safeDouble(ingredient.getCarbsPer100g()) * ratio);
            item.put("fat", safeDouble(ingredient.getFatPer100g()) * ratio);
            ingredientPayload.add(item);
        }

        return ingredientPayload;
    }

    private Map<String, Object> buildHealthInfoPayload(HealthInfo healthInfo) {
        Map<String, Object> payload = new HashMap<>();
        if (healthInfo == null) {
            return payload;
        }
        payload.put("age", healthInfo.getAge());
        payload.put("gender", healthInfo.getGender());
        payload.put("height", healthInfo.getHeight());
        payload.put("weight", healthInfo.getWeight());
        payload.put("bmi", healthInfo.getBmi());
        payload.put("bmr", healthInfo.getBmr());
        payload.put("activityLevel", healthInfo.getActivityLevel());
        payload.put("chronicDiseases", healthInfo.getChronicDiseases());
        return payload;
    }

    private Map<String, Object> buildDietGoalPayload(DietGoal dietGoal) {
        Map<String, Object> payload = new HashMap<>();
        if (dietGoal == null) {
            return payload;
        }
        payload.put("goalType", dietGoal.getGoalType());
        payload.put("targetCalories", dietGoal.getTargetCalories());
        payload.put("proteinRatio", dietGoal.getProteinRatio());
        payload.put("carbsRatio", dietGoal.getCarbsRatio());
        payload.put("fatRatio", dietGoal.getFatRatio());
        payload.put("proteinTarget", dietGoal.getProteinTarget());
        payload.put("carbsTarget", dietGoal.getCarbsTarget());
        payload.put("fatTarget", dietGoal.getFatTarget());
        payload.put("waterTarget", dietGoal.getWaterTarget());
        payload.put("targetWeight", dietGoal.getTargetWeight());
        return payload;
    }

    private List<Map<String, Object>> buildAlgorithmCandidates() {
        List<Recipe> recipes = recipeMapper.selectList(
            new QueryWrapper<Recipe>().orderByDesc("score").orderByDesc("collect_count").orderByDesc("view_count")
        );
        List<Map<String, Object>> candidates = new ArrayList<>();
        for (Recipe recipe : recipes) {
            Map<String, Object> candidate = new HashMap<>();
            candidate.put("id", recipe.getId());
            candidate.put("name", recipe.getName());
            candidate.put("description", recipe.getDescription());
            candidate.put("category", recipe.getCategory());
            candidate.put("difficulty", recipe.getDifficulty());
            candidate.put("cookingTime", recipe.getCookingTime());
            candidate.put("totalCalories", safeDouble(recipe.getTotalCalories()));
            candidate.put("protein", safeDouble(recipe.getProtein()));
            candidate.put("carbs", safeDouble(recipe.getCarbs()));
            candidate.put("fat", safeDouble(recipe.getFat()));
            candidate.put("fiber", safeDouble(recipe.getFiber()));
            candidate.put("tips", recipe.getTips());
            candidate.put("mealType", inferMealType(recipe));
            candidate.put("ingredients", buildIngredientPayload(recipe.getId()));
            candidate.put("steps", splitInstructions(recipe.getInstructions()));
            candidates.add(candidate);
        }
        return candidates;
    }

    private String formatQuantity(Double quantity, String unit) {
        if (quantity == null && (unit == null || unit.trim().isEmpty())) {
            return "";
        }
        String quantityText = quantity == null ? "" : String.valueOf(quantity % 1 == 0 ? quantity.intValue() : quantity);
        String unitText = unit == null ? "" : unit;
        return (quantityText + unitText).trim();
    }

    private List<String> splitInstructions(String instructions) {
        if (instructions == null || instructions.trim().isEmpty()) {
            return new ArrayList<>();
        }

        String[] rawSteps = instructions.replace("；", "\n").replace("。", "\n").split("\\r?\\n");
        List<String> steps = new ArrayList<>();
        for (String rawStep : rawSteps) {
            String step = rawStep.trim();
            if (!step.isEmpty()) {
                steps.add(step);
            }
        }
        return steps;
    }

    private double calculateRecipeScore(
        Recipe recipe,
        String mealType,
        double mealTargetCalories,
        MacroProfile macroProfile,
        HealthInfo healthInfo,
        DietGoal dietGoal,
        UserDietPreference preference
    ) {
        double score = 0;
        score += scoreMealFit(recipe, mealType);
        score += scoreCalories(recipe, mealTargetCalories);
        score += scoreMacroFit(recipe, macroProfile);
        score += scoreGoalFit(recipe, healthInfo, dietGoal);
        score += scoreSuitability(recipe, dietGoal);
        score += scorePracticality(recipe, mealType);
        score += scorePreferenceFit(recipe, preference);
        return Math.max(score, 1);
    }

    private double scoreMealFit(Recipe recipe, String mealType) {
        String text = normalizeText(recipe.getName()) + " " + normalizeText(recipe.getCategory()) + " " + normalizeText(recipe.getDescription());
        for (String keyword : getMealKeywords(mealType)) {
            if (text.contains(keyword)) {
                return 24;
            }
        }

        double calories = safeDouble(recipe.getTotalCalories());
        if ("breakfast".equals(mealType) && calories <= 420) {
            return 18;
        }
        if ("lunch".equals(mealType) && calories >= 350 && calories <= 720) {
            return 18;
        }
        if ("dinner".equals(mealType) && calories <= 620) {
            return 18;
        }
        return 10;
    }

    private double scoreCalories(Recipe recipe, double mealTargetCalories) {
        double calories = safeDouble(recipe.getTotalCalories());
        if (mealTargetCalories <= 0 || calories <= 0) {
            return 12;
        }

        double differenceRatio = Math.abs(calories - mealTargetCalories) / mealTargetCalories;
        if (differenceRatio <= 0.1) {
            return 26;
        }
        if (differenceRatio <= 0.2) {
            return 22;
        }
        if (differenceRatio <= 0.35) {
            return 16;
        }
        return 8;
    }

    private double scoreMacroFit(Recipe recipe, MacroProfile macroProfile) {
        double calories = safeDouble(recipe.getTotalCalories());
        if (calories <= 0) {
            return 10;
        }

        double proteinCalories = safeDouble(recipe.getProtein()) * 4;
        double carbsCalories = safeDouble(recipe.getCarbs()) * 4;
        double fatCalories = safeDouble(recipe.getFat()) * 9;
        double recipeCalories = proteinCalories + carbsCalories + fatCalories;
        if (recipeCalories <= 0) {
            recipeCalories = calories;
        }

        double proteinRatio = proteinCalories / recipeCalories;
        double carbsRatio = carbsCalories / recipeCalories;
        double fatRatio = fatCalories / recipeCalories;
        double distance =
            Math.abs(proteinRatio - macroProfile.proteinRatio) +
            Math.abs(carbsRatio - macroProfile.carbsRatio) +
            Math.abs(fatRatio - macroProfile.fatRatio);

        if (distance <= 0.12) {
            return 22;
        }
        if (distance <= 0.2) {
            return 18;
        }
        if (distance <= 0.28) {
            return 14;
        }
        return 8;
    }

    private double scoreGoalFit(Recipe recipe, HealthInfo healthInfo, DietGoal dietGoal) {
        String goalType = dietGoal == null ? "" : normalizeText(dietGoal.getGoalType());
        double score = 10;
        double protein = safeDouble(recipe.getProtein());
        double carbs = safeDouble(recipe.getCarbs());
        double fat = safeDouble(recipe.getFat());
        double fiber = safeDouble(recipe.getFiber());
        double calories = safeDouble(recipe.getTotalCalories());

        if ("fat_loss".equals(goalType)) {
            if (protein >= 20) score += 5;
            if (fat <= 18) score += 4;
            if (calories <= 520) score += 5;
        } else if ("muscle_toning".equals(goalType)) {
            if (protein >= 25) score += 8;
            if (calories >= 350) score += 3;
        } else if ("healthy_weight_gain".equals(goalType)) {
            if (calories >= 420) score += 6;
            if (carbs >= 30) score += 4;
            if (protein >= 18) score += 3;
        } else if ("blood_sugar_control".equals(goalType)) {
            if (carbs <= 35) score += 6;
            if (fiber >= 4) score += 4;
        } else if ("lipid_control".equals(goalType)) {
            if (fat <= 16) score += 6;
            if (fiber >= 4) score += 4;
        } else if ("low_sodium".equals(goalType)) {
            if (isLightCooking(recipe)) score += 8;
        } else if ("pregnancy_nutrition".equals(goalType)) {
            if (protein >= 18) score += 5;
            if (fiber >= 3) score += 3;
        } else if ("child_growth".equals(goalType)) {
            if (protein >= 16) score += 5;
            if (calories >= 280 && calories <= 620) score += 4;
        } else if ("senior_wellness".equals(goalType)) {
            if (isEasyToDigest(recipe)) score += 7;
            if (fat <= 18) score += 3;
        } else if ("weight_maintenance".equals(goalType)) {
            if (calories >= 260 && calories <= 620) score += 5;
        }

        String chronicDiseases = healthInfo == null ? "" : normalizeText(healthInfo.getChronicDiseases());
        if (chronicDiseases.contains("糖") && carbs <= 35) {
            score += 3;
        }
        if (chronicDiseases.contains("高血脂") && fat <= 16) {
            score += 3;
        }
        if ((chronicDiseases.contains("高血压") || chronicDiseases.contains("血压")) && isLightCooking(recipe)) {
            score += 3;
        }
        return score;
    }

    private double scoreSuitability(Recipe recipe, DietGoal dietGoal) {
        String suitableFor = normalizeText(recipe.getSuitableFor());
        String goalType = dietGoal == null ? "" : normalizeText(dietGoal.getGoalType());
        if (suitableFor.isEmpty() || goalType.isEmpty()) {
            return 4;
        }

        if (suitableFor.contains(goalType) || suitableFor.contains(mapGoalLabel(goalType))) {
            return 10;
        }
        return 4;
    }

    private double scorePracticality(Recipe recipe, String mealType) {
        int cookingTime = recipe.getCookingTime() == null ? 0 : recipe.getCookingTime();
        if ("breakfast".equals(mealType) && cookingTime > 0 && cookingTime <= 15) {
            return 8;
        }
        if ("dinner".equals(mealType) && cookingTime > 0 && cookingTime <= 30) {
            return 6;
        }
        return 4;
    }

    private boolean isExcludedByPreferences(Recipe recipe, HealthInfo healthInfo, UserDietPreference preference) {
        String preferenceAllergies = preference == null ? "" : normalizeText(preference.getAllergies());
        String dislikes = preference == null ? "" : normalizeText(preference.getDislikes());
        if (preferenceAllergies.isEmpty() && dislikes.isEmpty()) {
            return false;
        }

        String recipeText = normalizeText(recipe.getName()) + " " + normalizeText(recipe.getDescription()) + " " + normalizeText(recipe.getTips());
        List<RecipeIngredient> ingredients = recipeIngredientMapper.selectByRecipeId(recipe.getId());
        for (RecipeIngredient recipeIngredient : ingredients) {
            Ingredient ingredient = ingredientMapper.selectById(recipeIngredient.getIngredientId());
            if (ingredient != null) {
                recipeText += " " + normalizeText(ingredient.getName());
            }
        }

        List<String> excludedTokens = new ArrayList<>();
        excludedTokens.addAll(splitTokens(preferenceAllergies));
        excludedTokens.addAll(splitTokens(dislikes));

        for (String token : excludedTokens) {
            if (!token.isEmpty() && recipeText.contains(token)) {
                return true;
            }
        }
        return false;
    }

    private double scorePreferenceFit(Recipe recipe, UserDietPreference preference) {
        if (preference == null) {
            return 0;
        }

        String recipeText = normalizeText(recipe.getName()) + " " + normalizeText(recipe.getDescription()) + " " + normalizeText(recipe.getTips());
        double score = 0;
        score += scoreTokens(recipeText, preference.getFavorites(), 4);
        score += scoreTokens(recipeText, preference.getDietType(), 3);
        return score;
    }

    private double scoreTokens(String text, String source, double hitScore) {
        if (source == null || source.trim().isEmpty()) {
            return 0;
        }

        double score = 0;
        for (String token : splitTokens(source)) {
            if (!token.isEmpty() && text.contains(token)) {
                score += hitScore;
            }
        }
        return score;
    }

    private List<String> buildTags(Recipe recipe, String mealType, HealthInfo healthInfo, DietGoal dietGoal) {
        Set<String> tags = new LinkedHashSet<>();
        tags.add(mapMealLabel(mealType));

        double calories = safeDouble(recipe.getTotalCalories());
        if (calories > 0) {
            if (calories <= 350) {
                tags.add("轻负担");
            } else if (calories >= 550) {
                tags.add("能量充足");
            } else {
                tags.add("热量适中");
            }
        }

        if (safeDouble(recipe.getProtein()) >= 20) {
            tags.add("高蛋白");
        }
        if (safeDouble(recipe.getFiber()) >= 4) {
            tags.add("高纤维");
        }
        if (safeDouble(recipe.getFat()) <= 15) {
            tags.add("低脂");
        }

        String goalType = dietGoal == null ? "" : normalizeText(dietGoal.getGoalType());
        if (!goalType.isEmpty()) {
            tags.add(mapGoalLabel(goalType));
        }

        if (healthInfo != null && healthInfo.getChronicDiseases() != null) {
            String diseases = normalizeText(healthInfo.getChronicDiseases());
            if (diseases.contains("糖") && safeDouble(recipe.getCarbs()) <= 35) {
                tags.add("控糖友好");
            }
            if (diseases.contains("高血脂") && safeDouble(recipe.getFat()) <= 16) {
                tags.add("控脂友好");
            }
        }

        return new ArrayList<>(tags);
    }

    private String buildRecommendationReason(
        Recipe recipe,
        String mealType,
        double mealTargetCalories,
        HealthInfo healthInfo,
        DietGoal dietGoal,
        UserDietPreference preference
    ) {
        List<String> reasons = new ArrayList<>();
        reasons.add(mapMealLabel(mealType) + "推荐更关注本餐热量分配和营养平衡");

        double calories = safeDouble(recipe.getTotalCalories());
        if (mealTargetCalories > 0 && calories > 0) {
            reasons.add("热量约 " + Math.round(calories) + " kcal，接近该餐建议值 " + Math.round(mealTargetCalories) + " kcal");
        }

        if (safeDouble(recipe.getProtein()) >= 20) {
            reasons.add("蛋白质较充足，有助于提升饱腹感和维持肌肉量");
        }
        if (safeDouble(recipe.getFiber()) >= 4) {
            reasons.add("膳食纤维表现较好，更利于控糖和日常消化");
        }
        if (safeDouble(recipe.getFat()) <= 15) {
            reasons.add("脂肪含量相对克制，更适合轻负担饮食");
        }

        String goalType = dietGoal == null ? "" : normalizeText(dietGoal.getGoalType());
        if (!goalType.isEmpty()) {
            reasons.add("结合你的目标“" + mapGoalLabel(goalType) + "”进行了优先排序");
        }

        if (preference != null && preference.getAllergies() != null && !preference.getAllergies().trim().isEmpty()) {
            reasons.add("已尽量避开你在饮食偏好中填写的过敏/忌口食材");
        }

        return joinSentences(reasons, 3);
    }

    private String joinSentences(List<String> reasons, int limit) {
        StringBuilder builder = new StringBuilder();
        int count = 0;
        for (String reason : reasons) {
            if (reason == null || reason.trim().isEmpty()) {
                continue;
            }
            if (count > 0) {
                builder.append("；");
            }
            builder.append(reason);
            count++;
            if (count >= limit) {
                break;
            }
        }
        return builder.toString();
    }

    private double resolveMealTargetCalories(HealthInfo healthInfo, DietGoal dietGoal, String mealType) {
        double totalCalories = 0;
        if (dietGoal != null && dietGoal.getTargetCalories() != null && dietGoal.getTargetCalories() > 0) {
            totalCalories = dietGoal.getTargetCalories();
        } else if (healthInfo != null) {
            double bmr = healthInfo.getBmr() == null ? 0 : healthInfo.getBmr();
            totalCalories = bmr * resolveActivityMultiplier(healthInfo.getActivityLevel());
        }

        if (totalCalories <= 0) {
            totalCalories = 1800;
        }

        if ("breakfast".equals(mealType)) {
            return totalCalories * 0.3;
        }
        if ("lunch".equals(mealType)) {
            return totalCalories * 0.4;
        }
        return totalCalories * 0.3;
    }

    private double resolveActivityMultiplier(String activityLevel) {
        String level = normalizeText(activityLevel);
        if (level.contains("高") || level.contains("heavy")) {
            return 1.75;
        }
        if (level.contains("中") || level.contains("moderate")) {
            return 1.55;
        }
        if (level.contains("轻") || level.contains("light")) {
            return 1.375;
        }
        return 1.2;
    }

    private MacroProfile resolveMacroProfile(DietGoal dietGoal) {
        if (dietGoal != null &&
            dietGoal.getProteinRatio() != null &&
            dietGoal.getCarbsRatio() != null &&
            dietGoal.getFatRatio() != null) {
            double totalRatio = dietGoal.getProteinRatio() + dietGoal.getCarbsRatio() + dietGoal.getFatRatio();
            if (totalRatio > 1.5) {
                return new MacroProfile(
                    dietGoal.getProteinRatio() / 100.0,
                    dietGoal.getCarbsRatio() / 100.0,
                    dietGoal.getFatRatio() / 100.0
                );
            }
            return new MacroProfile(dietGoal.getProteinRatio(), dietGoal.getCarbsRatio(), dietGoal.getFatRatio());
        }

        String goalType = dietGoal == null ? "" : normalizeText(dietGoal.getGoalType());
        if ("fat_loss".equals(goalType)) {
            return new MacroProfile(0.3, 0.4, 0.3);
        }
        if ("muscle_toning".equals(goalType)) {
            return new MacroProfile(0.32, 0.43, 0.25);
        }
        if ("healthy_weight_gain".equals(goalType)) {
            return new MacroProfile(0.25, 0.5, 0.25);
        }
        if ("blood_sugar_control".equals(goalType)) {
            return new MacroProfile(0.28, 0.37, 0.35);
        }
        if ("lipid_control".equals(goalType)) {
            return new MacroProfile(0.28, 0.45, 0.27);
        }
        if ("low_sodium".equals(goalType) || "senior_wellness".equals(goalType)) {
            return new MacroProfile(0.25, 0.45, 0.3);
        }
        return new MacroProfile(0.25, 0.5, 0.25);
    }

    private boolean isLightCooking(Recipe recipe) {
        String text = normalizeText(recipe.getDescription()) + " " + normalizeText(recipe.getTips()) + " " + normalizeText(recipe.getName());
        return text.contains("蒸") || text.contains("煮") || text.contains("炖") || text.contains("清淡");
    }

    private boolean isEasyToDigest(Recipe recipe) {
        String text = normalizeText(recipe.getDescription()) + " " + normalizeText(recipe.getTips()) + " " + normalizeText(recipe.getName());
        return text.contains("粥") || text.contains("汤") || text.contains("蒸") || text.contains("软");
    }

    private List<String> getMealKeywords(String mealType) {
        if ("breakfast".equals(mealType)) {
            return Arrays.asList("早餐", "早饭", "燕麦", "粥", "牛奶", "鸡蛋", "三明治", "面包");
        }
        if ("lunch".equals(mealType)) {
            return Arrays.asList("午餐", "午饭", "米饭", "鸡胸", "牛肉", "意面", "盖饭", "便当");
        }
        return Arrays.asList("晚餐", "晚饭", "汤", "鱼", "蔬菜", "沙拉", "蒸", "炖");
    }

    private String mapMealLabel(String mealType) {
        if ("breakfast".equals(mealType)) {
            return "早餐";
        }
        if ("lunch".equals(mealType)) {
            return "午餐";
        }
        return "晚餐";
    }

    private String mapGoalLabel(String goalType) {
        if ("fat_loss".equals(goalType)) {
            return "减肥减脂";
        }
        if ("muscle_toning".equals(goalType)) {
            return "增肌塑形";
        }
        if ("weight_maintenance".equals(goalType)) {
            return "维持体重";
        }
        if ("healthy_weight_gain".equals(goalType)) {
            return "健康增重";
        }
        if ("blood_sugar_control".equals(goalType)) {
            return "控糖饮食";
        }
        if ("lipid_control".equals(goalType)) {
            return "控脂降脂";
        }
        if ("low_sodium".equals(goalType)) {
            return "控压低盐";
        }
        if ("pregnancy_nutrition".equals(goalType)) {
            return "孕妇营养";
        }
        if ("child_growth".equals(goalType)) {
            return "儿童成长";
        }
        if ("senior_wellness".equals(goalType)) {
            return "老年养生";
        }
        return "均衡饮食";
    }

    private List<String> splitTokens(String text) {
        if (text == null || text.trim().isEmpty()) {
            return new ArrayList<>();
        }
        String normalized = text.replace("，", ",").replace("、", ",").replace(";", ",").replace("；", ",").replace("/", ",");
        String[] parts = normalized.split(",");
        List<String> tokens = new ArrayList<>();
        for (String part : parts) {
            String token = part.trim().toLowerCase(Locale.ROOT);
            if (!token.isEmpty()) {
                tokens.add(token);
            }
        }
        return tokens;
    }

    private String normalizeText(String text) {
        return text == null ? "" : text.trim().toLowerCase(Locale.ROOT);
    }

    private double safeDouble(Double value) {
        return value == null ? 0 : value;
    }

    private Double toDouble(Object value) {
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        return 0D;
    }

    private String inferMealType(Recipe recipe) {
        String text = normalizeText(recipe.getName()) + " " + normalizeText(recipe.getCategory()) + " " + normalizeText(recipe.getDescription());
        for (String mealType : Arrays.asList("breakfast", "lunch", "dinner")) {
            for (String keyword : getMealKeywords(mealType)) {
                if (text.contains(keyword)) {
                    return mealType;
                }
            }
        }

        double calories = safeDouble(recipe.getTotalCalories());
        if (calories <= 350) {
            return "breakfast";
        }
        if (calories <= 560) {
            return "lunch";
        }
        return "dinner";
    }

    private static class MacroProfile {
        private final double proteinRatio;
        private final double carbsRatio;
        private final double fatRatio;

        private MacroProfile(double proteinRatio, double carbsRatio, double fatRatio) {
            this.proteinRatio = proteinRatio;
            this.carbsRatio = carbsRatio;
            this.fatRatio = fatRatio;
        }
    }
}
