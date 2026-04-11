package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.HealthArticle;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface HealthArticleMapper extends BaseMapper<HealthArticle> {

    @Select("SELECT * FROM health_article " +
        "WHERE status = 1 AND category = #{category} " +
        "ORDER BY publish_date DESC, create_time DESC")
    List<HealthArticle> selectByCategory(@Param("category") String category);

    @Select("SELECT * FROM health_article " +
        "WHERE status = 1 AND tags LIKE CONCAT('%', #{tag}, '%') " +
        "ORDER BY publish_date DESC, create_time DESC")
    List<HealthArticle> selectByTag(@Param("tag") String tag);

    @Select("SELECT * FROM health_article " +
        "WHERE status = 1 " +
        "ORDER BY read_count DESC, like_count DESC, publish_date DESC " +
        "LIMIT #{limit}")
    List<HealthArticle> selectHotArticles(@Param("limit") int limit);

    @Select("SELECT * FROM health_article " +
        "WHERE status = 1 " +
        "ORDER BY publish_date DESC, create_time DESC " +
        "LIMIT #{limit}")
    List<HealthArticle> selectLatestArticles(@Param("limit") int limit);
}
