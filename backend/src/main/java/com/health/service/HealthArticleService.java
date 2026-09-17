package com.health.service;

import com.health.entity.HealthArticle;
import com.health.entity.UserReadRecord;

import java.util.Map;
import java.util.List;

/**
 * 健康文章服务接口
 */
public interface HealthArticleService {

    /**
     * 获取所有文章
     * @return 文章列表
     */
    List<HealthArticle> getAllArticles();

    /**
     * 根据ID获取文章
     * @param id 文章ID
     * @return 文章信息
     */
    HealthArticle getArticleById(Long id);

    /**
     * 根据ID获取文章（支持用户ID参数）
     * @param id 文章ID
     * @param userId 用户ID
     * @return 文章信息
     */
    HealthArticle getHealthArticleById(Long id, Long userId);

    /**
     * 根据分类获取文章
     * @param category 文章分类
     * @return 文章列表
     */
    List<HealthArticle> getArticlesByCategory(String category);

    /**
     * 根据分类、页码、每页大小获取文章
     * @param category 文章分类
     * @param page 页码
     * @param pageSize 每页大小
     * @return 文章列表
     */
    List<HealthArticle> getHealthArticles(String category, Integer page, Integer pageSize);

    /**
     * 根据标签获取文章
     * @param tag 标签名称
     * @return 文章列表
     */
    List<HealthArticle> getArticlesByTag(String tag);

    /**
     * 获取热门文章
     * @param limit 限制数量
     * @return 热门文章列表
     */
    List<HealthArticle> getHotArticles(int limit);

    /**
     * 获取最新文章
     * @param limit 限制数量
     * @return 最新文章列表
     */
    List<HealthArticle> getLatestArticles(int limit);

    /**
     * 搜索文章
     * @param keyword 搜索关键词
     * @return 文章列表
     */
    List<HealthArticle> searchArticles(String keyword);

    /**
     * 搜索文章（支持分页）
     * @param keyword 搜索关键词
     * @param page 页码
     * @param pageSize 每页大小
     * @return 文章列表
     */
    List<HealthArticle> searchHealthArticles(String keyword, Integer page, Integer pageSize);

    /**
     * 保存文章
     * @param article 文章信息
     * @return 保存后的文章
     */
    HealthArticle saveArticle(HealthArticle article);

    /**
     * 更新文章
     * @param article 文章信息
     * @return 更新后的文章
     */
    HealthArticle updateArticle(HealthArticle article);

    /**
     * 删除文章
     * @param id 文章ID
     * @return 是否删除成功
     */
    boolean deleteArticle(Long id);

    /**
     * 记录用户阅读文章
     * @param userId 用户ID
     * @param articleId 文章ID
     * @param readDuration 阅读时长（秒）
     * @return 阅读记录
     */
    UserReadRecord recordArticleRead(Long userId, Long articleId, Integer readDuration, Integer scrollPercent);

    /**
     * 记录用户阅读文章（简化版）
     * @param userId 用户ID
     * @param articleId 文章ID
     * @return 阅读记录
     */
    UserReadRecord recordArticleRead(Long userId, Long articleId);

    /**
     * 获取用户阅读历史
     * @param userId 用户ID
     * @param limit 限制数量
     * @return 阅读历史列表
     */
    List<Map<String, Object>> getUserReadHistory(Long userId, int limit);

    /**
     * 获取个性化推荐文章
     * @param userId 用户ID
     * @param limit 限制数量，小于等于 0 时返回完整推荐列表
     * @return 推荐文章列表
     */
    List<HealthArticle> getRecommendedArticles(Long userId, Integer limit);

    /**
     * 同步文章冗余统计字段
     * @param articleId 文章ID
     */
    void syncArticleStats(Long articleId);
}
