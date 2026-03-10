package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.HealthArticle;
import java.util.List;

/**
 * 健康文章Mapper接口
 */
public interface HealthArticleMapper extends BaseMapper<HealthArticle> {

    /**
     * 根据分类查询文章
     * @param category 文章分类
     * @return 文章列表
     */
    List<HealthArticle> selectByCategory(String category);

    /**
     * 根据标签查询文章
     * @param tag 标签名称
     * @return 文章列表
     */
    List<HealthArticle> selectByTag(String tag);

    /**
     * 查询热门文章
     * @param limit 限制数量
     * @return 文章列表
     */
    List<HealthArticle> selectHotArticles(int limit);

    /**
     * 查询最新文章
     * @param limit 限制数量
     * @return 文章列表
     */
    List<HealthArticle> selectLatestArticles(int limit);
}
