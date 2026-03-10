package com.health.service.impl;

import com.health.entity.HealthInfo;
import com.health.dto.HealthInfoDTO;
import com.health.service.HealthInfoService;
import com.health.mapper.HealthInfoMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class HealthInfoServiceImpl implements HealthInfoService {

    @Autowired
    private HealthInfoMapper healthInfoMapper;

    @Override
    public HealthInfo saveOrUpdateHealthInfo(Long userId, HealthInfoDTO healthInfoDTO) {
        // 计算BMI
        double bmi = calculateBMI(healthInfoDTO.getHeight(), healthInfoDTO.getWeight());

        // 查找用户是否已有健康信息
        HealthInfo existingHealthInfo = healthInfoMapper.findByUserId(userId);

        if (existingHealthInfo != null) {
            // 更新现有健康信息
            existingHealthInfo.setAge(healthInfoDTO.getAge());
            existingHealthInfo.setGender(healthInfoDTO.getGender());
            existingHealthInfo.setHeight(healthInfoDTO.getHeight());
            existingHealthInfo.setWeight(healthInfoDTO.getWeight());
            existingHealthInfo.setBmi(bmi);
            existingHealthInfo.setBloodType(healthInfoDTO.getBloodType());
            existingHealthInfo.setAllergies(healthInfoDTO.getAllergies());
            existingHealthInfo.setChronicDiseases(healthInfoDTO.getChronicDiseases());
            existingHealthInfo.setActivityLevel(healthInfoDTO.getActivityLevel());
            existingHealthInfo.setHealthCondition(healthInfoDTO.getHealthCondition());
            existingHealthInfo.setWaistCircumference(healthInfoDTO.getWaistCircumference());
            existingHealthInfo.setBmr(healthInfoDTO.getBmr());
            existingHealthInfo.setBloodPressure(healthInfoDTO.getBloodPressure());
            existingHealthInfo.setBloodSugar(healthInfoDTO.getBloodSugar());
            existingHealthInfo.setExerciseDuration(healthInfoDTO.getExerciseDuration());
            existingHealthInfo.setExerciseType(healthInfoDTO.getExerciseType());
            healthInfoMapper.updateById(existingHealthInfo);
            return existingHealthInfo;
        } else {
            // 创建新的健康信息
            HealthInfo newHealthInfo = new HealthInfo();
            newHealthInfo.setUserId(userId);
            newHealthInfo.setAge(healthInfoDTO.getAge());
            newHealthInfo.setGender(healthInfoDTO.getGender());
            newHealthInfo.setHeight(healthInfoDTO.getHeight());
            newHealthInfo.setWeight(healthInfoDTO.getWeight());
            newHealthInfo.setBmi(bmi);
            newHealthInfo.setBloodType(healthInfoDTO.getBloodType());
            newHealthInfo.setAllergies(healthInfoDTO.getAllergies());
            newHealthInfo.setChronicDiseases(healthInfoDTO.getChronicDiseases());
            newHealthInfo.setActivityLevel(healthInfoDTO.getActivityLevel());
            newHealthInfo.setHealthCondition(healthInfoDTO.getHealthCondition());
            newHealthInfo.setWaistCircumference(healthInfoDTO.getWaistCircumference());
            newHealthInfo.setBmr(healthInfoDTO.getBmr());
            newHealthInfo.setBloodPressure(healthInfoDTO.getBloodPressure());
            newHealthInfo.setBloodSugar(healthInfoDTO.getBloodSugar());
            newHealthInfo.setExerciseDuration(healthInfoDTO.getExerciseDuration());
            newHealthInfo.setExerciseType(healthInfoDTO.getExerciseType());
            healthInfoMapper.insert(newHealthInfo);
            return newHealthInfo;
        }
    }

    @Override
    public HealthInfo getHealthInfoByUserId(Long userId) {
        return healthInfoMapper.findByUserId(userId);
    }

    @Override
    public double calculateBMI(double height, double weight) {
        // 身高转换为米
        double heightInMeters = height / 100;
        // BMI = 体重(kg) / 身高(m)的平方
        return weight / (heightInMeters * heightInMeters);
    }

    @Override
    public double calculateBMR(double height, double weight, int age, String gender) {
        // 使用Harris-Benedict公式计算基础代谢率
        if ("男".equals(gender) || "male".equals(gender.toLowerCase())) {
            // 男性: BMR = 88.362 + (13.397 × 体重kg) + (4.799 × 身高cm) - (5.677 × 年龄)
            return 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age);
        } else {
            // 女性: BMR = 447.593 + (9.247 × 体重kg) + (3.098 × 身高cm) - (4.330 × 年龄)
            return 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age);
        }
    }

}
