package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.entity.ArticleComment;
import com.health.entity.HealthArticle;
import com.health.entity.UserDietPreference;
import com.health.entity.UserArticleLike;
import com.health.entity.UserReadRecord;
import com.health.mapper.ArticleCommentMapper;
import com.health.mapper.HealthArticleMapper;
import com.health.mapper.UserArticleLikeMapper;
import com.health.mapper.UserDietPreferenceMapper;
import com.health.mapper.UserReadRecordMapper;
import com.health.service.HealthArticleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class HealthArticleServiceImpl implements HealthArticleService {

    @Autowired
    private HealthArticleMapper healthArticleMapper;

    @Autowired
    private UserReadRecordMapper userReadRecordMapper;

    @Autowired
    private UserDietPreferenceMapper userDietPreferenceMapper;

    @Autowired
    private UserArticleLikeMapper userArticleLikeMapper;

    @Autowired
    private ArticleCommentMapper articleCommentMapper;

    @Override
    public List<HealthArticle> getAllArticles() {
        return healthArticleMapper.selectList(new QueryWrapper<HealthArticle>().orderByDesc("publish_date", "create_time"));
    }

    @Override
    public HealthArticle getArticleById(Long id) {
        return healthArticleMapper.selectById(id);
    }

    @Override
    public HealthArticle getHealthArticleById(Long id, Long userId) {
        return healthArticleMapper.selectById(id);
    }

    @Override
    public List<HealthArticle> getArticlesByCategory(String category) {
        if (category == null || category.trim().isEmpty()) {
            return getPublishedArticles();
        }
        return healthArticleMapper.selectByCategory(category.trim());
    }

    @Override
    public List<HealthArticle> getHealthArticles(String category, Integer page, Integer pageSize) {
        List<HealthArticle> articles = getArticlesByCategory(category);
        return paginate(articles, page, pageSize);
    }

    @Override
    public List<HealthArticle> getArticlesByTag(String tag) {
        if (tag == null || tag.trim().isEmpty()) {
            return getPublishedArticles();
        }
        return healthArticleMapper.selectByTag(tag.trim());
    }

    @Override
    public List<HealthArticle> getHotArticles(int limit) {
        return healthArticleMapper.selectHotArticles(limit);
    }

    @Override
    public List<HealthArticle> getLatestArticles(int limit) {
        return healthArticleMapper.selectLatestArticles(limit);
    }

    @Override
    public List<HealthArticle> searchArticles(String keyword) {
        return filterByKeyword(getPublishedArticles(), keyword);
    }

    @Override
    public List<HealthArticle> searchHealthArticles(String keyword, Integer page, Integer pageSize) {
        return paginate(searchArticles(keyword), page, pageSize);
    }

    @Override
    public HealthArticle saveArticle(HealthArticle article) {
        prepareArticle(article);
        healthArticleMapper.insert(article);
        return healthArticleMapper.selectById(article.getId());
    }

    @Override
    public HealthArticle updateArticle(HealthArticle article) {
        prepareArticle(article);
        healthArticleMapper.updateById(article);
        return healthArticleMapper.selectById(article.getId());
    }

    @Override
    public boolean deleteArticle(Long id) {
        return healthArticleMapper.deleteById(id) > 0;
    }

    @Transactional
    @Override
    public UserReadRecord recordArticleRead(Long userId, Long articleId, Integer readDuration, Integer scrollPercent) {
        UserReadRecord existingRecord = userReadRecordMapper.selectByUserIdAndArticleId(userId, articleId);
        int safeReadDuration = sanitizeReadDuration(readDuration);
        int safeScrollPercent = sanitizeScrollPercent(scrollPercent);
        int isFinished = isReadFinished(articleId, safeReadDuration, safeScrollPercent) ? 1 : 0;

        if (existingRecord != null) {
            existingRecord.setReadTime(new Date());
            existingRecord.setReadDuration(Math.max(safeReadDuration, safeInteger(existingRecord.getReadDuration())));
            existingRecord.setScrollPercent(Math.max(safeScrollPercent, safeInteger(existingRecord.getScrollPercent())));
            existingRecord.setIsFinished(Math.max(isFinished, safeInteger(existingRecord.getIsFinished())));
            userReadRecordMapper.updateById(existingRecord);
            syncArticleStats(articleId);
            return existingRecord;
        }

        UserReadRecord record = new UserReadRecord();
        record.setUserId(userId);
        record.setArticleId(articleId);
        record.setReadTime(new Date());
        record.setReadDuration(safeReadDuration);
        record.setScrollPercent(safeScrollPercent);
        record.setIsFinished(isFinished);
        userReadRecordMapper.insert(record);
        syncArticleStats(articleId);
        return record;
    }

    @Transactional
    @Override
    public UserReadRecord recordArticleRead(Long userId, Long articleId) {
        return recordArticleRead(userId, articleId, null, null);
    }

    @Override
    public List<Map<String, Object>> getUserReadHistory(Long userId, int limit) {
        List<UserReadRecord> records = userReadRecordMapper.selectByUserId(userId, limit);
        List<Map<String, Object>> articles = new ArrayList<>();

        for (UserReadRecord record : records) {
            HealthArticle article = healthArticleMapper.selectById(record.getArticleId());
            if (article != null) {
                Map<String, Object> item = new HashMap<>();
                item.put("article", article);
                item.put("readTime", record.getReadTime());
                item.put("readDuration", safeInteger(record.getReadDuration()));
                item.put("scrollPercent", safeInteger(record.getScrollPercent()));
                item.put("finished", Integer.valueOf(1).equals(record.getIsFinished()));
                articles.add(item);
            }
        }

        return articles;
    }

    @Override
    public List<HealthArticle> getRecommendedArticles(Long userId, Integer limit) {
        List<HealthArticle> articles = getPublishedArticles();
        if (articles.isEmpty()) {
            return new ArrayList<>();
        }

        UserDietPreference preference = null;
        if (userId != null) {
            preference = userDietPreferenceMapper.selectOne(
                new QueryWrapper<UserDietPreference>().eq("user_id", userId).last("LIMIT 1")
            );
        }

        Map<Long, UserReadRecord> readRecordMap = loadRecentReadRecords(userId, 20);
        final UserDietPreference finalPreference = preference;
        final String readPreferenceText = buildReadPreferenceText(readRecordMap);
        final Set<Long> readArticleIds = readRecordMap.keySet();
        articles.sort(
            Comparator.comparingDouble(
                (HealthArticle article) -> scoreArticle(article, finalPreference, readPreferenceText, readArticleIds.contains(article.getId()))
            ).reversed()
        );
        articles.forEach(article -> article.setRecommendReason(
            buildRecommendReason(article, finalPreference, readPreferenceText, readArticleIds.contains(article.getId()))
        ));
        if (limit == null || limit <= 0) {
            return articles;
        }
        return new ArrayList<>(articles.subList(0, Math.min(limit, articles.size())));
    }

    @Override
    public void syncArticleStats(Long articleId) {
        if (articleId == null) {
            return;
        }

        HealthArticle article = healthArticleMapper.selectById(articleId);
        if (article == null) {
            return;
        }

        QueryWrapper<UserArticleLike> likeWrapper = new QueryWrapper<>();
        likeWrapper.eq("article_id", articleId);

        QueryWrapper<ArticleComment> commentWrapper = new QueryWrapper<>();
        commentWrapper.eq("article_id", articleId).eq("is_deleted", 0);

        article.setReadCount(userReadRecordMapper.selectReadCountByArticleId(articleId));
        article.setLikeCount(Math.toIntExact(userArticleLikeMapper.selectCount(likeWrapper)));
        article.setCommentCount(Math.toIntExact(articleCommentMapper.selectCount(commentWrapper)));
        healthArticleMapper.updateById(article);
    }

    private List<HealthArticle> getPublishedArticles() {
        return healthArticleMapper.selectList(
            new QueryWrapper<HealthArticle>()
                .eq("status", 1)
                .orderByDesc("publish_date", "create_time")
        );
    }

    private List<HealthArticle> filterByKeyword(List<HealthArticle> source, String keyword) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return source;
        }

        String normalizedKeyword = keyword.trim().toLowerCase(Locale.ROOT);
        List<HealthArticle> result = new ArrayList<>();
        for (HealthArticle article : source) {
            String haystack = String.join(
                " ",
                normalize(article.getTitle()),
                normalize(article.getSummary()),
                normalize(article.getContent()),
                normalize(article.getCategory()),
                normalize(article.getTags()),
                normalize(article.getAuthor())
            );
            if (haystack.contains(normalizedKeyword)) {
                result.add(article);
            }
        }
        return result;
    }

    private List<HealthArticle> paginate(List<HealthArticle> source, Integer page, Integer pageSize) {
        int currentPage = page == null || page < 1 ? 1 : page;
        int size = pageSize == null || pageSize < 1 ? source.size() : pageSize;
        int start = (currentPage - 1) * size;
        if (start >= source.size()) {
            return new ArrayList<>();
        }
        int end = Math.min(start + size, source.size());
        return new ArrayList<>(source.subList(start, end));
    }

    private void prepareArticle(HealthArticle article) {
        if (article.getPublishDate() == null) {
            article.setPublishDate(new Date());
        }
        if (article.getStatus() == null) {
            article.setStatus(1);
        }
        if (article.getReadCount() == null) {
            article.setReadCount(0);
        }
        if (article.getLikeCount() == null) {
            article.setLikeCount(0);
        }
        if (article.getCommentCount() == null) {
            article.setCommentCount(0);
        }
        if ((article.getSummary() == null || article.getSummary().trim().isEmpty()) && article.getContent() != null) {
            String content = article.getContent().trim().replaceAll("\\s+", " ");
            article.setSummary(content.length() > 120 ? content.substring(0, 120) : content);
        }
    }

    private double scoreArticle(HealthArticle article, UserDietPreference preference, String readPreferenceText, boolean hasRead) {
        double score = article.getReadCount() == null ? 0 : article.getReadCount();
        score += article.getLikeCount() == null ? 0 : article.getLikeCount() * 1.5;
        score += article.getCommentCount() == null ? 0 : article.getCommentCount() * 1.2;
        score += matchTokens(normalizeArticleText(article), readPreferenceText, 6);

        if (hasRead) {
            score -= 18;
        }

        if (preference == null) {
            return score;
        }

        String text = normalizeArticleText(article);

        score += matchTokens(text, preference.getDietType(), 20);
        score += matchTokens(text, preference.getFavorites(), 12);
        score -= matchTokens(text, preference.getDislikes(), 8);
        score -= matchTokens(text, preference.getAllergies(), 10);
        return score;
    }

    private double matchTokens(String text, String source, double hitScore) {
        if (source == null || source.trim().isEmpty()) {
            return 0;
        }

        double score = 0;
        for (String token : source.replace("，", ",").replace("、", ",").split(",")) {
            String item = normalize(token);
            if (!item.isEmpty() && text.contains(item)) {
                score += hitScore;
            }
        }
        return score;
    }

    private String buildRecommendReason(HealthArticle article, UserDietPreference preference, String readPreferenceText, boolean hasRead) {
        String text = normalizeArticleText(article);
        List<String> reasons = new ArrayList<>();

        if (preference != null) {
            String dietType = firstMatchedToken(text, preference.getDietType());
            if (!dietType.isEmpty()) {
                reasons.add("匹配你的饮食目标：" + dietType);
            }

            String favorite = firstMatchedToken(text, preference.getFavorites());
            if (!favorite.isEmpty()) {
                reasons.add("包含你偏好的内容：" + favorite);
            }
        }

        if (!firstMatchedToken(text, readPreferenceText).isEmpty()) {
            reasons.add("与你最近阅读的主题相近");
        }

        int heat = safeInteger(article.getReadCount()) + safeInteger(article.getLikeCount()) * 2 + safeInteger(article.getCommentCount());
        if (heat >= 20) {
            reasons.add("近期阅读和互动较高");
        }

        if (hasRead && reasons.isEmpty()) {
            reasons.add("你之前浏览过，可继续深入阅读");
        }

        if (reasons.isEmpty()) {
            if (article.getGoalType() != null && !article.getGoalType().trim().isEmpty()) {
                reasons.add("适合关注" + article.getGoalType().trim() + "的人群");
            } else if (article.getCategory() != null && !article.getCategory().trim().isEmpty()) {
                reasons.add("来自" + article.getCategory().trim() + "分类的精选内容");
            } else {
                reasons.add("根据热度和发布时间综合推荐");
            }
        }

        return reasons.stream().limit(2).collect(Collectors.joining("，"));
    }

    private String firstMatchedToken(String text, String source) {
        if (source == null || source.trim().isEmpty()) {
            return "";
        }

        for (String token : splitTokens(source)) {
            String item = normalize(token);
            if (!item.isEmpty() && text.contains(item)) {
                return token.trim();
            }
        }
        return "";
    }

    private String[] splitTokens(String source) {
        return source.replace("[", "")
            .replace("]", "")
            .replace("\"", "")
            .split("[,，、;；\\s]+");
    }

    private Map<Long, UserReadRecord> loadRecentReadRecords(Long userId, int limit) {
        if (userId == null) {
            return new HashMap<>();
        }

        return userReadRecordMapper.selectByUserId(userId, limit).stream()
            .filter(item -> item.getArticleId() != null)
            .collect(Collectors.toMap(UserReadRecord::getArticleId, item -> item, (left, right) -> left));
    }

    private String buildReadPreferenceText(Map<Long, UserReadRecord> readRecordMap) {
        if (readRecordMap.isEmpty()) {
            return "";
        }

        return readRecordMap.keySet().stream()
            .map(healthArticleMapper::selectById)
            .filter(Objects::nonNull)
            .sorted(Comparator.comparingInt((HealthArticle article) -> {
                UserReadRecord record = readRecordMap.get(article.getId());
                return safeInteger(record == null ? null : record.getIsFinished()) * 100 + safeInteger(record == null ? null : record.getReadDuration());
            }).reversed())
            .limit(8)
            .map(article -> String.join(
                ",",
                normalize(article.getCategory()),
                normalize(article.getTags()),
                normalize(article.getGoalType()),
                normalize(article.getSuitableFor())
            ))
            .collect(Collectors.joining(","));
    }

    private String normalizeArticleText(HealthArticle article) {
        return String.join(
            " ",
            normalize(article.getTitle()),
            normalize(article.getSummary()),
            normalize(article.getCategory()),
            normalize(article.getTags()),
            normalize(article.getContent()),
            normalize(article.getSuitableFor()),
            normalize(article.getGoalType())
        );
    }

    private boolean isReadFinished(Long articleId, int readDuration, int scrollPercent) {
        if (scrollPercent < 90) {
            return false;
        }

        HealthArticle article = healthArticleMapper.selectById(articleId);
        if (article == null) {
            return false;
        }

        int estimatedDuration = estimateReadingDuration(article);
        int finishThreshold = Math.max(15, (int) Math.ceil(estimatedDuration * 0.6));
        return readDuration >= finishThreshold;
    }

    private int estimateReadingDuration(HealthArticle article) {
        String content = String.join(
            "",
            normalize(article.getTitle()),
            normalize(article.getSummary()),
            normalize(article.getContent())
        );
        int textLength = content.replaceAll("\\s+", "").length();
        if (textLength <= 0) {
            return 15;
        }

        return Math.max(15, (int) Math.ceil(textLength / 5.0));
    }

    private int sanitizeReadDuration(Integer readDuration) {
        return Math.max(0, safeInteger(readDuration));
    }

    private int sanitizeScrollPercent(Integer scrollPercent) {
        return Math.max(0, Math.min(100, safeInteger(scrollPercent)));
    }

    private int safeInteger(Integer value) {
        return value == null ? 0 : value;
    }

    private String normalize(String text) {
        return text == null ? "" : text.trim().toLowerCase(Locale.ROOT);
    }
}
