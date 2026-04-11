package com.health.mapper;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.HealthInfoHistory;

import java.util.List;

public interface HealthInfoHistoryMapper extends BaseMapper<HealthInfoHistory> {

    default List<HealthInfoHistory> findByUserId(Long userId) {
        return selectList(
            new QueryWrapper<HealthInfoHistory>()
                .eq("user_id", userId)
                .orderByAsc("create_time", "id")
        );
    }

    default HealthInfoHistory findLatestByUserId(Long userId) {
        return selectOne(
            new QueryWrapper<HealthInfoHistory>()
                .eq("user_id", userId)
                .orderByDesc("create_time", "id")
                .last("limit 1")
        );
    }
}
