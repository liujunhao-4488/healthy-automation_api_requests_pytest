package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.health.entity.DietGoal;
import com.health.entity.HealthInfo;
import com.health.entity.Ingredient;
import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;
import com.health.entity.AssistantMessage;
import com.health.entity.UserDietPreference;
import com.health.mapper.AssistantMessageMapper;
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
import java.util.regex.Pattern;

@Service
@Slf4j
public class RecipeServiceImpl implements RecipeService {

    private static final String PYTHON_SERVICE_URL = "http://localhost:5000";

    /**
     * 多轮对话历史窗口：最多带入多少条历史消息（约 10 轮，user/assistant 各算一条）。
     */
    private static final int MAX_HISTORY_MESSAGES = 20;

    /**
     * 单条历史消息进入模型前的最大长度，超出截断，避免个别长回复占满上下文。
     */
    private static final int MAX_HISTORY_CONTENT_LENGTH = 500;

    // ══════════ 意图识别（本地关键词规则） ══════════
    // 2026-10-12 新增。在此之前：/assistant/chat 入口**无条件**把任何问题都送进
    // getIngredientSubstitutes，意图既没被算出来、也没被传出来 ——
    // 黑盒测试只能断文本，断不了"它到底判成了什么"，数据集里的 intent 标签一直没人接。
    //
    // 这一步只做两件事：① 把意图**算出来**（下面的 classifyIntent）；
    //                   ② 让它随返回值**透传**到响应里（getIngredientSubstitutes 末尾 put）。
    //
    // ⚠️ 故意**没有改分支走向** —— greeting / out_of_scope 现在仍然会去调模型。
    //    原因：一旦本地短接（比如越界问题不再问模型），"越界必被拒绝"就会从
    //    "模型守不守得住"变成"我写的这句文案对不对"，现在那些盯模型稳定性的
    //    哨兵用例（重复 5 次的 pass^5）就白建了。
    //    分叉怎么切、切哪几类，等这批断言先跑起来、有了真实误判率再定。
    //    —— 一次只改一件事，改完能验收，再加下一件。
    private static final List<String> OUT_OF_SCOPE_KEYWORDS = Arrays.asList(
        "写代码", "代码", "编程", "程序", "脚本", "算法", "排序", "冒泡", "python", "java", "报错", "bug",
        "机票", "订票", "酒店", "天气", "气温", "股票", "基金", "翻译", "作文", "数学题", "电影", "游戏"
    );

    private static final List<String> SUBSTITUTE_KEYWORDS = Arrays.asList(
        "替代", "代替", "替换", "换成", "换掉", "用什么代", "拿什么代"
    );

    // 寒暄用**整句相等**判定，不用"包含"。
    // 为什么：数据集里有一条「你好，今天想吃点好的」——真实意图是饮食问答（点餐需求）。
    // 如果按"包含你好"判，它会被判成 greeting，把真实需求丢掉。
    // 整句相等能天然放过这种"寒暄夹带需求"，代价是「你好呀」「您好，请问」这类
    // 带尾巴的问候不再算寒暄，一律落到 other —— 这个取舍是有意的：宁可少判寒暄，不可吞掉需求。
    private static final Set<String> GREETING_ONLY = new LinkedHashSet<>(Arrays.asList(
        "你好", "您好", "哈喽", "嗨", "hi", "hello", "在吗", "早上好", "中午好", "下午好", "晚上好",
        "谢谢", "谢谢啦", "多谢", "好的", "ok", "再见", "拜拜"
    ));

    // ══════════ 输入安全拦截（2026-10-12 新增） ══════════
    // 规则**由前端 frontend/src/utils/assistantSafety.js 平移而来**，
    // 但把前端那版实测出来的 4 处误伤一起修掉了（逐条见下方注释）。
    //
    // 为什么搬到后端：
    //   ① 前端那层跑在浏览器里，curl 直接打 /assistant/chat 就绕过去了；
    //   ② pytest 读不懂 JS，那层永远测不到。放这儿才拦得住、也才测得到。
    //
    // ⚠️ 前端那份规则**暂未删除** —— 同一套判断现在写了两遍，改词表要改两处。
    //    这是有意留下的技术债：先把后端这版跑稳、测出来，再决定前端那层去留。
    private static final int MAX_PROMPT_LENGTH = 1000;

