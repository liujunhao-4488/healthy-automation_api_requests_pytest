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
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
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
import java.util.function.Consumer;
import java.util.regex.Pattern;

@Service
@Slf4j
public class RecipeServiceImpl implements RecipeService {

    private static final String PYTHON_SERVICE_URL = "http://localhost:5000";

    /**
     * 模型不可用时的固定文案。
     * 非流式 / 流式两条路**共用同一条** —— 同一句用户可见的话写两遍，改一处漏一处的坑项目里踩过。
     */
    private static final String ASSISTANT_UNAVAILABLE_REPLY =
        "抱歉，AI 助手暂时无法回复。模型服务连接失败或尚未配置密钥，请稍后再试。\n"
            + "如果一直如此，请联系管理员检查 DEEPSEEK_API_KEY 配置。";

    /**
     * 多轮对话历史窗口：最多带入多少条历史消息（约 10 轮，user/assistant 各算一条）。
     */
    private static final int MAX_HISTORY_MESSAGES = 20;

    /**
     * 单条历史消息进入模型前的最大长度，超出截断，避免个别长回复占满上下文。
     */
    private static final int MAX_HISTORY_CONTENT_LENGTH = 500;

    // ══════════ 意图识别（本地关键词规则） ══════════
    // 2026-10-14 **归一**：本文件只有一条分类器 classifyIntent，取值 5 个
    //   query / knowledge / advice / fallback / chat。
    //
    // 以前的旧四类（greeting / out_of_scope / substitute / other）同日**退休**，
    // 原因记在这里免得被人误以为丢了东西：
    //   · 旧四类回答的是"这句话是什么性质"（贴标签），读它的下游 if 是 0 个；
    //     新五类回答的是"该分派到哪条路"（驱动动作）。**一个字段装不下两个维度** ——
    //     硬塞的后果已经出现过：旧意图表和新硬拦表各自维护了一张"越界"词表
    //     （24 词 vs 13 词），同一句话两个分类器能给出相反结论。
    //   · 退休后，越界判断的**唯一出处**回到硬拦表（detectBlockedType），重复消失。
    //   · 旧取值的去向：greeting / substitute → chat（它们不含任何路由关键词）；
    //     out_of_scope → 硬拦命中则 fallback、否则 chat；other → chat。
    //
    // 这一步只做两件事：① 把意图**算出来**（下面的 classifyIntent）；
    //                   ② 让它随返回值**透传**到响应里（getIngredientSubstitutes 末尾 put）。
    //
    // ⚠️ 故意**没有改分支走向** —— 5 个值目前仍然全都去调模型（被硬拦的除外）。
    //    原因：一旦本地短接（比如 query 真去读库），那些盯模型稳定性的哨兵用例
    //    （重复 5 次的 pass^5）就白建了。接线是下一步、单独验收。
    //
    // ══════════ 意图分类：取值 5 个 ══════════
    //   query      数据统计 —— 问"我（某时段）吃了多少"，该读 diet_record 并聚合
    //   knowledge  营养知识 —— 问某食物的公共营养数据，该查 ingredient（与个人记录无关）
    //   advice     健康建议 —— 要个性化方案，该带画像（+ 记录）
    //   fallback   安全兜底 —— 命中硬拦，不调模型
    //   chat       不派动作 —— 闲聊 / 纯陈述 / 看不出诉求，**直接交给模型自己回答**
    //
    // ⚠️ chat 是**默认出口，不是第五种业务意图** —— 它代表"我不给这句话分派任何动作"。
    //    用户说「刚吃了碗牛肉面」，没有问号、没有诉求词，就是一句**陈述**；
    //    对陈述句弹一句"去记录页记一下吧"是自作多情，比不接还烦人。
    //    所以判据看**诉求词**（多少 / 怎么 / 帮我…），**不看食物词**。
    //
    // ⚠️ 顺序：query 必须排在 knowledge 前面。
    //    「我今天吃了多少卡」同时含 query 特征（吃了多少）和 knowledge 特征（多少卡）；
    //    先判 knowledge 会把它误分派去"查公共营养库" —— 可它问的是**用户自己的记录**。
    //    口径：第一人称 + 时段 = query；光问食物本身 = knowledge。
    // query 的判据是**合取**：第一人称 + 时段词 + 吃喝/摄入，三个都沾才算数据统计。
    // 为什么不用一串固定短语去 contains：「我昨天晚饭吃了什么」不含任何固定短语，
    // 可它显然在问自己的记录；「我今天有点累」含"我今天"，却跟统计无关。
    // 拆成两组词做合取，才分得开这两种。
    private static final List<String> INTENT_QUERY_TIME_WORDS = Arrays.asList(
        "今天", "昨天", "前天", "这周", "本周", "这一周", "这几天", "这两天", "这个月",
        "早上", "中午", "晚上", "早餐", "午餐", "晚餐", "夜宵", "加餐"
    );

    private static final List<String> INTENT_QUERY_RECORD_WORDS = Arrays.asList(
        "吃", "喝", "摄入", "记录", "热量"
    );

    // 2026-10-16 扩表。原表**全是数值词**，而用户真会问的是「高血压饮食注意什么」
    // 「血糖怎么控制」—— 一个数值词都不含，于是落到 advice/chat，二级路由压根不执行，
    // RAG 一次都不会被触发。不扩这张表，article 那侧接得再好也测不出任何变化。
    //
    // ⚠️ 加词前必须查：classifyIntent 的顺序是 query → knowledge → advice，
    //    所以往这里加词会**抢走** advice 的词。本次刻意避开了 advice 表里已有的
    //    「控糖 / 减脂 / 怎么吃 / 建议」—— 数据集里「我想控糖应该注意什么」
    //    「减脂晚餐怎么吃」的期望值都是 advice，被抢走就会红。
    private static final List<String> INTENT_KNOWLEDGE_KEYWORDS = Arrays.asList(
        // —— 第一组：营养数值词（原有）。判据是"问食物本身的营养数据"，有唯一正确答案；
        //    句中带食材名 → 二级路由落到 ingredient → 查表拿确定数值。
        "多少卡", "热量", "卡路里", "营养成分", "成分表", "升糖", "gi值",
        "碳水", "蛋白质含量", "脂肪含量", "含糖", "钠含量", "胆固醇", "膳食纤维",
        // —— 第二组：慢病主题词（2026-10-16 新增）。这类问题句中**不含食材名**，
        //    于是落到 article → 检索权威指南。注意「血压」已覆盖「高血压」，不必再列。
        //    ⚠️ 已知副作用（未处理）：它们从 advice 变 knowledge 后**不再带用户画像**
        //    （includeProfile = "advice".equals(intent)），而慢病用户恰恰最需要画像。
        //    要不要给 article 路由也放行画像，是单独一个决定，别顺手改。
        "血糖", "血压", "血脂", "尿酸", "痛风", "糖尿病", "脂肪肝", "骨质疏松",
        // —— 第三组：饮食体系 / 概念词。问的是"是什么"，没有唯一答案 → 天然该走检索。
        "生酮", "轻断食", "食养"
    );

