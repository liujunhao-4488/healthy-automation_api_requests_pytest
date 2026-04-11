package com.health.service;

import com.health.dto.HealthInfoDTO;
import com.health.entity.DietGoal;
import com.health.entity.HealthInfo;
import com.health.entity.HealthInfoHistory;

import java.util.List;
import java.util.Map;

public interface HealthInfoService {

    HealthInfo saveOrUpdateHealthInfo(Long userId, HealthInfoDTO healthInfoDTO);

    HealthInfo getHealthInfoByUserId(Long userId);

    List<HealthInfoHistory> getHealthHistoryByUserId(Long userId);

    Map<String, Object> buildHealthAnalysis(Long userId, HealthInfo healthInfo, DietGoal dietGoal);

    double calculateBMI(double height, double weight);

    double calculateBMR(double height, double weight, int age, String gender);
}
