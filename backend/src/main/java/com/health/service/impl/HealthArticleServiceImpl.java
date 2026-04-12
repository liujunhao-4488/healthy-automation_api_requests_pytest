package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.entity.HealthArticle;
import com.health.entity.UserDietPreference;
import com.health.entity.UserReadRecord;
import com.health.mapper.HealthArticleMapper;
import com.health.mapper.UserDietPreferenceMapper;
import com.health.mapper.UserReadRecordMapper;
import com.health.service.HealthArticleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;

@Service
public class HealthArticleServiceImpl implements HealthArticleService {

    @Autowired
    private HealthArticleMapper healthArticleMapper;

    @Autowired
    private UserReadRecordMapper userReadRecordMapper;

    @Autowired
    private UserDietPreferenceMapper userDietPreferenceMapper;

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
        HealthArticle article = healthArticleMapper.selectById(id);
        if (article == null) {
            return null;
        }

        if (userId != null) {
            int latestReadCount = incrementArticleReadCount(id);
            article.setReadCount(latestReadCount);
        }

        return article;
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
    public UserReadRecord recordArticleRead(Long userId, Long articleId, Integer readDuration) {
        UserReadRecord existingRecord = userReadRecordMapper.selectByUserIdAndArticleId(userId, articleId);

        if (existingRecord != null) {
            existingRecord.setReadTime(new Date());
            existingRecord.setReadDuration(readDuration);
            userReadRecordMapper.updateById(existingRecord);
            return existingRecord;
        }

        UserReadRecord record = new UserReadRecord();
        record.setUserId(userId);
        record.setArticleId(articleId);
        record.setReadTime(new Date());
        record.setReadDuration(readDuration);
        userReadRecordMapper.insert(record);
        incrementArticleReadCount(articleId);
        return record;
    }

    @Transactional
    @Override
    public UserReadRecord recordArticleRead(Long userId, Long articleId) {
        return recordArticleRead(userId, articleId, null);
    }

    @Override
    public List<HealthArticle> getUserReadHistory(Long userId, int limit) {
        List<UserReadRecord> records = userReadRecordMapper.selectByUserId(userId, limit);
        List<HealthArticle> articles = new ArrayList<>();

        for (UserReadRecord record : records) {
            HealthArticle article = healthArticleMapper.selectById(record.getArticleId());
            if (article != null) {
                articles.add(article);
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

        final UserDietPreference finalPreference = preference;
        articles.sort(Comparator.comparingDouble((HealthArticle article) -> scoreArticle(article, finalPreference)).reversed());
        if (limit == null || limit <= 0) {
            return articles;
        }
        return new ArrayList<>(articles.subList(0, Math.min(limit, articles.size())));
    }

    @Override
    public int incrementArticleReadCount(Long articleId) {
        HealthArticle article = healthArticleMapper.selectById(articleId);
        if (article == null) {
            return 0;
        }

        int newCount = (article.getReadCount() == null ? 0 : article.getReadCount()) + 1;
        article.setReadCount(newCount);
        healthArticleMapper.updateById(article);
        return newCount;
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
        if (article.getShareCount() == null) {
            article.setShareCount(0);
        }
        if ((article.getSummary() == null || article.getSummary().trim().isEmpty()) && article.getContent() != null) {
            String content = article.getContent().trim().replaceAll("\\s+", " ");
            article.setSummary(content.length() > 120 ? content.substring(0, 120) : content);
        }
    }

    private double scoreArticle(HealthArticle article, UserDietPreference preference) {
        double score = article.getReadCount() == null ? 0 : article.getReadCount();
        score += article.getLikeCount() == null ? 0 : article.getLikeCount() * 1.5;
        score += article.getCommentCount() == null ? 0 : article.getCommentCount() * 1.2;

        if (preference == null) {
            return score;
        }

        String text = String.join(
            " ",
            normalize(article.getTitle()),
            normalize(article.getSummary()),
            normalize(article.getCategory()),
            normalize(article.getTags()),
            normalize(article.getContent()),
            normalize(article.getSuitableFor()),
            normalize(article.getGoalType())
        );

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

    private String normalize(String text) {
        return text == null ? "" : text.trim().toLowerCase(Locale.ROOT);
    }
}
