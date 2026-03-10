package com.health.mapper;

import com.health.entity.DietGoal;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

public interface DietGoalMapper extends BaseMapper<DietGoal> {

    default DietGoal findByUserId(Long userId) {
        return selectOne(new QueryWrapper<DietGoal>().eq("user_id", userId).orderByDesc("create_time").last("LIMIT 1"));
    }

}
