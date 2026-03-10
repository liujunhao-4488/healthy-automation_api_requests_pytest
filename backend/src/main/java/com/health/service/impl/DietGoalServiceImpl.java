package com.health.service.impl;

import com.health.entity.DietGoal;
import com.health.dto.DietGoalDTO;
import com.health.service.DietGoalService;
import com.health.mapper.DietGoalMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class DietGoalServiceImpl implements DietGoalService {

    @Autowired
    private DietGoalMapper dietGoalMapper;

    @Override
    public DietGoal saveOrUpdateDietGoal(Long userId, DietGoalDTO dietGoalDTO) {
        // 查找用户是否已有饮食目标
        DietGoal existingDietGoal = dietGoalMapper.findByUserId(userId);

        if (existingDietGoal != null) {
            // 更新现有饮食目标
            existingDietGoal.setGoalType(dietGoalDTO.getGoalType());
            existingDietGoal.setTargetCalories(dietGoalDTO.getTargetCalories());
            existingDietGoal.setProteinRatio(dietGoalDTO.getProteinRatio());
            existingDietGoal.setCarbsRatio(dietGoalDTO.getCarbsRatio());
            existingDietGoal.setFatRatio(dietGoalDTO.getFatRatio());
            existingDietGoal.setStartDate(dietGoalDTO.getStartDate());
            existingDietGoal.setEndDate(dietGoalDTO.getEndDate());
            dietGoalMapper.updateById(existingDietGoal);
            return existingDietGoal;
        } else {
            // 创建新的饮食目标
            DietGoal newDietGoal = new DietGoal();
            newDietGoal.setUserId(userId);
            newDietGoal.setGoalType(dietGoalDTO.getGoalType());
            newDietGoal.setTargetCalories(dietGoalDTO.getTargetCalories());
            newDietGoal.setProteinRatio(dietGoalDTO.getProteinRatio());
            newDietGoal.setCarbsRatio(dietGoalDTO.getCarbsRatio());
            newDietGoal.setFatRatio(dietGoalDTO.getFatRatio());
            newDietGoal.setStartDate(dietGoalDTO.getStartDate());
            newDietGoal.setEndDate(dietGoalDTO.getEndDate());
            dietGoalMapper.insert(newDietGoal);
            return newDietGoal;
        }
    }

    @Override
    public DietGoal getDietGoalByUserId(Long userId) {
        return dietGoalMapper.findByUserId(userId);
    }

    @Override
    public double calculateTargetCalories(double height, double weight, int age, String gender, String goalType) {
        // 计算基础代谢率
        double bmr;
        if ("男".equals(gender) || "male".equals(gender.toLowerCase())) {
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age);
        } else {
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age);
        }

        // 根据目标类型调整卡路里
        switch (goalType.toLowerCase()) {
            case "weight_loss": // 减肥
                return bmr * 0.85;
            case "muscle_gain": // 增肌
                return bmr * 1.15;
            case "health_maintenance": // 维持健康
                return bmr;
            default:
                return bmr;
        }
    }

}
