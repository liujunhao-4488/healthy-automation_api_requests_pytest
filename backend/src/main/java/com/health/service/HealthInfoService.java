package com.health.service;

import com.health.entity.HealthInfo;
import com.health.dto.HealthInfoDTO;

public interface HealthInfoService {

    // 保存或更新健康信息
    HealthInfo saveOrUpdateHealthInfo(Long userId, HealthInfoDTO healthInfoDTO);

    // 根据用户ID获取健康信息
    HealthInfo getHealthInfoByUserId(Long userId);

    // 计算BMI
    double calculateBMI(double height, double weight);

    // 计算基础代谢率
    double calculateBMR(double height, double weight, int age, String gender);

}
