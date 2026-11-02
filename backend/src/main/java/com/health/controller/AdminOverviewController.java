package com.health.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.health.entity.DietRecord;
import com.health.entity.HealthArticle;
import com.health.entity.Ingredient;
import com.health.entity.Notification;
import com.health.entity.Recipe;
import com.health.entity.User;
import com.health.entity.UserArticleCollect;
import com.health.entity.UserReadRecord;
import com.health.entity.UserRecipeCollect;
import com.health.mapper.DietRecordMapper;
import com.health.mapper.HealthArticleMapper;
import com.health.mapper.IngredientMapper;
import com.health.mapper.NotificationMapper;
import com.health.mapper.RecipeMapper;
import com.health.mapper.UserArticleCollectMapper;
import com.health.mapper.UserReadRecordMapper;
import com.health.mapper.UserRecipeCollectMapper;
import com.health.service.HealthArticleService;
import com.health.service.RecipeService;
import com.health.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.security.Principal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/admin")
public class AdminOverviewController {

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("MM-dd");

    @Autowired
    private UserService userService;

    @Autowired
    private IngredientMapper ingredientMapper;

    @Autowired
    private RecipeMapper recipeMapper;

    @Autowired
    private HealthArticleMapper healthArticleMapper;

    @Autowired
    private NotificationMapper notificationMapper;

    @Autowired
    private DietRecordMapper dietRecordMapper;

    @Autowired
    private UserRecipeCollectMapper userRecipeCollectMapper;

    @Autowired
    private UserArticleCollectMapper userArticleCollectMapper;

    @Autowired
    private UserReadRecordMapper userReadRecordMapper;

    @Autowired
    private RecipeService recipeService;

