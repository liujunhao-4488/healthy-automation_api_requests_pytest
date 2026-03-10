package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.UserReadRecord;
import java.util.List;

/**
 * 用户阅读记录Mapper接口
 */
public interface UserReadRecordMapper extends BaseMapper<UserReadRecord> {

    /**
     * 查询用户阅读记录
     * @param userId 用户ID
     * @param limit 限制数量
     * @return 阅读记录列表
     */
    List<UserReadRecord> selectByUserId(Long userId, int limit);

    /**
     * 查询用户是否阅读过某篇文章
     * @param userId 用户ID
     * @param articleId 文章ID
     * @return 阅读记录
     */
    UserReadRecord selectByUserIdAndArticleId(Long userId, Long articleId);

    /**
     * 查询文章的阅读次数
     * @param articleId 文章ID
     * @return 阅读次数
     */
    int selectReadCountByArticleId(Long articleId);
}
