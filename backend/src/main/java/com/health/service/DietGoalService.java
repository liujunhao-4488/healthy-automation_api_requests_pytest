package com.health.service;

import com.health.entity.DietGoal;
import com.health.dto.DietGoalDTO;

public interface DietGoalService {

    // 保存或更新饮食目标
    DietGoal saveOrUpdateDietGoal(Long userId, DietGoalDTO dietGoalDTO);

    // 根据用户ID获取饮食目标
    DietGoal getDietGoalByUserId(Long userId);

    // 根据健康信息和目标类型计算目标卡路里
    double calculateTargetCalories(double height, double weight, int age, String gender, String goalType);

}