    // 脏话 / 辱骂：**只匹配明确的辱骂组合与拼音缩写**，绝不匹配单字「草」「操」
    // （草莓 / 甘草 / 体操 / 操场 会被单字规则大面积误伤）。
    //
    // ⚠️ 三处负向断言，全是**实测抓出来的误伤**，不是想当然加的：
    //    · 我草(?![一-龥])  —— 否则「我草莓过敏」被判辱骂
    //    · 我操(?![一-龥])  —— 同理（我对操场…）
    //    · "妈的" 不能光写两个字：
    //        写 `妈的`        → 「我**妈妈的**饮食建议」命中（第二个"妈"+"的"拼出来了）→ 误伤
    //        写 `妈的(?![妈])` → 上面这条挡住了，但「**我妈的**血糖高吗」照样命中 → 还是误伤
    //      最后改成**只认固定搭配 + 后面不接汉字**：他妈的 / 你妈的 / 妈的(!接汉字)。
    //      代价是「妈的智障」这种会被放过 —— 宁可漏拦一句脏话，也不要把「我妈的饮食」挡在门外。
    private static final List<Pattern> BLOCK_ABUSE_PATTERNS = Arrays.asList(
        Pattern.compile("cnm|nmsl|tmd|tnnd|woc|wc(?![a-z])|sb(?![a-z])|fuck|shit", Pattern.CASE_INSENSITIVE),
        Pattern.compile("草泥马|艹你|艹尼玛|操你|操他|他妈的|你妈的|它妈的|妈的(?![一-龥])|妈逼|傻逼|煞笔|沙雕|狗东西|去死|卧槽|我操(?![一-龥])|我艹|我草(?![一-龥])")
    );

    // 高危医疗：求具体剂量、自行停药换药、自残/极端做法。
    // ⚠️ 第一条是**修过**的。前端原版是 /(吃|服).*(几片|几粒|几袋|几支)/ ——
    //    只要求"吃"和"几片"先后出现、不限定"几片"指的是**药**，
    //    实测把「早餐吃几片全麦面包合适」「晚饭吃几粒杏仁比较合适」都判成了求用药剂量，
    //    然后回一句"请以医生的诊断和处方为准"。问份量是营养问答最常见的问法，这条必须收。
    //    改法：加**频次词**约束（一次/每次/每天…），把"食物问份量"的说法放过去，
    //    同时「一次吃几片布洛芬」这类真求剂量的照旧拦住。
    private static final List<Pattern> BLOCK_MEDICAL_PATTERNS = Arrays.asList(
        Pattern.compile("(一次|每次|每天|每日|一天|一顿|每顿)[^。！？!?]{0,8}(吃|服)[^。！？!?]{0,8}(几片|几粒|几袋|几支)"),
        Pattern.compile("(剂量|用量)是?多少|多少(毫克|mg|毫升|ml)"),
        Pattern.compile("(自行|自己|能不能|可以)[^。！？!?]{0,8}(停药|减药|换药|停掉|减半)"),
        Pattern.compile("自杀|不想活|催吐|泻药减肥|禁食[0-9一二三四五六七八九十]+天")
    );

    // 与饮食健康完全无关的领域。
    private static final List<Pattern> BLOCK_OUT_OF_SCOPE_PATTERNS = Arrays.asList(
        Pattern.compile("写(个|一段)?代码|冒泡排序|编程|python|java|sql|bug|报错", Pattern.CASE_INSENSITIVE),
        Pattern.compile("机票|订票|酒店|天气|气温|股票|基金|翻译|作文|数学题")
    );

    /**
     * 饮食词白名单：越界词**和饮食词同时出现**时，按饮食问题放过。
     *
     * 这是修"裸词误伤"的那一刀。前端把「天气」「翻译」当裸词用，于是
     * 「今天天气冷了，适合喝什么汤」「帮我翻译一下这个营养成分表」都被整套拦掉。
     * 加了这层：这两条放行，而「今天天气怎么样」「帮我翻译这段英文」照旧拦住。
     */
    private static final Pattern DIET_CONTEXT_PATTERN = Pattern.compile(
        "吃|喝|食物|食材|菜|饭|汤|营养|热量|蛋白|碳水|脂肪|糖|盐|油|减肥|减脂|增肌|食谱|餐|饮食|替代|代替|水果|蔬菜|肉|蛋|奶|豆|坚果|零食|早餐|午餐|晚餐|加餐"
    );