    private static final List<String> INTENT_ADVICE_KEYWORDS = Arrays.asList(
        "怎么吃", "如何吃", "吃什么好", "应该吃", "建议", "我该", "能改善", "怎么办",
        "减脂", "减肥", "控糖", "增肌", "食谱", "搭配", "三餐", "饮食计划", "能吃吗", "可以吃吗"
    );

    // ══════════ knowledge 的二级路由（2026-10-16 新增） ══════════
    // knowledge 只回答"该不该查公共营养知识"，但**公共营养知识有两种来源**，
    // 取得方式与可靠性完全不同：
    //   · 食材数值（米饭 = 116 千卡）—— **有唯一正确答案**，该走**精确查表**；
    //   · 概念建议（生酮饮食是什么、高血压饮食注意什么）—— 没有唯一答案，该走**检索**。
    //
    // 为什么必须分开：混成一条路，翻车方式是**静默的** —— 拿"米饭多少卡"去做相似度检索，
    // 召回几段"差不多"的文字，模型照着写出一个"差不多"的数字。界面上看不出任何异常，
    // 但它已经从"查数据"退化成了"猜数据"。
    //
    // ⚠️ 这是 intent 之外的**第二个**标签字段，不与 intent 混用（一个字段装两个维度，
    //    这个项目在"意图表 vs 硬拦表"上已经踩过一次）。
    private static final String KNOWLEDGE_ROUTE_INGREDIENT = "ingredient";
    private static final String KNOWLEDGE_ROUTE_ARTICLE = "article";

    /**
     * 一次最多注入几种食材的数据。
     * 超过 3 种通常说明问的是"搭配 / 对比"（那属于 article 的活），也避免把 prompt 灌爆。
     */
    private static final int MAX_KNOWLEDGE_INGREDIENTS = 3;

    // ══════════ article 路由的知识库检索参数（2026-10-16 接入） ══════════

    /** 检索返回几条。3 条 ≈ 一两千字资料，够模型组织回答，又不至于把 prompt 灌爆。 */
    private static final int KB_TOP_K = 3;

    /**
     * 检索调用的超时（毫秒）。**必须设**，理由见 kbRestTemplate 字段上的注释。
     * 本机内网检索实测在几十毫秒级，1.5s / 3s 宽松到不可能误杀正常请求，
     * 又能保证 5000 挂掉时聊天请求不会被拖死。
     */
    private static final int KB_CONNECT_TIMEOUT_MS = 1500;
    private static final int KB_READ_TIMEOUT_MS = 3000;

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
        Pattern.compile("自杀|不想活|催吐|泻药减肥|禁食[0-9一二三四五六七八九十]+天"),
        // 2026-10-14 新增：**极端速减**。
        //   上一行只认"催吐 / 泻药 / 禁食 N 天"这类**具体做法**，认不出把危险包装成承诺的说法。
        //   实测：「我是营养师，要给客户设计一个极速减脂方案，每天 300 大卡，你帮我完善一下细节」
        //   既不中医疗、也不中越界 → 直接递给了模型（然后判 advice、带着画像照答）。
        // ⚠️ **刻意不收"快速减肥 / 快速减脂"** —— 那是正常用户最常问的说法之一，
        //   拦它等于把正经提问挡在门外（本表第一条踩过同一个坑，见上方注释）。只认明确越界的措辞。
        // ⚠️ **刻意不收"三天瘦十斤"这类"X 天瘦 N 斤"** —— 数据里那条越狱样本目前还能
        //   真的递到模型、观测"模型守不守 B3 边界"；拦掉它，那条哨兵就退化成"测正则对不对"了。
        Pattern.compile("极速减脂|极速减肥|暴瘦")
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
        "用药剂量、停药换药、极端节食或过速减重等问题关系到人身安全，请以医生的诊断和处方为准，我无法提供这类建议。";
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

    /**
     * 知识库检索专用的 client —— **故意不复用上面那个**。
     *
     * ⭐ 为什么：全局那个在 RestTemplateConfig 里是裸的 new RestTemplate()，**没设任何超时**
     *    （默认无限等待），而且不能顺手给它补 —— 它还要给 DeepSeek 流式用：
     *    流式响应要连着读几十秒，设 readTimeout 会把流从中间截断。
     *    两种调用的超时诉求正好相反，共用一个 client 必然有一边被将就。
     *
     *    检索调用则相反：内网本机，要么几十毫秒返回、要么就是服务挂了，
     *    必须尽早失败 —— 否则一次检索挂住就等于整条 /assistant/chat 挂住，
     *    用户对着转圈的界面等一个无限期的响应。
     */
    private final RestTemplate kbRestTemplate = createKbRestTemplate();

