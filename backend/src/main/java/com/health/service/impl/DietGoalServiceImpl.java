package com.health.service.impl;

import com.health.dto.DietGoalDTO;
import com.health.entity.DietGoal;
import com.health.mapper.DietGoalMapper;
import com.health.service.DietGoalService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class DietGoalServiceImpl implements DietGoalService {

    @Autowired
    private DietGoalMapper dietGoalMapper;

    @Override
    public DietGoal saveOrUpdateDietGoal(Long userId, DietGoalDTO dietGoalDTO) {
        DietGoal existingDietGoal = dietGoalMapper.findByUserId(userId);

        if (existingDietGoal != null) {
            applyDietGoal(existingDietGoal, dietGoalDTO);
            dietGoalMapper.updateById(existingDietGoal);
            return existingDietGoal;
        }

        DietGoal newDietGoal = new DietGoal();
        newDietGoal.setUserId(userId);
        applyDietGoal(newDietGoal, dietGoalDTO);
        dietGoalMapper.insert(newDietGoal);
        return newDietGoal;
    }

    private void applyDietGoal(DietGoal dietGoal, DietGoalDTO dietGoalDTO) {
        dietGoal.setGoalType(dietGoalDTO.getGoalType());
        dietGoal.setTargetWeight(dietGoalDTO.getTargetWeight());
        dietGoal.setTargetCalories(dietGoalDTO.getTargetCalories());
        dietGoal.setProteinRatio(dietGoalDTO.getProteinRatio());
        dietGoal.setCarbsRatio(dietGoalDTO.getCarbsRatio());
        dietGoal.setFatRatio(dietGoalDTO.getFatRatio());
        dietGoal.setProteinTarget(dietGoalDTO.getProteinTarget());
        dietGoal.setCarbsTarget(dietGoalDTO.getCarbsTarget());
        dietGoal.setFatTarget(dietGoalDTO.getFatTarget());
        dietGoal.setWaterTarget(dietGoalDTO.getWaterTarget());
        dietGoal.setStatus(dietGoalDTO.getStatus());
        dietGoal.setStartDate(dietGoalDTO.getStartDate());
        dietGoal.setEndDate(dietGoalDTO.getEndDate());
        dietGoal.setReminderEnabled(dietGoalDTO.getReminderEnabled());
        dietGoal.setReminderTime(dietGoalDTO.getReminderTime());
    }

    @Override
    public DietGoal getDietGoalByUserId(Long userId) {
        return dietGoalMapper.findByUserId(userId);
    }

    @Override
    public double calculateTargetCalories(double height, double weight, int age, String gender, String goalType) {
        double bmr;
        if ("男".equals(gender) || "male".equalsIgnoreCase(gender)) {
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age);
        } else {
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age);
        }

        switch (goalType.toLowerCase()) {
            case "fat_loss":
                return bmr * 0.85;
            case "muscle_toning":
                return bmr * 1.12;
            case "weight_maintenance":
                return bmr;
            case "healthy_weight_gain":
                return bmr * 1.15;
            case "blood_sugar_control":
                return bmr * 0.9;
            case "lipid_control":
                return bmr * 0.92;
            case "low_sodium":
                return bmr * 0.95;
            case "pregnancy_nutrition":
                return bmr * 1.1;
            case "child_growth":
                return bmr * 1.08;
            case "senior_wellness":
                return bmr * 0.92;
            default:
                return bmr;
        }
    }
}