    private static final String BLOCK_REPLY_ABUSE =
        "请文明交流哦～我会尽力帮你解答饮食与健康相关的问题，比如食材替代、三餐搭配、热量营养估算等。";
    private static final String BLOCK_REPLY_MEDICAL =
        "用药剂量、停药换药等问题关系到人身安全，请以医生的诊断和处方为准，我无法提供这类建议。";
    private static final String BLOCK_REPLY_OUT_OF_SCOPE =
        "我只负责饮食与健康相关的问题，这个话题超出了我的能力范围，我们聊聊饮食方面的内容吧。";
    private static final String BLOCK_REPLY_TOO_LONG =
        "输入内容过长，请精简到 1000 字以内再提问。";

    /**
     * 输入安全拦截检测：命中返回规则类型，未命中返回 null。
     * 取值：abuse（辱骂）/ medical（高危医疗）/ out_of_scope（无关领域）/ too_long（超长）。
     *
     * 纯本地、不调模型 —— 同一句话问一百次结果一样，测试才敢拿它当断言。
     * 顺序就是优先级：超长 → 辱骂 → 高危医疗 → 无关领域。
     */
    private String detectBlockedType(String question) {
        if (question == null) {
            return null;
        }
        String text = question.trim();
        if (text.isEmpty()) {
            return null;
        }
        if (text.length() > MAX_PROMPT_LENGTH) {
            return "too_long";
        }
        if (matchesAnyPattern(BLOCK_ABUSE_PATTERNS, text)) {
            return "abuse";
        }
        if (matchesAnyPattern(BLOCK_MEDICAL_PATTERNS, text)) {
            return "medical";
        }
        // 越界词与饮食词**同现** → 当成饮食问题放过，不判越界（见 DIET_CONTEXT_PATTERN 注释）
        if (matchesAnyPattern(BLOCK_OUT_OF_SCOPE_PATTERNS, text)
            && !DIET_CONTEXT_PATTERN.matcher(text).find()) {
            return "out_of_scope";
        }
        return null;
    }

    private boolean matchesAnyPattern(List<Pattern> patterns, String text) {
        for (Pattern pattern : patterns) {
            if (pattern.matcher(text).find()) {
                return true;
            }
        }
        return false;
    }

    /** 按拦截类型取固定回复文案。 */
    private String blockReply(String blockedType) {
        if ("abuse".equals(blockedType)) {
            return BLOCK_REPLY_ABUSE;
        }
        if ("medical".equals(blockedType)) {
            return BLOCK_REPLY_MEDICAL;
        }
        if ("too_long".equals(blockedType)) {
            return BLOCK_REPLY_TOO_LONG;
        }
        return BLOCK_REPLY_OUT_OF_SCOPE;
    }

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
    private AssistantMessageMapper assistantMessageMapper;

    @Autowired
    private ObjectMapper objectMapper;

    @Override
    public List<Recipe> getAllRecipes() {
        return sanitizeRecipesForDisplay(recipeMapper.selectList(null));
    }

    @Override
    public Recipe getRecipeById(Long id) {
        return sanitizeRecipeForDisplay(recipeMapper.selectById(id));
    }

    @Override
    public List<RecipeIngredient> getRecipeIngredients(Long recipeId) {
        return recipeIngredientMapper.selectByRecipeId(recipeId);
    }

    @Override
    public List<Recipe> getCustomRecipes(Long userId) {
        return sanitizeRecipesForDisplay(recipeMapper.selectCustomByUserId(userId));
    }