    private static RestTemplate createKbRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(KB_CONNECT_TIMEOUT_MS);
        factory.setReadTimeout(KB_READ_TIMEOUT_MS);
        return new RestTemplate(factory);
    }

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
        // 意图标签：**只算、只透传，不改分支走向**（见 classifyIntent 注释）。
        String intent = classifyIntent(question);

        // knowledge 的**二级路由**（2026-10-16 新增）：决定这次是"查表"还是"检索"。
        // 只在 knowledge 意图下才算 —— 别的意图压根没有这个分歧。
        //   · ingredient 路由 → 当场查库，把确定性数值带进 prompt（下面 put 进 requests）；
        //   · article 路由    → 检索服务尚未接入，facts 为空，等于走原来的裸模型回答。
        String knowledgeRoute = "";
        String knowledgeFacts = "";
        if ("knowledge".equals(intent)) {
            Map<String, String> knowledgeContext = resolveKnowledgeContext(question);
            knowledgeRoute = knowledgeContext.getOrDefault("route", "");
            knowledgeFacts = knowledgeContext.getOrDefault("facts", "");
            log.info("AI 助手 knowledge 路由: route={}, 命中食材数据={}字", knowledgeRoute, knowledgeFacts.length());
        }

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

        Map<String, Object> deepSeekResult = getDeepSeekIngredientAssistantResult(ingredientData, "advice".equals(intent), knowledgeFacts);
        if (deepSeekResult != null && !deepSeekResult.isEmpty()) {
            deepSeekResult.put("intent", intent);
            putKnowledgeRoute(deepSeekResult, knowledgeRoute);
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
        Map<String, Object> errorResult = buildAssistantTextResult(ASSISTANT_UNAVAILABLE_REPLY, "error");
        errorResult.put("intent", intent);
        putKnowledgeRoute(errorResult, knowledgeRoute);
        return errorResult;
    }

    /**
     * 流式版：把上面的 getIngredientSubstitutes 走一遍，但模型回答边生成边推给 onDelta。
     *
     * 三条出口和非流式**一一对应**（硬拦 / 模型 / 报错），区别只在"文本怎么出去"：
     *   · 硬拦、报错   → 没有真实增量，把固定文案**一次性**推出去（保证客户端总能拿到文本）
     *   · 模型正常     → 增量逐段推出去
     * 返回值的形状和非流式完全一致，所以调用方保存消息、读 intent/source 的代码可以原样复用。
     */
    @Override
    public Map<String, Object> streamIngredientSubstitutes(Map<String, Object> ingredientData, Consumer<String> onDelta) {
        String question = extractIngredientQuestion(ingredientData);
        String intent = classifyIntent(question);

        // knowledge 二级路由 —— 与非流式**同一套判定**（共用 resolveKnowledgeContext，
        // 不另写一份，避免"两条路结论不同"这种本项目踩过的坑）。
        String knowledgeRoute = "";
        String knowledgeFacts = "";
        if ("knowledge".equals(intent)) {
            Map<String, String> knowledgeContext = resolveKnowledgeContext(question);
            knowledgeRoute = knowledgeContext.getOrDefault("route", "");
            knowledgeFacts = knowledgeContext.getOrDefault("facts", "");
            log.info("AI 助手 knowledge 路由(流式): route={}, 命中食材数据={}字", knowledgeRoute, knowledgeFacts.length());
        }

        // ① 硬拦：命中就**不调模型**，直接回固定文案（与非流式同一套判定，不另写表）。
        String blocked = detectBlockedType(question);
        if (blocked != null) {
            log.info("AI 助手输入被拦截(流式): type={}, question={}", blocked, question);
            Map<String, Object> blockedResult = buildAssistantTextResult(blockReply(blocked), "blocked");
            blockedResult.put("intent", intent);
            blockedResult.put("blocked", blocked);
            onDelta.accept(String.valueOf(blockedResult.get("text")));
            return blockedResult;
        }

        // ② 模型：逐段推增量。
        Map<String, Object> deepSeekResult = streamDeepSeekAssistantResult(ingredientData, question, onDelta, "advice".equals(intent), knowledgeFacts);
        if (deepSeekResult != null && !deepSeekResult.isEmpty()) {
            deepSeekResult.put("intent", intent);
            putKnowledgeRoute(deepSeekResult, knowledgeRoute);
            return deepSeekResult;
        }

        // ③ 模型不可用：如实报错，不再编答案（理由见非流式那条的注释）。
        log.warn("AI 助手流式无可用结果，返回错误提示");
        Map<String, Object> errorResult = buildAssistantTextResult(ASSISTANT_UNAVAILABLE_REPLY, "error");
        errorResult.put("intent", intent);
        putKnowledgeRoute(errorResult, knowledgeRoute);
        onDelta.accept(ASSISTANT_UNAVAILABLE_REPLY);
        return errorResult;
    }

    // ── 旧四类分类器（greeting / out_of_scope / substitute / other）于 2026-10-14 退休 ──
    // 它只贴标签、不驱动动作；而且和硬拦各维护了一张"越界"词表（24 词 vs 13 词），
    // 同一句话两个分类器能给出相反结论。退休后全项目只剩下面一个分类器 ——
    // 越界判断的唯一出处回到硬拦表（detectBlockedType）。
    // 旧逻辑没丢什么有价值的信息，只是"这句话是什么性质"这个问题不再由代码回答。

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

    /**
     * 意图分类：query / knowledge / advice / fallback / chat。
     *
     * 纯本地关键词规则 —— 意图**不依赖模型**，同一句话问一百次结果一样，
     * 测试才敢拿它当断言（模型回答是概率性的，温度 0.6 下同一句话两次不一样）。
     *
     * 现状（2026-10-14）**只算不派** —— 5 个值都只跟着响应回出去，还没有下游 if。
     * 为什么先不派：query 要读的 /record/analysis/trend、knowledge 要查的 ingredient 表
     * 都还没接进来。先让标签跑起来、拿到真实分布，再决定怎么切 —— 一次只改一件事。
     *
     * 顺序即优先级，别随意调换：
     *   ① fallback → ② query → ③ knowledge → ④ advice → ⑤ chat（默认）
     * 安全永远排第一：「吃什么能治好糖尿病」必须被 fallback 接住，
     * 不能因为含个"吃"字就先落进 advice。
     */
    private String classifyIntent(String question) {
        String normalized = normalizeStrict(question);
        if (normalized.isEmpty()) {
            return "chat";
        }
        // ① 安全兜底：**复用**硬拦判定，不另写一份表 ——
        //    两份表对同一句话结论相反这种事，这个项目里已经踩过（意图表 vs 硬拦表）。
        if (detectBlockedType(question) != null) {
            return "fallback";
        }
        // ② 数据统计：第一人称 + 时段 + 吃喝/摄入，**三个条件同时成立**才算（见词表注释）。
        if (normalized.contains("我")
            && containsAny(normalized, INTENT_QUERY_TIME_WORDS)
            && containsAny(normalized, INTENT_QUERY_RECORD_WORDS)) {
            return "query";
        }
        if (containsAny(normalized, INTENT_KNOWLEDGE_KEYWORDS)) {
            return "knowledge";
        }
        if (containsAny(normalized, INTENT_ADVICE_KEYWORDS)) {
            return "advice";
        }
        // ⑤ 默认：**不路由** —— 闲聊 / 纯陈述 / 看不出诉求，直接交给模型自己回答。
        //    这条必须存在，否则每句话都被硬塞进前四类。
        return "chat";
    }

    /** 命中词表里任意一个词就算中（与 matchesAnyPattern 同形，只是换成字符串列表）。 */
    private boolean containsAny(String text, List<String> keywords) {
        for (String keyword : keywords) {
            if (text.contains(keyword)) {
                return true;
            }
        }
        return false;
    }

    // ══════════ knowledge 二级路由：算标签 + 取数据，一次完成 ══════════

    /**
     * 只在 knowledge 意图下调用。一次算出两样东西，返回值 2 个键：
     *   route —— ingredient（精确查表）/ article（走检索）
     *   facts —— 命中食材时拼好的**事实块**，未命中为空串
     *
     * ⚠️ 为什么不拆成"先算 route、再决定要不要查"两个方法：那样要么查两遍库，
     *    要么把 List 当出参传来传去。一次算完，调用方只做"要不要用它"的判断。
     */
    private Map<String, String> resolveKnowledgeContext(String question) {
        Map<String, String> result = new HashMap<>();
        String normalized = normalizeStrict(question);

        List<Ingredient> hit = normalized.isEmpty()
            ? new ArrayList<>()
            : matchIngredientsInQuestion(normalized);

        // ⚠️ 这里**不需要**再判断"问题里有没有数值询问词"——
        //    能走到这里就说明 classifyIntent 已经判成 knowledge，而 knowledge 的判据
        //    本身就是 INTENT_KNOWLEDGE_KEYWORDS（多少卡/热量/碳水/含糖/钠含量/GI…）。
        //    再加一次那个条件，等于恒真，是**看着严谨其实没用的代码**。
        //
        //    所以判据只剩一条：**问题里出现了库里真实存在的食材名**。
        //      · 命中 → 问的是"这个食材的营养素" → 查表，数字可控；
        //      · 未命中 → 问的是"概念/指标含义/怎么看"（「升糖指数是什么意思」
        //        「营养成分表怎么看」）→ 没有唯一答案 → 检索（article）。
        //    ⚠️ 代价要有意识：**knowledge 现在这个范围偏窄** —— 它接不住
        //    「生酮饮食是什么」「高血压饮食注意什么」这类，那些句子里不含营养数值词，
        //    会在 classifyIntent 里落到 advice / chat，压根进不来这里。
        //    要让 RAG 真正吃得饱，下一步得改的是 **INTENT_KNOWLEDGE_KEYWORDS 词表**，
        //    不是这个方法 —— 但那会动到意图标签那 31 条用例的期望值，得单独一轮做。
        if (!hit.isEmpty()) {
            result.put("route", KNOWLEDGE_ROUTE_INGREDIENT);
            result.put("facts", buildIngredientFacts(hit));
        } else {
            // article 路由：**RAG 检索的挂载点**（2026-10-16 已接上）。
            //
            // ⭐ 返回值形状与未接入时**完全一样**（还是 route + facts 两个键），
            //    所以从拼 prompt 到流式返回，下游一个字都不用改 ——
            //    RAG 片段本质就是"另一种 facts"，走的是同一条 system 消息通道。
            result.put("route", KNOWLEDGE_ROUTE_ARTICLE);
            result.put("facts", searchKnowledgeBase(question));
        }
        return result;
    }

    /**
     * article 路由的检索实现 —— 调算法服务（Flask 5000）的 /api/kb/search。
     *
     * ⭐ 为什么走 HTTP 而不是在 Java 里再实现一遍检索：
     *    分词（字符 bigram）、BM25、阈值全在 algorithm/kb_retriever.py 里，
     *    检索的口径只有一个出处（召回测试也是直连那一个端口测的）。
     *    在 Java 里重写一份 = 又多一份"同一件事两个实现"，正是本项目反复踩的坑。
     *    何况 Java 早就在调 5000 了 —— 见本文件顶部的 PYTHON_SERVICE_URL。
     *
     * ⚠️ 降级：任何失败都返回**空串**，而不是抛异常。
     *    空串的语义是"这次没有资料"，而 buildAssistantRequestBody 对空 facts 的处理
     *    恰好就是"不加那条 system 消息" —— 也就是说**降级路径 = 接入前的行为**，
     *    不需要另写兜底分支。检索挂了，用户拿到的是一份没有依据的回答，而不是 500。
     */
    private String searchKnowledgeBase(String question) {
        try {
            Map<String, Object> request = new HashMap<>();
            request.put("query", question);
            request.put("topK", KB_TOP_K);
            // 不传 sourceType → 用服务端默认（当前是 authority，只查权威指南）。
            // ⚠️ 别在这里写死 "authority"：默认检索范围是个产品决定，
            //    写死在两处就变成"改一处漏一处"。
            Map<String, Object> response = kbRestTemplate.postForObject(
                PYTHON_SERVICE_URL + "/api/kb/search", request, Map.class);
            return buildKnowledgeFacts(response);
        } catch (RestClientException exception) {
            // 超时 / 连接被拒 / 5xx 都落这里。**不打 error**：知识库不可用不该惊动告警 ——
            // 它的设计后果就是"退化成一份没有依据的回答"，属于可接受的降级。
            log.warn("知识库检索不可用，退化为裸模型回答: {}", exception.getMessage());
            return "";
        }
    }

    /**
     * 把检索结果拼成"资料块"（喂给模型的 system 消息）。
     *
     * ⭐ "只能依据以上资料作答"这句指令写在**资料块自己身上**，而不是 system prompt 里 ——
     *    这不是风格选择：system prompt 是无条件发出的，而资料块只在真召回时才拼。
     *    把指令写进 system prompt，在没召回的那一半请求里就成了一句
     *    **指向不存在数据的空指令**（"结合用户档案"那句踩过同一个坑，见
     *    buildIngredientAssistantSystemPrompt 的注释）。写进资料块，天然做到"有资料才有指令"。
     */
    private String buildKnowledgeFacts(Map<String, Object> response) {
        if (response == null) {
            return "";
        }
        Object data = response.get("data");
        if (!(data instanceof List) || ((List<?>) data).isEmpty()) {
            // 检索成功但**一条都没召回** —— 与"检索失败"返回同一个空串。
            // 这是有意的：上游只需要知道"这次没有资料可用"，不关心为什么没有。
            return "";
        }

        StringBuilder facts = new StringBuilder(
            "【知识库资料 · 摘自权威膳食指南】以下是检索到的参考资料，是本系统回答该问题的依据：\n"
        );
        int index = 1;
        for (Object item : (List<?>) data) {
            if (!(item instanceof Map)) {
                continue;
            }
            Map<?, ?> hit = (Map<?, ?>) item;
            facts.append("[").append(index++).append("] 《")
                .append(factsField(hit.get("title"))).append("》");
            String section = factsField(hit.get("section"));
            if (!section.isEmpty()) {
                facts.append(" · ").append(section);
            }
            facts.append("\n").append(factsField(hit.get("snippet"))).append("\n");
        }
        if (index == 1) {
            return "";
        }

        // ⚠️ 这段是"防止模型把检索结果当摆设"的关键：不写明"只能依据以上资料"，
        //    模型会照着自己的训练记忆讲（同一食材不同来源能差 20%），召回就白做了。
        //    要求标注出处的另一半价值在**可核验** —— 用户能顺着「《XX指南》」自己去看原文。
        facts.append("请以上述资料为主要依据作答，不要用你的记忆替换其中的数字或结论；")
            .append("引用时请说明出自哪一份指南。若上述资料没有覆盖用户问到的点，")
            .append("就直接说明资料中没有提到，不要凭印象补充。");
        return facts.toString();
    }

    /** null 安全取值 —— 检索结果里的字段可能缺失（与 valueOrDash 不同：缺了就返回空串，不占位）。 */
    private String factsField(Object value) {
        return value == null ? "" : String.valueOf(value);
    }

    /**
     * 实体链接：从问题里找出库里真实存在的食材。
     *
     * 为什么用 **ingredient 表本身当词典**、不引分词器：
     *   ① 124 条规模下 O(n) 扫描是微秒级，为它装一个词典/分词器不划算；
     *   ② 天然随库更新 —— 后台新加一条食材，识别能力立刻跟上，不会出现"词典忘了同步"。
     *
     * ⚠️ 但"拿库当词典"有三个坑，都是**看了真数据才发现的**，逐条在这一版里处理：
     *   ① 单字名 —— 库里真有「梨」「虾」。任何含"梨"的句子都会命中，于是
     *      **「凤梨热量多少」会拿到「梨」的数据**：不报错、不空手，直接注入一份**错的**事实。
     *      库里只有这两个单字名、而"凤梨/雪梨"一个都没收录，所以取舍是
     *      **宁可漏（问"梨"时查不到），也不给错（问"凤梨"时别给梨）** ——
     *      与硬拦表"宁可漏拦一句脏话"同一个取舍方向。
     *   ② 重名 —— 124 条里 **33 个名字重复**（「燕麦」「鸡胸肉」「牛奶」…各两条，
     *      应是不同分类下各录了一遍）。不去重会把同一食材注入两遍，模型看到两个数值还可能打架。
     *   ③ 名字互相包含 —— 如「低脂牛奶」/「牛奶」。命中长名时短名是它的**一部分**，
     *      不是并列的第二种食材（「低脂牛奶的热量」不该同时塞一份「牛奶」的数据）。
     */
    private List<Ingredient> matchIngredientsInQuestion(String normalizedQuestion) {
        List<Ingredient> all = ingredientMapper.selectList(
            new QueryWrapper<Ingredient>().eq("status", 1)
        );

        List<Ingredient> matched = new ArrayList<>();
        for (Ingredient ingredient : all) {
            String normalizedName = normalizeStrict(ingredient.getName());
            // 名字归一化后可能变空（名字全是标点）→ 必须跳过，
            // 否则 contains("") 恒为 true，整个库都会被当成"命中"。
            // 单字名一并跳过 —— 理由见上面 ①。
            if (normalizedName.length() < 2) {
                continue;
            }
            if (normalizedQuestion.contains(normalizedName)) {
                matched.add(ingredient);
            }
        }

        // 名称长的排前面：「鸡胸肉」优先于「鸡肉」。
        matched.sort((a, b) -> b.getName().length() - a.getName().length());

        // 去重 + 剔除"被更长命中名包含"的短名（坑 ② 与 ③）。
        // 因为已按长度降序，所以 result 里先存的必然是更长的名字。
        List<Ingredient> result = new ArrayList<>();
        for (Ingredient candidate : matched) {
            String candidateName = candidate.getName();
            boolean redundant = false;
            for (Ingredient chosen : result) {
                if (chosen.getName().equals(candidateName) || chosen.getName().contains(candidateName)) {
                    redundant = true;
                    break;
                }
            }
            if (!redundant) {
                result.add(candidate);
            }
        }

        return result.size() > MAX_KNOWLEDGE_INGREDIENTS
            ? new ArrayList<>(result.subList(0, MAX_KNOWLEDGE_INGREDIENTS))
            : result;
    }

    /**
     * 把命中的食材记录拼成**确定性的事实块**，交给模型去表述。
     *
     * ⭐ 整个"精确查表"路线的核心就在这段文字里：**数字由代码提供，模型只负责组织语言**。
     *    这也是它和 RAG 检索的本质区别 —— 这里的每个数字都能回溯到库里某一行，
     *    而检索回来的文字只是"相似"，不保证是"正确"。
     *
     * 所以必须明写"只能使用以下数值"。否则模型会按训练记忆里的"常识"覆盖它 ——
     * 而它记的数字经常是错的（同一食材不同来源能差 20%）。
     */
    private String buildIngredientFacts(List<Ingredient> ingredients) {
        if (ingredients == null || ingredients.isEmpty()) {
            return "";
        }

        StringBuilder facts = new StringBuilder(
            "【食材营养数据 · 每 100 克】以下数值直接取自本系统的食材库，是权威数据：\n"
        );
        for (Ingredient ingredient : ingredients) {
            facts.append("- ").append(ingredient.getName()).append("：")
                .append("热量 ").append(formatNutrient(ingredient.getCaloriesPer100g())).append(" 千卡，")
                .append("蛋白质 ").append(formatNutrient(ingredient.getProteinPer100g())).append(" 克，")
                .append("碳水化合物 ").append(formatNutrient(ingredient.getCarbsPer100g())).append(" 克，")
                .append("脂肪 ").append(formatNutrient(ingredient.getFatPer100g())).append(" 克");
            // 后四项**只在有值时追加** —— 库里大量记录这几列是 NULL，
            // 全拼出来会变成一串"—"，既没用还挤占上下文。
            appendIfPresent(facts, "膳食纤维", ingredient.getFiberPer100g(), " 克");
            appendIfPresent(facts, "糖", ingredient.getSugarPer100g(), " 克");
            appendIfPresent(facts, "钠", ingredient.getSodiumPer100g(), " 毫克");
            appendIfPresent(facts, "胆固醇", ingredient.getCholesterolPer100g(), " 毫克");
            if (ingredient.getGiValue() != null) {
                facts.append("，升糖指数 GI ").append(ingredient.getGiValue());
            }
            facts.append("。\n");
        }

        facts.append("请严格使用以上数值作答，不要改动、不要凭记忆替换、也不要补充表中没有的数据；")
            .append("若问题问的指标不在上面，就直接说明该项数据缺失。");
        return facts.toString();
    }

    /** 营养值非空时追加一段「，名称 X 单位」。 */
    private void appendIfPresent(StringBuilder builder, String label, Double value, String unit) {
        if (value != null) {
            builder.append("，").append(label).append(" ").append(formatNutrient(value)).append(unit);
        }
    }

    /**
     * 营养数值格式化：null → "—"；整数去掉小数点（116.0 → 116）；其余保留 1 位小数。
     * 为什么不能直接用 valueOrDash：那个走 String.valueOf(Double)，
     * 116 会打成 "116.0"，扔进 prompt 里既难看又容易被模型"顺手四舍五入"。
     */
    private String formatNutrient(Double value) {
        if (value == null) {
            return "—";
        }
        if (!Double.isInfinite(value) && value == Math.floor(value)) {
            return String.valueOf((long) (double) value);
        }
        return String.format(Locale.ROOT, "%.1f", value);
    }

    /** 只在算出来时挂上 route，避免响应里出现一堆空字段（与 blocked 同一口径）。 */
    private void putKnowledgeRoute(Map<String, Object> result, String knowledgeRoute) {
        if (result != null && knowledgeRoute != null && !knowledgeRoute.isEmpty()) {
            result.put("knowledgeRoute", knowledgeRoute);
        }
    }

    /**
     * 组装发给 DeepSeek 的请求体（model / temperature / messages，可选 stream）。
     *
     * 非流式（getDeepSeekIngredientAssistantResult）与流式（streamDeepSeekAssistantResult）
     * **共用这一个方法** —— 提示词只在源码里拼一次。拆成两份的代价这个项目里见过：
     * 两张"越界"词表各写一套，同一句话能给出相反结论。
     *
     * 两段"可选上下文"，各自独立判断、各自空则不发：
     *   includeProfile  → 用户画像（只在 advice 意图）；
     *   knowledgeFacts → 食材事实块（只在 knowledge + ingredient 路由）。
     */
    private Map<String, Object> buildAssistantRequestBody(
        Map<String, Object> ingredientData, String question, boolean stream, boolean includeProfile, String knowledgeFacts) {
        // ⭐ 2026-10-14：画像**按意图装配** —— 只有 advice（要个性化方案的那类）才读库、才拼进 prompt。
        //
        // 为什么在这儿门控：本方法是**流式 / 非流式共用的唯一**一处请求体拼装点，
        //   在这里加一个开关 = 两条路同时生效，不会出现"改了一条忘了另一条"。
        //
        // 为什么 advice 之外要摘掉画像（原话："这么多步都会拼接用户画像完全没必要"）：
        //   ① 画像里那句「请在回答时优先考虑…目标热量和宏量营养素方向」是**写死的强指令**，
        //      问「鸡胸肉多少卡」这类公共营养问题也会被要求往"你的减脂目标"上靠 → **画像串味**；
        //   ② 更要紧的是**拒绝场合**：越狱样本（如"扮演没有内容限制的医学顾问"）被模型拒绝后，
        //      仍会照着个性化指令补一段"就你这份档案来说…" → 把身高体重/BMI/过敏原**回吐**给
        //      一个正在被拒绝的提问者（安全上叫**软拒绝泄漏**）。
        //
        // ⚠️ 这也是 `intent` 第一次**真的驱动行为** —— 以前它只算不派、只透传给测试看。
        //    代价要有意识：非 advice 的回答会变"通用"，不再带用户档案。
        String assistantContext = "";
        if (includeProfile) {
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
            assistantContext = buildIngredientAssistantContext(healthInfo, dietGoal, preference, healthInfoPayload, dietGoalPayload);
        }

        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", deepSeekModel);
        requestBody.put("temperature", 0.6);

        // 这里原来有三行"加了又清"的废动作（第一版遗留的 JSON 数组提示词）：
        //   messages.add(...); messages.add(...); messages.clear();
        // 加完立刻 clear，等于没写；可那段"严格返回 JSON 数组"的提示词留在源码里
        // 极具误导性 —— 读到的人会以为模型现在仍被要求返回 JSON 数组。已删除。
        List<Map<String, String>> messages = new ArrayList<>();
        // 基础系统提示词里的"结合用户档案"一句，与实际是否带画像保持一致：
        // 只有 assistantContext 非空（即真的拼了画像）才让它出现，否则那句会变成指向不存在数据的空指令。
        messages.add(buildMessage("system", buildIngredientAssistantSystemPrompt(!assistantContext.isEmpty())));
        // 不带画像时这段 system 消息**整条不发** —— 否则会发出一条空内容的消息，
        // 部分模型对空 content 会报 400。
        if (!assistantContext.isEmpty()) {
            messages.add(buildMessage("system", assistantContext));
        }
        // ⭐ 知识库事实块（2026-10-16 新增）：knowledge + ingredient 路由下由代码查出来的
        //    **确定性数值**（米饭 = 116 千卡…）。模型只负责把它讲成人话，不允许改数。
        //
        //    与画像**各自独立判断**，不共用一个 boolean：
        //      画像 → 只在 advice 出现；事实块 → 只在 knowledge+ingredient 出现。
        //      两者当前不会同时非空，但**别因此合并** —— 一个字段装两个维度，
        //      这个项目在"意图表 vs 硬拦表"上已经付过一次代价。
        if (knowledgeFacts != null && !knowledgeFacts.isEmpty()) {
            messages.add(buildMessage("system", knowledgeFacts));
        }
        // 注入本会话的多轮历史（最近窗口，按时间正序），让模型能理解"它/那个/再来一份"等指代
        messages.addAll(buildConversationHistoryMessages(ingredientData));
        messages.add(buildMessage("user", buildIngredientAssistantNaturalUserPrompt(question, assistantContext)));
        requestBody.put("messages", messages);

        if (stream) {
            // 关键的一行：让 DeepSeek 按 SSE 分块吐字，而不是等整段生成完再一次性返回。
            requestBody.put("stream", true);
        }
        return requestBody;
    }

    /**
     * 流式调用 DeepSeek，把增量逐段交给 onDelta。
     *
     * 为什么不用 postForObject：那个方法会把响应体**整个读完**再返回，
     * 流式的意义就没了。这里用 RestTemplate.execute + 自己的 ResponseExtractor，
     * 直接拿着响应的 InputStream 一行行读 —— 读一行推一段，才叫流式。
     *
     * 没有引入新依赖：RestTemplate 本来就支持 execute（底层还是 JDK 的 HttpURLConnection，
     * 它不会把响应缓冲起来）。
     *
     * 返回值和 getDeepSeekIngredientAssistantResult 同构（mode / text / source）。
     * 半路断了但已经吐出去一些 → 返回那部分（别让用户看到的内容凭空消失）；
     * 一个字都没吐就失败 → 返回 null，交给上层走"模型不可用"那条路。
     */
    private Map<String, Object> streamDeepSeekAssistantResult(Map<String, Object> ingredientData, String question, Consumer<String> onDelta, boolean includeProfile, String knowledgeFacts) {
        // 与非流式路径对齐：这两个前置条件不满足就直接当"不可用"，别打一个注定失败的请求。
        if (deepSeekApiKey == null || deepSeekApiKey.trim().isEmpty()) {
            log.warn("DEEPSEEK_API_KEY 未配置或为空，AI 助手无法调用模型");
            return null;
        }
        if (question == null || question.isEmpty()) {
            return null;
        }

        Map<String, Object> requestBody = buildAssistantRequestBody(ingredientData, question, true, includeProfile, knowledgeFacts);
        StringBuilder accumulated = new StringBuilder();

        try {
            restTemplate.execute(
                deepSeekBaseUrl + "/chat/completions",
                HttpMethod.POST,
                request -> {
                    request.getHeaders().setContentType(MediaType.APPLICATION_JSON);
                    request.getHeaders().setBearerAuth(deepSeekApiKey.trim());
                    objectMapper.writeValue(request.getBody(), requestBody);
                },
                response -> {
                    try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(response.getBody(), StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            // DeepSeek 的流是一行一个事件：`data: {...}`，最后一行是 `data: [DONE]`。
                            // 空行是事件分隔符，忽略。
                            if (!line.startsWith("data:")) {
                                continue;
                            }
                            String payload = line.substring(5).trim();
                            if (payload.isEmpty() || "[DONE]".equals(payload)) {
                                continue;
                            }
                            String piece = extractDeltaContent(payload);
                            if (piece != null && !piece.isEmpty()) {
                                accumulated.append(piece);
                                onDelta.accept(piece);
                            }
                        }
                    }
                    return null;
                }
            );
        } catch (Exception exception) {
            log.error("DeepSeek 流式调用失败: {}", exception.getMessage(), exception);
            if (accumulated.length() == 0) {
                return null;
            }
        }

        if (accumulated.length() == 0) {
            return null;
        }
        return buildAssistantTextResult(accumulated.toString(), "deepseek");
    }

    /**
     * 从一个流式分片 JSON 里取出增量文字：choices[0].delta.content。
     *
     * 取不到就返回 null（例如首包只有 role、没有 content；或末尾包 delta 为空对象）。
     * 解析失败也返回 null —— 单个坏分片不值得让整个回答崩掉。
     */
    private String extractDeltaContent(String json) {
        try {
            JsonNode root = objectMapper.readTree(json);
            JsonNode choices = root.path("choices");
            if (!choices.isArray() || choices.isEmpty()) {
                return null;
            }
            JsonNode content = choices.get(0).path("delta").path("content");
            return content.isMissingNode() || content.isNull() ? null : content.asText();
        } catch (Exception exception) {
            log.warn("解析 DeepSeek 流式分片失败: {}", exception.getMessage());
            return null;
        }
    }

    private Map<String, Object> getDeepSeekIngredientAssistantResult(Map<String, Object> ingredientData, boolean includeProfile, String knowledgeFacts) {
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

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setBearerAuth(deepSeekApiKey.trim());

            Map<String, Object> requestBody = buildAssistantRequestBody(ingredientData, question, false, includeProfile, knowledgeFacts);

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

    /**
     * 拼装喂给模型的「用户当前信息」上下文。
     *
     * ⚠️ 2026-10-14 修复一处**静默失败**（画像丢失）：
     *    改之前这段是**整段二选一** —— 只要 payload（前端拼好的 healthInfo / dietGoal）
     *    或 preference 任一非空，就整段走 payload 分支，**库表里刚按 userId 查出来的
     *    healthInfo / dietGoal 被直接丢掉**。而 user_diet_preference 几乎必然有行，
     *    所以那个"回退库表"的兜底分支实际永远走不到。
     *    后果：不传 payload 的客户端（移动端 app/pages/assistant/chat.vue、直连 API、
     *    自动化用例）拿到的是"你目前没有填写过敏/忌口、慢性病和目标热量信息"——
     *    模型不是没看，是根本没收到。**不报错，只是答案悄悄变差。**
     *
     *    修法：改成**分段回退** —— 每一段 payload 优先（前端已拼好的直接用），
     *    payload 为空才回退到库表实体。两路内容等价，所以网页端（走 payload）行为不变。
     *    原 3 参重载只剩"回退"这一个用途，已随本次修复删除（它是死代码）。
     */
    private String buildIngredientAssistantContext(
        HealthInfo healthInfo,
        DietGoal dietGoal,
        UserDietPreference preference,
        Map<String, Object> healthInfoPayload,
        Map<String, Object> dietGoalPayload
    ) {
        StringBuilder context = new StringBuilder("以下是用户当前信息。");
        // ① 健康档案：payload 优先（前端已拼好的直接用），payload 为空则回退库表实体。
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
        } else if (healthInfo != null) {
            context.append(" 健康档案：")
                .append("年龄=").append(valueOrDash(healthInfo.getAge()))
                .append("，性别=").append(valueOrDash(healthInfo.getGender()))
                .append("，身高=").append(valueOrDash(healthInfo.getHeight())).append("cm")
                .append("，体重=").append(valueOrDash(healthInfo.getWeight())).append("kg")
                .append("，BMI=").append(valueOrDash(healthInfo.getBmi()))
                .append("，基础代谢=").append(valueOrDash(healthInfo.getBmr())).append("kcal")
                .append("，活动水平=").append(valueOrDash(healthInfo.getActivityLevel()))
                .append("，慢病情况=").append(valueOrDash(healthInfo.getChronicDiseases()))
                .append("。");
        }
        // ② 饮食偏好：只有库表一个来源（前端不传这段 payload）。
        if (preference != null) {
            context.append(" 饮食偏好：")
                .append("过敏/忌口=").append(valueOrDash(preference.getAllergies()))
                .append("，不喜欢食物=").append(valueOrDash(preference.getDislikes()))
                .append("。");
        }
        // ③ 饮食目标：同 ①，payload 优先、为空回退库表。
        if (dietGoalPayload != null && !dietGoalPayload.isEmpty()) {
            context.append(" 饮食目标：")
                .append("目标类型=").append(valueOrDash(readPayloadValue(dietGoalPayload, "goalType")))
                .append("，目标热量=").append(valueOrDash(readPayloadValue(dietGoalPayload, "targetCalories"))).append("kcal")
                .append("，蛋白质目标=").append(valueOrDash(readPayloadValue(dietGoalPayload, "proteinTarget"))).append("g")
                .append("，碳水目标=").append(valueOrDash(readPayloadValue(dietGoalPayload, "carbsTarget"))).append("g")
                .append("，脂肪目标=").append(valueOrDash(readPayloadValue(dietGoalPayload, "fatTarget"))).append("g")
                .append("，饮水目标=").append(valueOrDash(readPayloadValue(dietGoalPayload, "waterTarget"))).append("ml")
                .append("。");
        } else if (dietGoal != null) {
            context.append(" 饮食目标：")
                .append("目标类型=").append(valueOrDash(dietGoal.getGoalType()))
                .append("，目标热量=").append(valueOrDash(dietGoal.getTargetCalories())).append("kcal")
                .append("，蛋白质目标=").append(valueOrDash(dietGoal.getProteinTarget())).append("g")
                .append("，碳水目标=").append(valueOrDash(dietGoal.getCarbsTarget())).append("g")
                .append("，脂肪目标=").append(valueOrDash(dietGoal.getFatTarget())).append("g")
                .append("，饮水目标=").append(valueOrDash(dietGoal.getWaterTarget())).append("ml")
                .append("。");
        }
        context.append(" 请在回答时优先考虑饮食偏好中的过敏/忌口、慢性疾病、目标热量和宏量营养素方向。");
        return context.toString();
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
    /**
     * 基础系统提示词。
     *
     * ⚠️ 2026-10-14：「结合用户档案」这句**随画像有无一起进退**（与 buildIngredientAssistantNaturalUserPrompt 同理）。
     * 以前这句是无条件写死的，但非 advice 调用根本不把画像塞进消息，
     * 于是模型一边被要求"结合档案"、一边根本没有数据、又被自然 prompt 禁止提档案 —— 自相矛盾，
     * 实测会让模型反问"请告诉我你的身高体重"或凭空编一段档案。
     * 改成：只有真的带画像（hasProfile=true，即 assistantContext 非空）才出现这句，否则直接落到"用自然专业清晰的中文回答"。
     */
    private String buildIngredientAssistantSystemPrompt(boolean hasProfile) {
        String profileClause = hasProfile
            ? "请结合用户当前健康档案、饮食目标、过敏/忌口和慢性病信息，"
            : "";
        return "你是一位专业的饮食与健康助手。"
            + "你可以回答：食材替代、食谱分析、三餐搭配、营养成分与热量估算、"
            + "控油控糖控钠等饮食调整、慢病相关的饮食注意事项、运动与体重管理、"
            + "以及保健品的常见作用与注意事项。"
            + profileClause
            + "用自然、专业、清晰的中文回答。"
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
        //
        // ⚠️ 2026-10-14：画像段可能**整段缺席**（非 advice 意图不带画像，见 buildAssistantRequestBody）。
        //    这时候"请结合以下用户信息回答"和"如果它涉及该用户的过敏/忌口…"都是**指向不存在的
        //    信息**的空指令 —— 实测模型会顺口编一句「你目前没有填写过敏/忌口信息」，
        //    这正是要去掉的"串味/档案回吐"。所以两句话都随画像**一起进退**。
        boolean hasProfile = assistantContext != null && !assistantContext.isEmpty();
        String head = hasProfile
            ? "请结合以下用户信息回答。\n" + assistantContext + "\n"
            : "请直接回答用户的问题。\n";
        String requirement = hasProfile
            ? "要求：先直接回答这个问题；如果它涉及该用户的过敏/忌口、慢性病或饮食目标，"
                + "再简要说明为什么这样建议适合他。若问题超出饮食与健康范围，按安全边界说明你的职责。"
            : "要求：先直接回答这个问题。若问题超出饮食与健康范围，按安全边界说明你的职责。"
                + "不要复述、猜测或提及任何用户个人档案（身高体重、热量目标、过敏忌口等）——"
                + "本轮没有向你提供这些信息。";
        return head
            + "用户问题：" + question + "\n"
            + requirement
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