    @Autowired
    private HealthArticleService healthArticleService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @GetMapping("/overview")
    public ResponseEntity<?> getOverview(Principal principal) {
        try {
            requireAdmin(principal);

            List<User> users = userService.listUsers();
            List<Ingredient> ingredients = ingredientMapper.selectList(new QueryWrapper<Ingredient>().orderByDesc("create_time"));
            List<Recipe> recipes = recipeMapper.selectList(new QueryWrapper<Recipe>().orderByDesc("create_time"));
            List<HealthArticle> articles = healthArticleMapper.selectList(new QueryWrapper<HealthArticle>().orderByDesc("create_time"));
            List<Notification> notifications = notificationMapper.selectList(
                new QueryWrapper<Notification>().eq("is_deleted", 0).orderByDesc("create_time")
            );
            List<DietRecord> dietRecords = dietRecordMapper.selectList(
                new QueryWrapper<DietRecord>().eq("is_deleted", 0).orderByDesc("create_time")
            );
            List<UserReadRecord> readRecords = userReadRecordMapper.selectList(
                new QueryWrapper<UserReadRecord>().orderByDesc("read_time")
            );
            List<UserRecipeCollect> recipeCollects = userRecipeCollectMapper.selectList(new QueryWrapper<>());
            List<UserArticleCollect> articleCollects = userArticleCollectMapper.selectList(new QueryWrapper<>());

            Map<String, Object> data = new HashMap<>();
            data.put("summary", buildSummary(users, ingredients, recipes, articles, notifications, dietRecords, readRecords));
            data.put("trends", buildTrends(users, dietRecords, readRecords));
            data.put("topRecipes", buildTopRecipes(recipes, recipeCollects));
            data.put("topArticles", buildTopArticles(articles, articleCollects, readRecords));
            data.put("recentActivities", buildRecentActivities(users, recipes, articles, notifications, readRecords));
            data.put("meta", buildMeta(dietRecords, readRecords));

            return successResponse("获取后台总览成功", data);
        } catch (Exception e) {
            log.error("获取后台总览失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    private Map<String, Object> buildSummary(
        List<User> users,
        List<Ingredient> ingredients,
        List<Recipe> recipes,
        List<HealthArticle> articles,
        List<Notification> notifications,
        List<DietRecord> dietRecords,
        List<UserReadRecord> readRecords
    ) {
        LocalDate today = LocalDate.now();
        LocalDate yesterday = today.minusDays(1);

        long disabledUserCount = users.stream()
            .filter(user -> Integer.valueOf(0).equals(user.getStatus()))
            .count();
        long todayNewUsers = users.stream()
            .filter(user -> today.equals(toLocalDate(user.getCreateTime())))
            .count();
        long yesterdayNewUsers = users.stream()
            .filter(user -> yesterday.equals(toLocalDate(user.getCreateTime())))
            .count();

        Set<Long> todayActiveUsers = dietRecords.stream()
            .filter(record -> today.equals(toLocalDate(record.getCreateTime(), record.getRecordDate())))
            .map(DietRecord::getUserId)
            .filter(Objects::nonNull)
            .collect(Collectors.toCollection(LinkedHashSet::new));
        Set<Long> yesterdayActiveUsers = dietRecords.stream()
            .filter(record -> yesterday.equals(toLocalDate(record.getCreateTime(), record.getRecordDate())))
            .map(DietRecord::getUserId)
            .filter(Objects::nonNull)
            .collect(Collectors.toCollection(LinkedHashSet::new));

        long todayDietRecordCount = dietRecords.stream()
            .filter(record -> today.equals(toLocalDate(record.getCreateTime(), record.getRecordDate())))
            .count();
        long yesterdayDietRecordCount = dietRecords.stream()
            .filter(record -> yesterday.equals(toLocalDate(record.getCreateTime(), record.getRecordDate())))
            .count();
        long todayNotificationCount = notifications.stream()
            .filter(item -> today.equals(toLocalDate(item.getCreateTime(), item.getSendTime())))
            .count();
        long yesterdayNotificationCount = notifications.stream()
            .filter(item -> yesterday.equals(toLocalDate(item.getCreateTime(), item.getSendTime())))
            .count();
        long unreadNotificationCount = notifications.stream()
            .filter(item -> !Integer.valueOf(1).equals(item.getIsRead()))
            .count();
        long customRecipeCount = recipes.stream()
            .filter(recipe -> Integer.valueOf(1).equals(recipe.getIsCustom()))
            .count();

        long todayArticleReadCount = readRecords.stream()
            .filter(item -> today.equals(toLocalDate(item.getReadTime())))
            .count();
        long yesterdayArticleReadCount = readRecords.stream()
            .filter(item -> yesterday.equals(toLocalDate(item.getReadTime())))
            .count();
        long todayFinishedReadCount = readRecords.stream()
            .filter(item -> today.equals(toLocalDate(item.getReadTime())))
            .filter(item -> Integer.valueOf(1).equals(item.getIsFinished()))
            .count();
        long todayReadUserCount = readRecords.stream()
            .filter(item -> today.equals(toLocalDate(item.getReadTime())))
            .map(UserReadRecord::getUserId)
            .filter(Objects::nonNull)
            .distinct()
            .count();

        Map<String, Object> summary = new HashMap<>();
        summary.put("userCount", users.size());
        summary.put("todayActiveUserCount", todayActiveUsers.size());
        summary.put("recipeCount", recipes.size());
        summary.put("todayDietRecordCount", todayDietRecordCount);
        summary.put("articleCount", articles.size());
        summary.put("todayNotificationCount", todayNotificationCount);
        summary.put("ingredientCount", ingredients.size());
        summary.put("disabledUserCount", disabledUserCount);
        summary.put("unreadNotificationCount", unreadNotificationCount);
        summary.put("customRecipeCount", customRecipeCount);
        summary.put("todayNewUsers", todayNewUsers);
        summary.put("todayArticleReadCount", todayArticleReadCount);
        summary.put("todayFinishedReadCount", todayFinishedReadCount);
        summary.put("todayReadUserCount", todayReadUserCount);
        summary.put("changes", buildSummaryChanges(
            todayNewUsers,
            yesterdayNewUsers,
            todayActiveUsers.size(),
            yesterdayActiveUsers.size(),
            todayDietRecordCount,
            yesterdayDietRecordCount,
            todayNotificationCount,
            yesterdayNotificationCount,
            todayArticleReadCount,
            yesterdayArticleReadCount
        ));
        return summary;
    }

    private Map<String, Object> buildSummaryChanges(
        long todayNewUsers,
        long yesterdayNewUsers,
        long todayActiveUserCount,
        long yesterdayActiveUserCount,
        long todayDietRecordCount,
        long yesterdayDietRecordCount,
        long todayNotificationCount,
        long yesterdayNotificationCount,
        long todayArticleReadCount,
        long yesterdayArticleReadCount
    ) {
        Map<String, Object> changes = new HashMap<>();
        changes.put("userCount", buildChangePayload(todayNewUsers, yesterdayNewUsers, "较昨日新增用户"));
        changes.put("todayActiveUserCount", buildChangePayload(todayActiveUserCount, yesterdayActiveUserCount, "较昨日活跃用户"));
        changes.put("todayDietRecordCount", buildChangePayload(todayDietRecordCount, yesterdayDietRecordCount, "较昨日饮食记录"));
        changes.put("todayNotificationCount", buildChangePayload(todayNotificationCount, yesterdayNotificationCount, "较昨日通知发送"));
        changes.put("todayArticleReadCount", buildChangePayload(todayArticleReadCount, yesterdayArticleReadCount, "较昨日文章阅读"));
        return changes;
    }

    private Map<String, Object> buildChangePayload(long current, long previous, String label) {
        Map<String, Object> payload = new HashMap<>();
        long delta = current - previous;
        payload.put("label", label);
        payload.put("delta", delta);
        payload.put("trend", delta >= 0 ? "up" : "down");
        payload.put("deltaText", delta >= 0 ? "+" + delta : String.valueOf(delta));
        return payload;
    }

    private Map<String, Object> buildTrends(
        List<User> users,
        List<DietRecord> dietRecords,
        List<UserReadRecord> readRecords
    ) {
        LocalDate today = LocalDate.now();
        LocalDate startDate = today.minusDays(6);

        LinkedHashMap<LocalDate, Integer> activeUserTrend = initDailyBuckets(startDate, today);
        LinkedHashMap<LocalDate, Integer> newUserTrend = initDailyBuckets(startDate, today);
        LinkedHashMap<LocalDate, Integer> recordTrend = initDailyBuckets(startDate, today);
        LinkedHashMap<LocalDate, Integer> articleReadTrend = initDailyBuckets(startDate, today);
        LinkedHashMap<LocalDate, Integer> finishedReadTrend = initDailyBuckets(startDate, today);
        Map<LocalDate, Set<Long>> activeUserBuckets = new HashMap<>();

        for (User user : users) {
            LocalDate date = toLocalDate(user.getCreateTime());
            if (date != null && newUserTrend.containsKey(date)) {
                newUserTrend.put(date, newUserTrend.get(date) + 1);
            }
        }

        for (DietRecord record : dietRecords) {
            LocalDate date = toLocalDate(record.getCreateTime(), record.getRecordDate());
            if (date == null || !recordTrend.containsKey(date)) {
                continue;
            }

            recordTrend.put(date, recordTrend.get(date) + 1);
            if (record.getUserId() != null) {
                activeUserBuckets.computeIfAbsent(date, key -> new LinkedHashSet<>()).add(record.getUserId());
            }
        }

        for (UserReadRecord readRecord : readRecords) {
            LocalDate date = toLocalDate(readRecord.getReadTime());
            if (date == null || !articleReadTrend.containsKey(date)) {
                continue;
            }

            articleReadTrend.put(date, articleReadTrend.get(date) + 1);
            if (Integer.valueOf(1).equals(readRecord.getIsFinished())) {
                finishedReadTrend.put(date, finishedReadTrend.get(date) + 1);
            }
        }

        for (Map.Entry<LocalDate, Integer> entry : activeUserTrend.entrySet()) {
            Set<Long> ids = activeUserBuckets.get(entry.getKey());
            activeUserTrend.put(entry.getKey(), ids == null ? 0 : ids.size());
        }

        Map<String, Object> trends = new HashMap<>();
        trends.put(
            "dates",
            activeUserTrend.keySet().stream().map(date -> date.format(DATE_FORMATTER)).collect(Collectors.toList())
        );
        trends.put("activeUsers", new ArrayList<>(activeUserTrend.values()));
        trends.put("newUsers", new ArrayList<>(newUserTrend.values()));
        trends.put("dietRecords", new ArrayList<>(recordTrend.values()));
        trends.put("articleReads", new ArrayList<>(articleReadTrend.values()));
        trends.put("finishedReads", new ArrayList<>(finishedReadTrend.values()));
        return trends;
    }

    private List<Map<String, Object>> buildTopRecipes(List<Recipe> recipes, List<UserRecipeCollect> recipeCollects) {
        Map<Long, Long> collectCountMap = recipeCollects.stream()
            .filter(item -> item.getRecipeId() != null)
            .collect(Collectors.groupingBy(UserRecipeCollect::getRecipeId, Collectors.counting()));

        return recipes.stream()
            .sorted(
                Comparator
                    .comparingLong((Recipe recipe) -> collectCountMap.getOrDefault(recipe.getId(), safeLong(recipe.getCollectCount())))
                    .reversed()
                    .thenComparing(recipe -> safeInteger(recipe.getViewCount()), Comparator.reverseOrder())
                    .thenComparing(Recipe::getUpdateTime, Comparator.nullsLast(Comparator.reverseOrder()))
                    .thenComparing(Recipe::getCreateTime, Comparator.nullsLast(Comparator.reverseOrder()))
            )
            .limit(5)
            .map(recipe -> {
                Map<String, Object> item = new HashMap<>();
                item.put("id", recipe.getId());
                item.put("name", recipe.getName());
                item.put("goalType", recipe.getGoalType());
                item.put("isCustom", Integer.valueOf(1).equals(recipe.getIsCustom()));
                item.put("collectCount", collectCountMap.getOrDefault(recipe.getId(), safeLong(recipe.getCollectCount())));
                item.put("viewCount", safeInteger(recipe.getViewCount()));
                item.put("heatScore", collectCountMap.getOrDefault(recipe.getId(), safeLong(recipe.getCollectCount())) * 4L + safeInteger(recipe.getViewCount()));
                return item;
            })
            .collect(Collectors.toList());
    }

    private List<Map<String, Object>> buildTopArticles(
        List<HealthArticle> articles,
        List<UserArticleCollect> articleCollects,
        List<UserReadRecord> readRecords
    ) {
        Map<Long, Long> collectCountMap = articleCollects.stream()
            .filter(item -> item.getArticleId() != null)
            .collect(Collectors.groupingBy(UserArticleCollect::getArticleId, Collectors.counting()));
        Map<Long, Long> readCountMap = readRecords.stream()
            .filter(item -> item.getArticleId() != null)
            .collect(Collectors.groupingBy(UserReadRecord::getArticleId, Collectors.counting()));
        Map<Long, Long> finishedReadCountMap = readRecords.stream()
            .filter(item -> item.getArticleId() != null && Integer.valueOf(1).equals(item.getIsFinished()))
            .collect(Collectors.groupingBy(UserReadRecord::getArticleId, Collectors.counting()));

        return articles.stream()
            .sorted(
                Comparator
                    .comparingDouble((HealthArticle article) -> articleHeat(
                        article,
                        collectCountMap.getOrDefault(article.getId(), 0L),
                        readCountMap.getOrDefault(article.getId(), safeLong(article.getReadCount())),
                        finishedReadCountMap.getOrDefault(article.getId(), 0L)
                    ))
                    .reversed()
                    .thenComparing(HealthArticle::getPublishDate, Comparator.nullsLast(Comparator.reverseOrder()))
                    .thenComparing(HealthArticle::getCreateTime, Comparator.nullsLast(Comparator.reverseOrder()))
            )
            .limit(5)
            .map(article -> {
                long collectCount = collectCountMap.getOrDefault(article.getId(), 0L);
                long readCount = readCountMap.getOrDefault(article.getId(), safeLong(article.getReadCount()));
                long finishedReadCount = finishedReadCountMap.getOrDefault(article.getId(), 0L);
                Map<String, Object> item = new HashMap<>();
                item.put("id", article.getId());
                item.put("title", article.getTitle());
                item.put("category", article.getCategory());
                item.put("readCount", readCount);
                item.put("likeCount", safeInteger(article.getLikeCount()));
                item.put("commentCount", safeInteger(article.getCommentCount()));
                item.put("collectCount", collectCount);
                item.put("finishedReadCount", finishedReadCount);
                item.put("heatScore", Math.round(articleHeat(article, collectCount, readCount, finishedReadCount)));
                return item;
            })
            .collect(Collectors.toList());
    }

    private Map<String, Object> buildRecentActivities(
        List<User> users,
        List<Recipe> recipes,
        List<HealthArticle> articles,
        List<Notification> notifications,
        List<UserReadRecord> readRecords
    ) {
        Map<String, Object> activities = new HashMap<>();
        LocalDate today = LocalDate.now();

        long disabledUserCount = users.stream()
            .filter(user -> Integer.valueOf(0).equals(user.getStatus()))
            .count();
        long unreadNotificationCount = notifications.stream()
            .filter(item -> !Integer.valueOf(1).equals(item.getIsRead()))
            .count();
        long todayReadUserCount = readRecords.stream()
            .filter(item -> today.equals(toLocalDate(item.getReadTime())))
            .map(UserReadRecord::getUserId)
            .filter(Objects::nonNull)
            .distinct()
            .count();
        long todayFinishedReadCount = readRecords.stream()
            .filter(item -> today.equals(toLocalDate(item.getReadTime())))
            .filter(item -> Integer.valueOf(1).equals(item.getIsFinished()))
            .count();

        activities.put("disabledUserCount", disabledUserCount);
        activities.put("unreadNotificationCount", unreadNotificationCount);
        activities.put("todayReadUserCount", todayReadUserCount);
        activities.put("todayFinishedReadCount", todayFinishedReadCount);
        activities.put(
            "recentArticles",
            articles.stream()
                .sorted(Comparator.comparing(HealthArticle::getCreateTime, Comparator.nullsLast(Comparator.reverseOrder())))
                .limit(3)
                .map(article -> {
                    Map<String, Object> item = new HashMap<>();
                    item.put("id", article.getId());
                    item.put("title", article.getTitle());
                    item.put("category", article.getCategory());
                    item.put("createTime", article.getCreateTime());
                    return item;
                })
                .collect(Collectors.toList())
        );
        activities.put(
            "recentCustomRecipes",
            recipes.stream()
                .filter(recipe -> Integer.valueOf(1).equals(recipe.getIsCustom()))
                .sorted(Comparator.comparing(Recipe::getCreateTime, Comparator.nullsLast(Comparator.reverseOrder())))
                .limit(3)
                .map(recipe -> {
                    Map<String, Object> item = new HashMap<>();
                    item.put("id", recipe.getId());
                    item.put("name", recipe.getName());
                    item.put("goalType", recipe.getGoalType());
                    item.put("createTime", recipe.getCreateTime());
                    return item;
                })
                .collect(Collectors.toList())
        );
        return activities;
    }

    private Map<String, Object> buildMeta(List<DietRecord> dietRecords, List<UserReadRecord> readRecords) {
        LocalDate today = LocalDate.now();
        LocalDate lastWeekStart = today.minusDays(6);
        LocalDate previousWeekStart = today.minusDays(13);
        LocalDate previousWeekEnd = today.minusDays(7);

        long currentWeekRecordCount = countDietRecordsBetween(dietRecords, lastWeekStart, today);
        long previousWeekRecordCount = countDietRecordsBetween(dietRecords, previousWeekStart, previousWeekEnd);
        long currentWeekReadCount = countReadRecordsBetween(readRecords, lastWeekStart, today);
        long previousWeekReadCount = countReadRecordsBetween(readRecords, previousWeekStart, previousWeekEnd);

        String summaryText;
        if (currentWeekReadCount > previousWeekReadCount) {
            summaryText = "过去 7 天文章阅读活跃度提升，内容消费行为在增长。";
        } else if (currentWeekRecordCount > previousWeekRecordCount) {
            summaryText = "过去 7 天饮食记录保持增长，用户健康打卡较稳定。";
        } else {
            summaryText = "过去 7 天整体数据较平稳，建议继续提升内容阅读转化。";
        }

        Map<String, Object> meta = new HashMap<>();
        meta.put("currentDate", today.toString());
        meta.put("summaryText", summaryText);
        return meta;
    }

    private long countDietRecordsBetween(List<DietRecord> records, LocalDate startDate, LocalDate endDate) {
        return records.stream()
            .map(record -> toLocalDate(record.getCreateTime(), record.getRecordDate()))
            .filter(Objects::nonNull)
            .filter(date -> !date.isBefore(startDate) && !date.isAfter(endDate))
            .count();
    }

    private long countReadRecordsBetween(List<UserReadRecord> readRecords, LocalDate startDate, LocalDate endDate) {
        return readRecords.stream()
            .map(record -> toLocalDate(record.getReadTime()))
            .filter(Objects::nonNull)
            .filter(date -> !date.isBefore(startDate) && !date.isAfter(endDate))
            .count();
    }

    private LinkedHashMap<LocalDate, Integer> initDailyBuckets(LocalDate start, LocalDate end) {
        LinkedHashMap<LocalDate, Integer> buckets = new LinkedHashMap<>();
        LocalDate cursor = start;
        while (!cursor.isAfter(end)) {
            buckets.put(cursor, 0);
            cursor = cursor.plusDays(1);
        }
        return buckets;
    }

    private double articleHeat(HealthArticle article, long collectCount, long readCount, long finishedReadCount) {
        return readCount
            + finishedReadCount * 2.5
            + safeInteger(article.getLikeCount()) * 3.0
            + safeInteger(article.getCommentCount()) * 2.0
            + collectCount * 4.0;
    }

    private int safeInteger(Integer value) {
        return value == null ? 0 : value;
    }

    private long safeLong(Integer value) {
        return value == null ? 0 : value.longValue();
    }

    private LocalDate toLocalDate(LocalDateTime value) {
        return value == null ? null : value.toLocalDate();
    }

    private LocalDate toLocalDate(Date value) {
        return value == null ? null : value.toInstant().atZone(ZoneId.systemDefault()).toLocalDate();
    }

    private LocalDate toLocalDate(LocalDateTime dateTime, Date fallbackDate) {
        LocalDate date = toLocalDate(dateTime);
        return date != null ? date : toLocalDate(fallbackDate);
    }

    private LocalDate toLocalDate(LocalDateTime dateTime, LocalDateTime fallbackDateTime) {
        LocalDate date = toLocalDate(dateTime);
        return date != null ? date : toLocalDate(fallbackDateTime);
    }

    @GetMapping("/{type}/list")
    public ResponseEntity<?> listContent(
        @PathVariable String type,
        @RequestParam(required = false) String keyword,
        @RequestParam(required = false) String cat,
        @RequestParam(required = false) String status,
        Principal principal
    ) {
        try {
            requireAdmin(principal);

            String kw = keyword == null ? "" : keyword.trim().toLowerCase();
            boolean onlyOn = "on".equals(status);
            boolean onlyOff = "off".equals(status);
            List<Object> rows = new ArrayList<>();

            if ("recipe".equals(type)) {
                List<Recipe> recipes = recipeMapper.selectList(new QueryWrapper<Recipe>().orderByDesc("create_time"));
                for (Recipe recipe : recipes) {
                    if (!matchesText(kw, recipe.getName(), recipe.getDescription())) {
                        continue;
                    }
                    if (cat != null && !cat.isBlank() && !cat.equals(recipe.getCategory())) {
                        continue;
                    }
                    if ((onlyOn && Integer.valueOf(0).equals(recipe.getStatus()))
                        || (onlyOff && !Integer.valueOf(0).equals(recipe.getStatus()))) {
                        continue;
                    }
                    Map<String, Object> row = new HashMap<>();
                    row.put("id", recipe.getId());
                    row.put("name", recipe.getName());
                    row.put("description", recipe.getDescription());
                    row.put("category", recipe.getCategory());
                    row.put("cuisineType", recipe.getCuisineType());
                    row.put("cookingTime", recipe.getCookingTime());
                    row.put("difficulty", recipe.getDifficulty());
                    row.put("servings", recipe.getServings());
                    row.put("totalCalories", recipe.getTotalCalories());
                    row.put("caloriesPerServing", recipe.getCaloriesPerServing());
                    row.put("protein", recipe.getProtein());
                    row.put("carbs", recipe.getCarbs());
                    row.put("fat", recipe.getFat());
                    row.put("fiber", recipe.getFiber());
                    row.put("suitableFor", recipe.getSuitableFor());
                    row.put("tips", recipe.getTips());
                    row.put("instructions", recipe.getInstructions());
                    row.put("imageUrl", recipe.getImageUrl());
                    row.put("status", recipe.getStatus() == null ? 1 : recipe.getStatus());
                    rows.add(row);
                }
            } else if ("article".equals(type)) {
                List<HealthArticle> articles = healthArticleMapper.selectList(
                    new QueryWrapper<HealthArticle>().orderByDesc("create_time")
                );
                for (HealthArticle article : articles) {
                    if (!matchesText(kw, article.getTitle(), article.getSummary())) {
                        continue;
                    }
                    if (cat != null && !cat.isBlank() && !cat.equals(article.getCategory())) {
                        continue;
                    }
                    if ((onlyOn && Integer.valueOf(0).equals(article.getStatus()))
                        || (onlyOff && !Integer.valueOf(0).equals(article.getStatus()))) {
                        continue;
                    }
                    Map<String, Object> row = new HashMap<>();
                    row.put("id", String.valueOf(article.getId()));
                    row.put("title", article.getTitle());
                    row.put("summary", article.getSummary());
                    row.put("content", article.getContent());
                    row.put("category", article.getCategory());
                    row.put("tags", article.getTags());
                    row.put("author", article.getAuthor());
                    row.put("readCount", article.getReadCount());
                    row.put("likeCount", article.getLikeCount());
                    row.put("commentCount", article.getCommentCount());
                    row.put("publishDate", article.getPublishDate());
                    row.put("status", article.getStatus() == null ? 1 : article.getStatus());
                    rows.add(row);
                }
            } else if ("ingredient".equals(type)) {
                List<Ingredient> ingredients = ingredientMapper.selectList(
                    new QueryWrapper<Ingredient>().orderByDesc("create_time")
                );
                for (Ingredient ingredient : ingredients) {
                    if (!matchesText(kw, ingredient.getName(), ingredient.getDescription())) {
                        continue;
                    }
                    if (cat != null && !cat.isBlank() && !cat.equals(ingredient.getCategory())) {
                        continue;
                    }
                    if ((onlyOn && Integer.valueOf(0).equals(ingredient.getStatus()))
                        || (onlyOff && !Integer.valueOf(0).equals(ingredient.getStatus()))) {
                        continue;
                    }
                    rows.add(ingredient);
                }
            } else {
                return badRequestResponse("不支持的内容类型");
            }

            Map<String, Object> data = new HashMap<>();
            data.put("list", rows);
            data.put("total", rows.size());
            return successResponse("获取内容列表成功", data);
        } catch (Exception e) {
            log.error("获取后台内容列表失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PutMapping("/{type}/{id}/status")
    public ResponseEntity<?> updateContentStatus(
        @PathVariable String type,
        @PathVariable Long id,
        @RequestParam Integer status,
        Principal principal
    ) {
        try {
            requireAdmin(principal);

            boolean updated;
            if ("recipe".equals(type)) {
                Recipe recipe = recipeMapper.selectById(id);
                updated = recipe != null;
                if (updated) {
                    recipe.setStatus(status);
                    recipeMapper.updateById(recipe);
                }
            } else if ("article".equals(type)) {
                HealthArticle article = healthArticleMapper.selectById(id);
                updated = article != null;
                if (updated) {
                    article.setStatus(status);
                    healthArticleMapper.updateById(article);
                }
            } else if ("ingredient".equals(type)) {
                Ingredient ingredient = ingredientMapper.selectById(id);
                updated = ingredient != null;
                if (updated) {
                    ingredient.setStatus(status);
                    ingredientMapper.updateById(ingredient);
                }
            } else {
                return badRequestResponse("不支持的内容类型");
            }

            if (!updated) {
                return badRequestResponse("内容不存在");
            }
            return successResponse(status == 0 ? "已下架" : "已上架", true);
        } catch (Exception e) {
            log.error("更新内容状态失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/{type}")
    public ResponseEntity<?> createContent(
        @PathVariable String type,
        @RequestBody Map<String, Object> payload,
        Principal principal
    ) {
        try {
            User admin = requireAdmin(principal);

            if ("recipe".equals(type)) {
                Recipe recipe = new Recipe();
                applyAdminRecipeFields(recipe, payload);
                if (recipe.getName() == null || recipe.getName().isBlank()) {
                    return badRequestResponse("请填写食谱名称");
                }
                recipe.setCreatorId(admin.getId());
                recipe.setIsCustom(0);
                if (recipe.getStatus() == null) {
                    recipe.setStatus(1);
                }
                recipeService.saveRecipe(recipe, null);
                return successResponse("新建食谱成功", true);
            }
            if ("article".equals(type)) {
                HealthArticle article = new HealthArticle();
                applyAdminArticleFields(article, payload);
                if (article.getTitle() == null || article.getTitle().isBlank()) {
                    return badRequestResponse("请填写文章标题");
                }
                if (article.getPublishDate() == null) {
                    article.setPublishDate(new Date());
                }
                if (article.getStatus() == null) {
                    article.setStatus(1);
                }
                healthArticleService.saveArticle(article);
                return successResponse("新建文章成功", true);
            }
            if ("ingredient".equals(type)) {
                Ingredient ingredient = new Ingredient();
                applyAdminIngredientFields(ingredient, payload);
                if (ingredient.getName() == null || ingredient.getName().isBlank()) {
                    return badRequestResponse("请填写食材名称");
                }
                if (ingredient.getStatus() == null) {
                    ingredient.setStatus(1);
                }
                ingredientMapper.insert(ingredient);
                return successResponse("新建食材成功", true);
            }
            return badRequestResponse("不支持的内容类型");
        } catch (Exception e) {
            log.error("新建内容失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    @PutMapping("/{type}/{id}")
    public ResponseEntity<?> updateContent(
        @PathVariable String type,
        @PathVariable Long id,
        @RequestBody Map<String, Object> payload,
        Principal principal
    ) {
        try {
            requireAdmin(principal);

            if ("recipe".equals(type)) {
                Recipe recipe = recipeMapper.selectById(id);
                if (recipe == null) {
                    return badRequestResponse("食谱不存在");
                }
                applyAdminRecipeFields(recipe, payload);
                recipeService.updateRecipe(recipe, null);
                return successResponse("更新食谱成功", true);
            }
            if ("article".equals(type)) {
                HealthArticle article = healthArticleMapper.selectById(id);
                if (article == null) {
                    return badRequestResponse("文章不存在");
                }
                applyAdminArticleFields(article, payload);
                healthArticleService.updateArticle(article);
                return successResponse("更新文章成功", true);
            }
            if ("ingredient".equals(type)) {
                Ingredient ingredient = ingredientMapper.selectById(id);
                if (ingredient == null) {
                    return badRequestResponse("食材不存在");
                }
                applyAdminIngredientFields(ingredient, payload);
                ingredientMapper.updateById(ingredient);
                return successResponse("更新食材成功", true);
            }
            return badRequestResponse("不支持的内容类型");
        } catch (Exception e) {
            log.error("更新内容失败: {}", e.getMessage());
            return badRequestResponse(e.getMessage());
        }
    }

    private void applyAdminRecipeFields(Recipe recipe, Map<String, Object> payload) {
        if (payload.get("name") != null) {
            recipe.setName(text(payload.get("name")));
        }
        if (payload.get("desc") != null) {
            recipe.setDescription(text(payload.get("desc")));
        }
        if (payload.get("time") != null) {
            recipe.setCookingTime(integerValue(payload.get("time")));
        }
        if (payload.get("level") != null) {
            recipe.setDifficulty(text(payload.get("level")));
        }
        Object steps = payload.containsKey("steps") ? payload.get("steps") : payload.get("instructions");
        if (steps != null) {
            recipe.setInstructions(instructionsText(steps));
        }
        if (payload.get("img") != null) {
            recipe.setImageUrl(text(payload.get("img")));
        }
        if (payload.get("mealType") != null) {
            recipe.setCategory(text(payload.get("mealType")));
        }
        if (payload.get("cuisine") != null) {
            recipe.setCuisineType(text(payload.get("cuisine")));
        }
        if (payload.get("servings") != null) {
            recipe.setServings(integerValue(payload.get("servings")));
        }
        Object calories = payload.containsKey("kcal") ? payload.get("kcal") : payload.get("totalCalories");
        if (calories != null) {
            recipe.setTotalCalories(number(calories));
        }
        Object protein = payload.containsKey("p") ? payload.get("p") : payload.get("protein");
        if (protein != null) {
            recipe.setProtein(number(protein));
        }
        Object carbs = payload.containsKey("c") ? payload.get("c") : payload.get("carbs");
        if (carbs != null) {
            recipe.setCarbs(number(carbs));
        }
        Object fat = payload.containsKey("f") ? payload.get("f") : payload.get("fat");
        if (fat != null) {
            recipe.setFat(number(fat));
        }
        if (payload.get("fiber") != null) {
            recipe.setFiber(number(payload.get("fiber")));
        }
        Object fit = payload.containsKey("fit") ? payload.get("fit") : payload.get("suitableFor");
        if (fit != null) {
            recipe.setSuitableFor(joinText(fit));
        }
        if (payload.get("tips") != null) {
            recipe.setTips(text(payload.get("tips")));
        }
        if (payload.get("status") != null) {
            recipe.setStatus(integerValue(payload.get("status")));
        }
    }

    private void applyAdminArticleFields(HealthArticle article, Map<String, Object> payload) {
        if (payload.get("title") != null) {
            article.setTitle(text(payload.get("title")));
        }
        if (payload.get("summary") != null) {
            article.setSummary(text(payload.get("summary")));
        }
        if (payload.get("cat") != null) {
            article.setCategory(text(payload.get("cat")));
        }
        if (payload.get("author") != null) {
            article.setAuthor(text(payload.get("author")));
        }
        if (payload.get("tags") != null) {
            article.setTags(joinText(payload.get("tags")));
        }
        if (payload.get("body") != null) {
            article.setContent(bodyText(payload.get("body")));
        } else if (payload.get("content") != null) {
            article.setContent(text(payload.get("content")));
        }
        if (payload.get("status") != null) {
            article.setStatus(integerValue(payload.get("status")));
        }
    }

    private void applyAdminIngredientFields(Ingredient ingredient, Map<String, Object> payload) {
        if (payload.get("name") != null) {
            ingredient.setName(text(payload.get("name")));
        }
        if (payload.get("cat") != null) {
            ingredient.setCategory(text(payload.get("cat")));
        }
        if (payload.get("desc") != null) {
            ingredient.setDescription(text(payload.get("desc")));
        }
        Object calories = payload.containsKey("kcal") ? payload.get("kcal") : payload.get("caloriesPer100g");
        if (calories != null) {
            ingredient.setCaloriesPer100g(number(calories));
        }
        Object protein = payload.containsKey("p") ? payload.get("p") : payload.get("proteinPer100g");
        if (protein != null) {
            ingredient.setProteinPer100g(number(protein));
        }
        Object carbs = payload.containsKey("c") ? payload.get("c") : payload.get("carbsPer100g");
        if (carbs != null) {
            ingredient.setCarbsPer100g(number(carbs));
        }
        Object fat = payload.containsKey("f") ? payload.get("f") : payload.get("fatPer100g");
        if (fat != null) {
            ingredient.setFatPer100g(number(fat));
        }
        if (payload.get("fiber") != null) {
            ingredient.setFiberPer100g(number(payload.get("fiber")));
        }
        if (payload.get("status") != null) {
            ingredient.setStatus(integerValue(payload.get("status")));
        }
    }

    private String text(Object value) {
        return value == null ? "" : String.valueOf(value);
    }

    private Double number(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        try {
            return Double.parseDouble(String.valueOf(value).trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private Integer integerValue(Object value) {
        Double num = number(value);
        return num == null ? null : num.intValue();
    }

    private String joinText(Object value) {
        if (value instanceof List) {
            return ((List<?>) value).stream()
                .filter(item -> item != null && !String.valueOf(item).isBlank())
                .map(String::valueOf)
                .collect(Collectors.joining("、"));
        }
        return text(value);
    }

    private String instructionsText(Object value) {
        if (value instanceof List) {
            try {
                return objectMapper.writeValueAsString(value);
            } catch (Exception e) {
                return "[]";
            }
        }
        return text(value);
    }

    private String bodyText(Object value) {
        if (value instanceof List) {
            List<String> lines = new ArrayList<>();
            for (Object item : (List<?>) value) {
                if (item instanceof Map) {
                    Object text = ((Map<?, ?>) item).get("text");
                    if (text != null && !String.valueOf(text).isBlank()) {
                        lines.add(String.valueOf(text));
                    }
                }
            }
            return String.join("\n\n", lines);
        }
        return text(value);
    }

    private boolean matchesText(String keyword, String... values) {
        if (keyword == null || keyword.isBlank()) {
            return true;
        }
        for (String value : values) {
            if (value != null && value.toLowerCase().contains(keyword)) {
                return true;
            }
        }
        return false;
    }

    private User requireAdmin(Principal principal) {
        if (principal == null) {
            throw new RuntimeException("未登录或登录已过期");
        }
        User currentUser = userService.findById(Long.parseLong(principal.getName()));
        if (!userService.isAdmin(currentUser)) {
            throw new RuntimeException("无权限执行该操作");
        }
        return currentUser;
    }

    private ResponseEntity<?> successResponse(String message, Object data) {
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", message);
        response.put("data", data);
        return ResponseEntity.ok(response);
    }

    private ResponseEntity<Map<String, Object>> badRequestResponse(String message) {
        Map<String, Object> response = new HashMap<>();
        response.put("code", 400);
        response.put("message", message);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
    }
}