    @Override
    public List<Recipe> searchRecipes(String keyword) {
        QueryWrapper<Recipe> wrapper = new QueryWrapper<>();
        wrapper.like("name", keyword).or().like("description", keyword);
        return sanitizeRecipesForDisplay(recipeMapper.selectList(wrapper));
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
        return sanitizeRecipeForDisplay(recipeMapper.selectById(recipe.getId()));
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
        return sanitizeRecipeForDisplay(recipeMapper.selectById(recipe.getId()));
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
            UserDietPreference preference = userDietPreferenceMapper.selectOne(
                new QueryWrapper<UserDietPreference>().eq("user_id", userId).last("LIMIT 1")
            );

            Map<String, Object> healthInfoPayload = buildHealthInfoPayload(healthInfo);
            if (preference != null) {
                if (preference.getAllergies() != null && !preference.getAllergies().trim().isEmpty()) {
                    healthInfoPayload.put("allergies", preference.getAllergies().trim());
                }
                if (preference.getDislikes() != null && !preference.getDislikes().trim().isEmpty()) {
                    healthInfoPayload.put("dislikes", preference.getDislikes().trim());
                }
            }

            Map<String, Object> requestData = new HashMap<>();
            requestData.put("userId", userId);
            requestData.put("breakfastCount", breakfastCount);
            requestData.put("lunchCount", lunchCount);
            requestData.put("dinnerCount", dinnerCount);
            requestData.put("healthInfo", healthInfoPayload);
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
                        recipes.add(sanitizeRecipeForDisplay(recipe));
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
        // 先在入口算出意图，再让它跟着**每一条**出口一起返回。
        // 之前这里没有这一行 —— 于是不管用户问的是"订机票"还是"鸡胸肉怎么替代"，
        // 调用方看到的返回值长得一模一样，分支无从观测。
        String question = extractIngredientQuestion(ingredientData);
        String intent = classifyIntent(question);

        // ③ 硬拦：命中安全规则就**不调模型**，直接回固定文案。
        //
        // 这是三层防线里唯一"确定性"的一层：
        //   ① DeepSeek 自带对齐 —— 管通用有害内容，管不了"你这个业务的职责边界"（你也不拥有它）
        //   ② system prompt 的【安全边界】4 条 —— 只是"劝"，实测越界问代码 3/4 次照写不误
        //   ③ 就在这里 —— 代码拦，绕不过去（前端那层 curl 一打就绕过）
        //
        // ⚠️ 代价要有意识：这一拦，「越界-写代码」那条重复 5 次的 pass^5 哨兵
        //    就不再是"盯模型守不守规矩"，而变成"盯这几条正则对不对"。
        //    模型行为那部分从此测不到了 —— 换来的是确定性。
        String blocked = detectBlockedType(question);
        if (blocked != null) {
            log.info("AI 助手输入被拦截: type={}, question={}", blocked, question);
            Map<String, Object> blockedResult = buildAssistantTextResult(blockReply(blocked), "blocked");
            blockedResult.put("intent", intent);
            blockedResult.put("blocked", blocked);
            return blockedResult;
        }

        Map<String, Object> deepSeekResult = getDeepSeekIngredientAssistantResult(ingredientData);
        if (deepSeekResult != null && !deepSeekResult.isEmpty()) {
            deepSeekResult.put("intent", intent);
            return deepSeekResult;
        }

        // 模型不可用时，如实报错，不再编一个答案。
        //
        // 2026-10-12 删掉了原来的两级兜底：
        //   ① Python 算法服务 localhost:5000/api/ingredient/substitute
        //   ② 本地模板 buildLocalAssistantCards + buildLocalAssistantReply
        // 这两条路只会产出"食材替代"，而助手现在的范围是泛健康 ——
        // 用户问「减脂晚餐怎么吃」，只要 DeepSeek 一挂，就会被套成「替代方案：1. 鸡蛋…」。
        // 那等于用一个错误答案去掩盖另一个错误答案，用户根本不知道服务其实坏了。
        // 宁可说"暂时不可用"，也不要说一个错的。
        log.warn("AI 助手无可用结果，返回错误提示（已不再回退到 Python 服务或本地模板）");
        Map<String, Object> errorResult = buildAssistantTextResult(
            "抱歉，AI 助手暂时无法回复。模型服务连接失败或尚未配置密钥，请稍后再试。\n"
                + "如果一直如此，请联系管理员检查 DEEPSEEK_API_KEY 配置。",
            "error");
        errorResult.put("intent", intent);
        return errorResult;
    }

