package com.health.mapper;

import com.health.entity.HealthInfo;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

public interface HealthInfoMapper extends BaseMapper<HealthInfo> {

    default HealthInfo findByUserId(Long userId) {
        return selectOne(new QueryWrapper<HealthInfo>().eq("user_id", userId));
    }

}
