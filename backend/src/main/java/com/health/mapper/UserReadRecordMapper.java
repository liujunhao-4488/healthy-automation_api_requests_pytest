package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.UserReadRecord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface UserReadRecordMapper extends BaseMapper<UserReadRecord> {

    @Select("SELECT * FROM user_read_record " +
        "WHERE user_id = #{userId} " +
        "ORDER BY read_time DESC " +
        "LIMIT #{limit}")
    List<UserReadRecord> selectByUserId(@Param("userId") Long userId, @Param("limit") int limit);

    @Select("SELECT * FROM user_read_record " +
        "WHERE user_id = #{userId} AND article_id = #{articleId} " +
        "LIMIT 1")
    UserReadRecord selectByUserIdAndArticleId(@Param("userId") Long userId, @Param("articleId") Long articleId);

    @Select("SELECT COUNT(*) FROM user_read_record WHERE article_id = #{articleId}")
    int selectReadCountByArticleId(@Param("articleId") Long articleId);
}