    /**
     * 意图分类：greeting / out_of_scope / substitute / other。
     *
     * 纯本地关键词规则 —— 这点很重要：意图**不依赖模型**，同一句话问一百次结果都一样，
     * 测试才敢拿它当断言（模型回答是概率性的，温度 0.6 下同一句话两次不一样）。
     *
     * 分类顺序就是优先级，别随意调换：
     *   ① 整句寒暄 → ② 越界关键词 → ③ 替代关键词 → ④ 兜底 other
     * 一个问题是"越界"还是"饮食"，比它是不是"求替代"更该优先判 ——
     * 「帮我用代码写个鸡胸肉替代方案」这种，判 out_of_scope 才是对的。
     *
     * ── ④ 原名 diet_qa，2026-10-13 **改名 other** ──
     * 旧名在撒谎：前三类都不中就一律贴 diet_qa，于是「帮我写首诗」这种**越界问题**
     * 也被叫成 饮食问答 —— 它其实只是 我什么都没认出来。
     * 改成 other 之后，这个位置终于名副其实了。
     *
     * ⚠️ 但改名**不带来任何能力提升**，代价却有一条（别指望白来）：
     *    diet_qa 这个标签**从此不存在** —— 「早餐吃什么比较抗饿」这类**没有关键词的
     *    正经饮食问题**也只能落进 other。也就是说：名字变诚实了，
     *    但"系统认不认得出饮食问题"这件事一点没变好
     *    （何况 other 不驱动任何动作，见本文件上方 故意没有改分支走向，系统行为一个字没变）。
     *
     * 已知的误判（数据集里刻意留了样本，就是为了让准确率不是 100%）：
     *   · 「我还能吃点什么别的」→ 判成 other（期望 substitute）—— 一个替代词都不含，落到兜底。
     *   · 带尾巴的问候（「你好呀」「您好，请问…」）→ 判成 other，会少算一次寒暄。
     *     （取舍理由见 GREETING_ONLY 上面的注释。）
     */
    private String classifyIntent(String question) {
        String normalized = normalizeStrict(question);
        if (normalized.isEmpty()) {
            return "other";
        }
        if (GREETING_ONLY.contains(normalized)) {
            return "greeting";
        }
        for (String keyword : OUT_OF_SCOPE_KEYWORDS) {
            if (normalized.contains(keyword)) {
                return "out_of_scope";
            }
        }
        for (String keyword : SUBSTITUTE_KEYWORDS) {
            if (normalized.contains(keyword)) {
                return "substitute";
            }
        }
        // ④ 兜底：如实标 没认出来 —— 原名 diet_qa（那是谎言，见上方注释）。
        return "other";
    }

    /**
     * 把问题压成"只剩字"的形式：去掉空白和常见标点，英文转小写。
     * 为什么不能直接用 normalizeText（它只 trim + 转小写）：
     *   「你好」和「你好，」要判成同一件事 —— 后者带着标点，整句相等就匹配不上了。
     */
    private String normalizeStrict(String text) {
        if (text == null) {
            return "";
        }
        return text.replaceAll("[\\s，。！？；：、,.!?;:~…\"'“”‘’（）()\\[\\]【】\\-]+", "")
            .toLowerCase(Locale.ROOT);
    }

