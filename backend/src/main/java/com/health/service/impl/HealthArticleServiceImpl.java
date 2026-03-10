package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.entity.HealthArticle;
import com.health.entity.UserReadRecord;
import com.health.mapper.HealthArticleMapper;
import com.health.mapper.UserReadRecordMapper;
import com.health.service.HealthArticleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.ArrayList;
import java.util.Date;

/**
 * 健康文章服务实现类
 */
@Service
public class HealthArticleServiceImpl implements HealthArticleService {

    @Autowired
    private HealthArticleMapper healthArticleMapper;

    @Autowired
    private UserReadRecordMapper userReadRecordMapper;

    @Override
    public List<HealthArticle> getAllArticles() {
        return healthArticleMapper.selectList(null);
    }

    @Override
    public HealthArticle getArticleById(Long id) {
        return healthArticleMapper.selectById(id);
    }

    @Override
    public HealthArticle getHealthArticleById(Long id, Long userId) {
        HealthArticle article = healthArticleMapper.selectById(id);
        if (article != null && userId != null) {
            // 增加阅读计数
            incrementArticleReadCount(id);
        }
        return article;
    }

    @Override
    public List<HealthArticle> getArticlesByCategory(String category) {
        return healthArticleMapper.selectByCategory(category);
    }

    @Override
    public List<HealthArticle> getHealthArticles(String category, Integer page, Integer pageSize) {
        if (category != null) {
            return healthArticleMapper.selectByCategory(category);
        } else {
            return healthArticleMapper.selectList(null);
        }
    }

    @Override
    public List<HealthArticle> getArticlesByTag(String tag) {
        return healthArticleMapper.selectByTag(tag);
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
        QueryWrapper<HealthArticle> wrapper = new QueryWrapper<>();
        wrapper.like("title", keyword).or().like("content", keyword).or().like("tags", keyword);
        return healthArticleMapper.selectList(wrapper);
    }

    @Override
    public List<HealthArticle> searchHealthArticles(String keyword, Integer page, Integer pageSize) {
        QueryWrapper<HealthArticle> wrapper = new QueryWrapper<>();
        wrapper.like("title", keyword).or().like("content", keyword).or().like("tags", keyword);
        return healthArticleMapper.selectList(wrapper);
    }

    @Override
    public HealthArticle saveArticle(HealthArticle article) {
        healthArticleMapper.insert(article);
        return article;
    }

    @Override
    public HealthArticle updateArticle(HealthArticle article) {
        healthArticleMapper.updateById(article);
        return article;
    }

    @Override
    public boolean deleteArticle(Long id) {
        return healthArticleMapper.deleteById(id) > 0;
    }

    @Transactional
    @Override
    public UserReadRecord recordArticleRead(Long userId, Long articleId, Integer readDuration) {
        // 检查是否已存在阅读记录
        UserReadRecord existingRecord = userReadRecordMapper.selectByUserIdAndArticleId(userId, articleId);
        
        if (existingRecord != null) {
            // 更新阅读记录
            existingRecord.setReadTime(new Date());
            existingRecord.setReadDuration(readDuration);
            userReadRecordMapper.updateById(existingRecord);
            return existingRecord;
        } else {
            // 创建新的阅读记录
            UserReadRecord record = new UserReadRecord();
            record.setUserId(userId);
            record.setArticleId(articleId);
            record.setReadTime(new Date());
            record.setReadDuration(readDuration);
            userReadRecordMapper.insert(record);
            
            // 增加文章阅读计数
            incrementArticleReadCount(articleId);
            
            return record;
        }
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
    public List<HealthArticle> getRecommendedArticles(Long userId, int limit) {
        // 这里可以集成个性化推荐算法
        // 暂时返回热门文章
        return healthArticleMapper.selectHotArticles(limit);
    }

    @Override
    public int incrementArticleReadCount(Long articleId) {
        HealthArticle article = healthArticleMapper.selectById(articleId);
        if (article != null) {
            int newCount = (article.getReadCount() != null ? article.getReadCount() : 0) + 1;
            article.setReadCount(newCount);
            healthArticleMapper.updateById(article);
            return newCount;
        }
        return 0;
    }
}
