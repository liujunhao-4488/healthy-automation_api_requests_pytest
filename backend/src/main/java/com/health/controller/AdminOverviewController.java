package com.health.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
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
import com.health.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
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

    private void requireAdmin(Principal principal) {
        if (principal == null) {
            throw new RuntimeException("未登录或登录已过期");
        }
        User currentUser = userService.findById(Long.parseLong(principal.getName()));
        if (!userService.isAdmin(currentUser)) {
            throw new RuntimeException("无权限执行该操作");
        }
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
