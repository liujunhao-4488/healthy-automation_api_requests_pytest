package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.ArticleComment;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface ArticleCommentMapper extends BaseMapper<ArticleComment> {

    @Select("SELECT id, article_id, user_id, parent_id, reply_to_user_id, content, is_deleted, create_time, update_time " +
        "FROM article_comment WHERE article_id = #{articleId} AND is_deleted = 0 ORDER BY create_time DESC")
    List<ArticleComment> selectByArticleId(Long articleId);
}