    private Map<String, Object> getDeepSeekIngredientAssistantResult(Map<String, Object> ingredientData) {
        if (deepSeekApiKey == null || deepSeekApiKey.trim().isEmpty()) {
            // 以前这里是静默 return null —— 日志里一个字都不留。
            // 结果是"回答全是本地模板"这个现象，只能靠人肉比对文本来判断，
            // 白白花掉很久。现在至少留一条。
            log.warn("DEEPSEEK_API_KEY 未配置或为空，AI 助手无法调用模型");
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

            // 这里原来有三行"加了又清"的废动作（第一版遗留的 JSON 数组提示词）：
            //   messages.add(...); messages.add(...); messages.clear();
            // 加完立刻 clear，等于没写；可那段"严格返回 JSON 数组"的提示词留在源码里
            // 极具误导性 —— 读到的人会以为模型现在仍被要求返回 JSON 数组。已删除。
            List<Map<String, String>> messages = new ArrayList<>();
            messages.add(buildMessage("system", buildIngredientAssistantSystemPrompt()));
            messages.add(buildMessage("system", assistantContext));
            // 注入本会话的多轮历史（最近窗口，按时间正序），让模型能理解"它/那个/再来一份"等指代
            messages.addAll(buildConversationHistoryMessages(ingredientData));
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

    /**
     * 拼装当前会话的多轮历史消息。
     *
     * 取当前用户消息之前、role 为 user/assistant 的最近 MAX_HISTORY_MESSAGES 条
     * （先按 id 倒序取窗口，再反转为时间正序），排除 context 类型和空内容消息。
     * 拿不到会话 ID 或当前消息 ID 时（如非 /assistant 入口的调用）返回空列表，
     * 不影响原有流程。
     */
    private List<Map<String, String>> buildConversationHistoryMessages(Map<String, Object> ingredientData) {
        Long conversationId = readLong(ingredientData.get("conversationId"));
        Long currentUserMessageId = readLong(ingredientData.get("currentUserMessageId"));
        if (conversationId == null || currentUserMessageId == null) {
            return new ArrayList<>();
        }

        QueryWrapper<AssistantMessage> wrapper = new QueryWrapper<>();
        wrapper.eq("conversation_id", conversationId)
            .in("role", "user", "assistant")
            .lt("id", currentUserMessageId)
            .orderByDesc("id")
            .last("LIMIT " + MAX_HISTORY_MESSAGES);

        List<AssistantMessage> recentMessages = assistantMessageMapper.selectList(wrapper);
        Collections.reverse(recentMessages);

        List<Map<String, String>> history = new ArrayList<>();
        for (AssistantMessage message : recentMessages) {
            String content = message.getContent() == null ? "" : message.getContent().trim();
            if (content.isEmpty()) {
                continue;
            }
            if (content.length() > MAX_HISTORY_CONTENT_LENGTH) {
                content = content.substring(0, MAX_HISTORY_CONTENT_LENGTH - 1) + "…";
            }
            history.add(buildMessage(message.getRole(), content));
        }
        return history;
    }

    private Long readLong(Object value) {
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

    /**
     * 通用饮食健康助手的 system prompt。
     *
     * ⚠️ 方法名还叫 Ingredient —— 这是历史遗留，别被名字骗了。
     * 它现在描述的是一个"泛健康"助手，不再是"食材替代小助手"。
     * 更名会牵动 RecipeService 接口和两个 Controller，留到命名清理那一版再做。
     *
     * 2026-10-12 放宽范围：从"只做食材替代"扩到 饮食 + 健康生活方式 + 慢病饮食。
     * 范围放宽的同时，必须把医疗边界写死在这里 ——
     * 本轮是"只改提示词"，代码层没有任何护栏，模型守不守得住边界全靠下面这段文字。
     */
    private String buildIngredientAssistantSystemPrompt() {
        return "你是一位专业的饮食与健康助手。"
            + "你可以回答：食材替代、食谱分析、三餐搭配、营养成分与热量估算、"
            + "控油控糖控钠等饮食调整、慢病相关的饮食注意事项、运动与体重管理、"
            + "以及保健品的常见作用与注意事项。"
            + "请结合用户当前健康档案、饮食目标、过敏/忌口和慢性病信息，用自然、专业、清晰的中文回答。"
            + "先给结论，再解释为什么这样建议适合该用户；需要时再分点给出具体方案。"
            + "\n\n【多轮对话规则，必须遵守】"
            + "\n1. 对话历史中用户已经说过的事实（如「我不喜欢吃鸡胸肉」「我海鲜过敏」），"
            + "直接当作既定前提，不要反问、不要质疑、也不要重新论证。"
            + "\n2. 后续追问通常很短（「鸡胸肉呢」「那它热量多少」「再来一份」），"
            + "要结合历史理解其指代，只针对追问本身简短作答，一般两三句话即可；"
            + "默认用户已经知道前几轮的结论，不要重复前文讲过的内容，也不要每轮复述完整档案。"
            + "\n3. 只有开启一个全新话题、或用户明确要求完整方案时，才给出分点的完整长回答。"
            + "\n\n【安全边界，必须遵守】"
            + "\n1. 你提供的只是饮食与生活方式参考，不做疾病诊断、不开处方、"
            + "不给具体用药剂量，也不建议用户自行调整正在服用的药物。"
            + "\n2. 遇到疾病治疗、药物相互作用、孕期哺乳期、婴幼儿、进食障碍、"
            + "严重过敏等高风险情形：先给一般性的饮食建议，"
            + "再明确提醒「具体请以医生的诊断和处方为准」。"
            + "\n3. 不推荐极端节食、催吐、禁食、滥用减肥药等有害做法；"
            + "遇到这类请求要明确拒绝，并说明风险。"
            + "\n4. 与饮食、健康完全无关的问题（写代码、查天气、订机票等），"
            + "直接说明你只负责饮食与健康相关的问题，不要勉强作答，也不要硬套成饮食建议。"
            + "\n\n不要返回 JSON，不要返回代码块，也不要用字段名模板式输出。";
    }

    private String buildIngredientAssistantNaturalUserPrompt(String question, String assistantContext) {
        // 之前这里写死了"回答食材替代问题"、"为什么这些替代方案适合该用户" ——
        // 等于每句话都先把模型按回替代任务里，泛健康的问题也会被套成替代方案。
        return "请结合以下用户信息回答。\n"
            + assistantContext + "\n"
            + "用户问题：" + question + "\n"
            + "要求：先直接回答这个问题；如果它涉及该用户的过敏/忌口、慢性病或饮食目标，"
            + "再简要说明为什么这样建议适合他。若问题超出饮食与健康范围，按安全边界说明你的职责。"
            + "如果这是结合上文的简短追问，请只回答追问本身、避免重复前文和档案。"
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
        double totalFiber = 0;

        for (RecipeIngredient recipeIngredient : ingredients) {
            Ingredient ingredient = ingredientMapper.selectById(recipeIngredient.getIngredientId());
            if (ingredient != null) {
                double quantity = safeDouble(recipeIngredient.getQuantity());
                double ratio = quantity / 100.0;

                totalCalories += safeDouble(ingredient.getCaloriesPer100g()) * ratio;
                totalProtein += safeDouble(ingredient.getProteinPer100g()) * ratio;
                totalCarbs += safeDouble(ingredient.getCarbsPer100g()) * ratio;
                totalFat += safeDouble(ingredient.getFatPer100g()) * ratio;
                totalFiber += safeDouble(ingredient.getFiberPer100g()) * ratio;
            }
        }

        recipe.setTotalCalories(roundValue(totalCalories));
        recipe.setProtein(roundValue(totalProtein));
        recipe.setCarbs(roundValue(totalCarbs));
        recipe.setFat(roundValue(totalFat));
        recipe.setFiber(roundValue(totalFiber));

        recipeMapper.updateById(recipe);
    }

    private List<Map<String, Object>> getLocalRecommendedRecipes(Long userId, String mealType, int limit) {
        List<Recipe> allRecipes = sanitizeRecipesForDisplay(recipeMapper.selectList(
            new QueryWrapper<Recipe>().orderByDesc("score").orderByDesc("collect_count").orderByDesc("view_count")
        ));
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
        payload.put("sugar", safeDouble(recipe.getSugar()));
        payload.put("sodium", safeDouble(recipe.getSodium()));
        payload.put("gi", safeDouble(recipe.getGi()));
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
            item.put("fiber", roundValue(safeDouble(ingredient.getFiberPer100g()) * ratio));
            item.put("sugar", roundValue(safeDouble(ingredient.getSugarPer100g()) * ratio));
            item.put("sodium", roundValue(safeDouble(ingredient.getSodiumPer100g()) * ratio));
            item.put("gi", ingredient.getGiValue() == null ? 0D : ingredient.getGiValue().doubleValue());
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
        List<Recipe> recipes = sanitizeRecipesForDisplay(recipeMapper.selectList(
            new QueryWrapper<Recipe>().orderByDesc("score").orderByDesc("collect_count").orderByDesc("view_count")
        ));
        List<Map<String, Object>> candidates = new ArrayList<>();
        for (Recipe recipe : recipes) {
            applyRecipeHealthMetrics(recipe);
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
            candidate.put("sugar", safeDouble(recipe.getSugar()));
            candidate.put("sodium", safeDouble(recipe.getSodium()));
            candidate.put("gi", safeDouble(recipe.getGi()));
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
        double sugar = safeDouble(recipe.getSugar());
        double sodium = safeDouble(recipe.getSodium());
        double gi = safeDouble(recipe.getGi());

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
            if (sugar > 0 && sugar <= 12) score += 3;
            if (gi > 0 && gi <= 55) score += 3;
        } else if ("lipid_control".equals(goalType)) {
            if (fat <= 16) score += 6;
            if (fiber >= 4) score += 4;
        } else if ("low_sodium".equals(goalType)) {
            if (sodium > 0 && sodium <= 350) score += 6;
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
        if (chronicDiseases.contains("糖")) {
            if (carbs <= 35) score += 3;
            if (sugar > 0 && sugar <= 12) score += 2;
            if (gi > 0 && gi <= 55) score += 2;
        }
        if (chronicDiseases.contains("高血脂") && fat <= 16) {
            score += 3;
        }
        if (chronicDiseases.contains("高血压") || chronicDiseases.contains("血压")) {
            if (isLightCooking(recipe)) score += 3;
            if (sodium > 0 && sodium <= 350) score += 3;
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
        if (safeDouble(recipe.getSugar()) > 0 && safeDouble(recipe.getSugar()) <= 12) {
            tags.add("低糖");
        }
        if (safeDouble(recipe.getGi()) > 0 && safeDouble(recipe.getGi()) <= 55) {
            tags.add("低GI");
        }
        if (safeDouble(recipe.getSodium()) > 0 && safeDouble(recipe.getSodium()) <= 350) {
            tags.add("低钠");
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
            if (diseases.contains("糖") && safeDouble(recipe.getGi()) > 0 && safeDouble(recipe.getGi()) <= 55) {
                tags.add("低GI友好");
            }
            if (diseases.contains("高血脂") && safeDouble(recipe.getFat()) <= 16) {
                tags.add("控脂友好");
            }
            if ((diseases.contains("高血压") || diseases.contains("血压")) && safeDouble(recipe.getSodium()) > 0 && safeDouble(recipe.getSodium()) <= 350) {
                tags.add("低钠友好");
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
        if (safeDouble(recipe.getSugar()) > 0 && safeDouble(recipe.getSugar()) <= 12) {
            reasons.add("含糖量相对较低，更适合控糖场景");
        }
        if (safeDouble(recipe.getGi()) > 0 && safeDouble(recipe.getGi()) <= 55) {
            reasons.add("升糖指数偏低，有助于平稳餐后血糖波动");
        }
        if (safeDouble(recipe.getSodium()) > 0 && safeDouble(recipe.getSodium()) <= 350) {
            reasons.add("钠含量控制较好，更适合低盐饮食方向");
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

    private List<Recipe> sanitizeRecipesForDisplay(List<Recipe> recipes) {
        List<Recipe> sanitized = new ArrayList<>();
        if (recipes == null) {
            return sanitized;
        }
        for (Recipe recipe : recipes) {
            Recipe item = sanitizeRecipeForDisplay(recipe);
            if (item != null) {
                sanitized.add(item);
            }
        }
        return sanitized;
    }

    private Recipe sanitizeRecipeForDisplay(Recipe recipe) {
        if (recipe == null) {
            return null;
        }
        applyRecipeHealthMetrics(recipe);
        recipe.setDescription(localizeGoalTypeInDescription(recipe.getDescription()));
        recipe.setSuitableFor(localizeGoalTypeInDescription(recipe.getSuitableFor()));
        recipe.setGoalType(localizeGoalTypeInDescription(recipe.getGoalType()));
        return recipe;
    }

    private void applyRecipeHealthMetrics(Recipe recipe) {
        if (recipe == null || recipe.getId() == null) {
            return;
        }
        Map<String, Double> metrics = calculateRecipeHealthMetrics(recipe.getId());
        recipe.setFiber(roundValue(metrics.get("fiber")));
        recipe.setSugar(roundValue(metrics.get("sugar")));
        recipe.setSodium(roundValue(metrics.get("sodium")));
        recipe.setGi(roundValue(metrics.get("gi")));
    }

    private Map<String, Double> calculateRecipeHealthMetrics(Long recipeId) {
        Map<String, Double> metrics = new HashMap<>();
        double totalFiber = 0;
        double totalSugar = 0;
        double totalSodium = 0;
        double weightedGi = 0;
        double giCarbWeight = 0;

        List<RecipeIngredient> ingredients = recipeIngredientMapper.selectByRecipeId(recipeId);
        for (RecipeIngredient recipeIngredient : ingredients) {
            Ingredient ingredient = ingredientMapper.selectById(recipeIngredient.getIngredientId());
            if (ingredient == null) {
                continue;
            }

            double quantity = safeDouble(recipeIngredient.getQuantity());
            double ratio = quantity / 100.0;
            totalFiber += safeDouble(ingredient.getFiberPer100g()) * ratio;
            totalSugar += safeDouble(ingredient.getSugarPer100g()) * ratio;
            totalSodium += safeDouble(ingredient.getSodiumPer100g()) * ratio;
            double carbs = safeDouble(ingredient.getCarbsPer100g()) * ratio;
            if (ingredient.getGiValue() != null && ingredient.getGiValue() > 0 && carbs > 0) {
                weightedGi += ingredient.getGiValue() * carbs;
                giCarbWeight += carbs;
            }
        }

        metrics.put("fiber", totalFiber);
        metrics.put("sugar", totalSugar);
        metrics.put("sodium", totalSodium);
        metrics.put("gi", giCarbWeight > 0 ? weightedGi / giCarbWeight : 0D);
        return metrics;
    }

    private String localizeGoalTypeInDescription(String text) {
        if (text == null || text.trim().isEmpty()) {
            return text;
        }
        String localized = text;
        localized = localized.replace("fat_loss", "减肥减脂");
        localized = localized.replace("muscle_toning", "增肌塑形");
        localized = localized.replace("weight_maintenance", "维持体重");
        localized = localized.replace("healthy_weight_gain", "健康增重");
        localized = localized.replace("blood_sugar_control", "控糖饮食");
        localized = localized.replace("lipid_control", "控脂降脂");
        localized = localized.replace("low_sodium", "控压低盐");
        localized = localized.replace("pregnancy_nutrition", "孕妇营养");
        localized = localized.replace("child_growth", "儿童成长");
        localized = localized.replace("senior_wellness", "老年养生");
        return localized;
    }

    private double roundValue(Double value) {
        double number = value == null ? 0D : value;
        return Math.round(number * 10D) / 10D;
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
