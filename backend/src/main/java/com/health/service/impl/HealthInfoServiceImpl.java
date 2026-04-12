package com.health.service.impl;

import com.health.dto.HealthInfoDTO;
import com.health.entity.DietGoal;
import com.health.entity.HealthInfo;
import com.health.entity.HealthInfoHistory;
import com.health.mapper.HealthInfoHistoryMapper;
import com.health.mapper.HealthInfoMapper;
import com.health.service.HealthInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class HealthInfoServiceImpl implements HealthInfoService {

    @Autowired
    private HealthInfoMapper healthInfoMapper;

    @Autowired
    private HealthInfoHistoryMapper healthInfoHistoryMapper;

    @Override
    public HealthInfo saveOrUpdateHealthInfo(Long userId, HealthInfoDTO healthInfoDTO) {
        double bmi = calculateBMI(healthInfoDTO.getHeight(), healthInfoDTO.getWeight());
        HealthInfo existingHealthInfo = healthInfoMapper.findByUserId(userId);

        if (existingHealthInfo != null) {
            existingHealthInfo.setAge(healthInfoDTO.getAge());
            existingHealthInfo.setGender(healthInfoDTO.getGender());
            existingHealthInfo.setHeight(healthInfoDTO.getHeight());
            existingHealthInfo.setWeight(healthInfoDTO.getWeight());
            existingHealthInfo.setBmi(bmi);
            existingHealthInfo.setChronicDiseases(healthInfoDTO.getChronicDiseases());
            existingHealthInfo.setActivityLevel(healthInfoDTO.getActivityLevel());
            existingHealthInfo.setBmr(healthInfoDTO.getBmr());
            existingHealthInfo.setBloodPressure(healthInfoDTO.getBloodPressure());
            existingHealthInfo.setBloodSugar(healthInfoDTO.getBloodSugar());
            existingHealthInfo.setExerciseDuration(healthInfoDTO.getExerciseDuration());
            existingHealthInfo.setExerciseType(healthInfoDTO.getExerciseType());
            healthInfoMapper.updateById(existingHealthInfo);
            appendHistoryIfNeeded(userId, existingHealthInfo);
            return existingHealthInfo;
        }

        HealthInfo newHealthInfo = new HealthInfo();
        newHealthInfo.setUserId(userId);
        newHealthInfo.setAge(healthInfoDTO.getAge());
        newHealthInfo.setGender(healthInfoDTO.getGender());
        newHealthInfo.setHeight(healthInfoDTO.getHeight());
        newHealthInfo.setWeight(healthInfoDTO.getWeight());
        newHealthInfo.setBmi(bmi);
        newHealthInfo.setChronicDiseases(healthInfoDTO.getChronicDiseases());
        newHealthInfo.setActivityLevel(healthInfoDTO.getActivityLevel());
        newHealthInfo.setBmr(healthInfoDTO.getBmr());
        newHealthInfo.setBloodPressure(healthInfoDTO.getBloodPressure());
        newHealthInfo.setBloodSugar(healthInfoDTO.getBloodSugar());
        newHealthInfo.setExerciseDuration(healthInfoDTO.getExerciseDuration());
        newHealthInfo.setExerciseType(healthInfoDTO.getExerciseType());
        healthInfoMapper.insert(newHealthInfo);
        appendHistoryIfNeeded(userId, newHealthInfo);
        return newHealthInfo;
    }

    @Override
    public HealthInfo getHealthInfoByUserId(Long userId) {
        return healthInfoMapper.findByUserId(userId);
    }

    @Override
    public List<HealthInfoHistory> getHealthHistoryByUserId(Long userId) {
        return healthInfoHistoryMapper.findByUserId(userId);
    }

    @Override
    public Map<String, Object> buildHealthAnalysis(Long userId, HealthInfo healthInfo, DietGoal dietGoal) {
        Map<String, Object> analysis = new HashMap<>();
        List<String> recommendations = new ArrayList<>();
        List<String> tags = new ArrayList<>();

        if (healthInfo == null) {
            analysis.put("overallLevel", "待完善");
            analysis.put("summary", "请先完善健康信息，系统才能生成更准确的身体状态分析与饮食建议。");
            analysis.put("recommendations", recommendations);
            analysis.put("tags", tags);
            return analysis;
        }

        String bmiCategory = resolveBmiCategory(healthInfo.getBmi());
        String bmiAdvice = resolveBmiAdvice(healthInfo.getBmi(), dietGoal);
        String bloodPressureStatus = resolveBloodPressureStatus(healthInfo.getBloodPressure());
        String bloodPressureAdvice = resolveBloodPressureAdvice(bloodPressureStatus);
        String bloodSugarStatus = resolveBloodSugarStatus(healthInfo.getBloodSugar());
        String bloodSugarAdvice = resolveBloodSugarAdvice(bloodSugarStatus);
        String activityStatus = resolveActivityStatus(healthInfo.getActivityLevel(), healthInfo.getExerciseDuration());
        String activityAdvice = resolveActivityAdvice(activityStatus);
        String goalInsight = resolveGoalInsight(healthInfo, dietGoal);

        recommendations.add(bmiAdvice);
        recommendations.add(bloodPressureAdvice);
        recommendations.add(bloodSugarAdvice);
        recommendations.add(activityAdvice);
        if (!goalInsight.isEmpty()) {
            recommendations.add(goalInsight);
        }

        addTag(tags, bmiCategory);
        addTag(tags, bloodPressureStatus);
        addTag(tags, bloodSugarStatus);
        addTag(tags, activityStatus);

        analysis.put("overallLevel", resolveOverallLevel(healthInfo, bmiCategory, bloodPressureStatus, bloodSugarStatus));
        analysis.put("summary", buildSummaryText(healthInfo, bmiCategory, bloodPressureStatus, bloodSugarStatus, activityStatus));
        analysis.put("bmiCategory", bmiCategory);
        analysis.put("bmiAdvice", bmiAdvice);
        analysis.put("bloodPressureStatus", bloodPressureStatus);
        analysis.put("bloodPressureAdvice", bloodPressureAdvice);
        analysis.put("bloodSugarStatus", bloodSugarStatus);
        analysis.put("bloodSugarAdvice", bloodSugarAdvice);
        analysis.put("activityStatus", activityStatus);
        analysis.put("activityAdvice", activityAdvice);
        analysis.put("goalInsight", goalInsight);
        analysis.put("recommendations", recommendations);
        analysis.put("tags", tags);
        return analysis;
    }

    @Override
    public double calculateBMI(double height, double weight) {
        double heightInMeters = height / 100;
        return weight / (heightInMeters * heightInMeters);
    }

    @Override
    public double calculateBMR(double height, double weight, int age, String gender) {
        if ("男".equals(gender) || "male".equalsIgnoreCase(gender)) {
            return 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age);
        }
        return 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age);
    }

    private void appendHistoryIfNeeded(Long userId, HealthInfo healthInfo) {
        HealthInfoHistory latestHistory = healthInfoHistoryMapper.findLatestByUserId(userId);

        if (latestHistory != null
            && equalsNumber(latestHistory.getWeight(), healthInfo.getWeight())
            && equalsNumber(latestHistory.getBmi(), healthInfo.getBmi())
            && equalsInteger(latestHistory.getExerciseDuration(), healthInfo.getExerciseDuration())) {
            return;
        }

        HealthInfoHistory history = new HealthInfoHistory();
        history.setUserId(userId);
        history.setWeight(healthInfo.getWeight());
        history.setBmi(healthInfo.getBmi());
        history.setExerciseDuration(healthInfo.getExerciseDuration());
        history.setRecordDate(LocalDate.now());
        healthInfoHistoryMapper.insert(history);
    }

    private boolean equalsNumber(Double left, Double right) {
        if (left == null && right == null) {
            return true;
        }
        if (left == null || right == null) {
            return false;
        }
        return Math.abs(left - right) < 0.0001;
    }

    private boolean equalsInteger(Integer left, Integer right) {
        if (left == null && right == null) {
            return true;
        }
        if (left == null || right == null) {
            return false;
        }
        return left.equals(right);
    }

    private String resolveBmiCategory(Double bmi) {
        if (bmi == null) {
            return "BMI待评估";
        }
        if (bmi < 18.5) {
            return "偏瘦";
        }
        if (bmi < 24) {
            return "正常";
        }
        if (bmi < 28) {
            return "超重";
        }
        return "肥胖风险";
    }

    private String resolveBmiAdvice(Double bmi, DietGoal dietGoal) {
        if (bmi == null) {
            return "建议持续记录体重和身高，方便系统跟踪 BMI 变化。";
        }
        if (bmi < 18.5) {
            return "当前体重偏轻，建议提高优质蛋白和主食摄入，必要时结合增重目标逐步提升能量。";
        }
        if (bmi < 24) {
            return "BMI 处于相对理想区间，建议继续保持稳定作息和均衡饮食结构。";
        }
        if (bmi < 28) {
            return "体重已有上升趋势，建议优先控制总热量和晚间高油高糖食物摄入。";
        }
        return "当前 BMI 偏高，建议配合减脂目标重点控制热量赤字，并逐步增加规律运动。";
    }

    private String resolveBloodPressureStatus(String bloodPressure) {
        if (bloodPressure == null || bloodPressure.trim().isEmpty()) {
            return "血压待补充";
        }

        String normalized = bloodPressure.trim();
        if (!normalized.contains("/")) {
            return "血压待观察";
        }

        try {
            String[] parts = normalized.split("/");
            int systolic = Integer.parseInt(parts[0].trim());
            int diastolic = Integer.parseInt(parts[1].trim());
            if (systolic >= 140 || diastolic >= 90) {
                return "血压偏高";
            }
            if (systolic < 90 || diastolic < 60) {
                return "血压偏低";
            }
            return "血压平稳";
        } catch (NumberFormatException exception) {
            return "血压待观察";
        }
    }

    private String resolveBloodPressureAdvice(String status) {
        if ("血压偏高".equals(status)) {
            return "血压偏高，建议减少高盐加工食品，注意规律作息并持续监测血压。";
        }
        if ("血压偏低".equals(status)) {
            return "血压偏低时要注意补水和规律进餐，运动时避免突然起身导致头晕。";
        }
        if ("血压平稳".equals(status)) {
            return "血压整体平稳，继续保持清淡饮食和规律运动即可。";
        }
        return "建议补充更规范的血压记录，便于系统做更准确判断。";
    }

    private String resolveBloodSugarStatus(Double bloodSugar) {
        if (bloodSugar == null) {
            return "血糖待补充";
        }
        if (bloodSugar < 3.9) {
            return "血糖偏低";
        }
        if (bloodSugar <= 6.1) {
            return "血糖平稳";
        }
        if (bloodSugar <= 7.0) {
            return "血糖偏高";
        }
        return "血糖需关注";
    }

    private String resolveBloodSugarAdvice(String status) {
        if ("血糖偏低".equals(status)) {
            return "血糖偏低时建议避免长时间空腹，主食和蛋白质搭配更均衡一些。";
        }
        if ("血糖平稳".equals(status)) {
            return "血糖处于相对平稳范围，继续保持低糖高纤维的饮食节奏即可。";
        }
        if ("血糖偏高".equals(status) || "血糖需关注".equals(status)) {
            return "血糖有波动风险，建议优先选择低 GI 主食，减少精制糖和含糖饮料。";
        }
        return "若近期有血糖监测数据，建议及时补充，系统会给出更细化的控糖建议。";
    }

    private String resolveActivityStatus(String activityLevel, Integer exerciseDuration) {
        int duration = exerciseDuration == null ? 0 : exerciseDuration;
        if ("extra_active".equals(activityLevel) || duration >= 60) {
            return "活动充足";
        }
        if ("moderately_active".equals(activityLevel) || "very_active".equals(activityLevel) || duration >= 30) {
            return "活动良好";
        }
        if ("lightly_active".equals(activityLevel) || duration > 0) {
            return "活动偏少";
        }
        return "运动不足";
    }

    private String resolveActivityAdvice(String status) {
        if ("活动充足".equals(status) || "活动良好".equals(status)) {
            return "当前活动水平不错，建议继续保持每周稳定的有氧或力量训练频率。";
        }
        if ("活动偏少".equals(status)) {
            return "运动量略少，建议先从每天 20-30 分钟快走或轻运动开始逐步增加。";
        }
        return "当前运动不足，建议从低强度日常活动入手，逐渐建立稳定运动习惯。";
    }

    private String resolveGoalInsight(HealthInfo healthInfo, DietGoal dietGoal) {
        if (dietGoal == null || dietGoal.getGoalType() == null || dietGoal.getGoalType().trim().isEmpty()) {
            return "";
        }

        String goalType = dietGoal.getGoalType().toLowerCase(Locale.ROOT);
        Double bmi = healthInfo.getBmi();
        if (goalType.contains("fat") || goalType.contains("loss")) {
            if (bmi != null && bmi < 18.5) {
                return "你当前体型偏瘦，若继续减脂建议非常谨慎，优先保证基础营养和力量训练质量。";
            }
            return "当前目标更偏向体脂控制，建议优先关注总热量、蛋白质和晚餐结构。";
        }
        if (goalType.contains("gain") || goalType.contains("muscle")) {
            return "当前目标更偏向增肌或增重，建议保持热量盈余并保证蛋白质和训练恢复。";
        }
        if (goalType.contains("sugar")) {
            return "当前目标更偏向控糖，建议主食定量、优先粗杂粮，并关注餐后血糖波动。";
        }
        if (goalType.contains("lipid")) {
            return "当前目标更偏向控脂，建议优先降低饱和脂肪与油炸食物摄入频率。";
        }
        if (goalType.contains("sodium") || goalType.contains("salt")) {
            return "当前目标更偏向低盐饮食，建议减少腌制食品和高钠调味料。";
        }
        return "系统已结合你的当前饮食目标进行分析，后续可继续根据体重变化动态微调。";
    }

    private String resolveOverallLevel(HealthInfo healthInfo, String bmiCategory, String bloodPressureStatus, String bloodSugarStatus) {
        if ("肥胖风险".equals(bmiCategory)
            || "血压偏高".equals(bloodPressureStatus)
            || "血糖需关注".equals(bloodSugarStatus)) {
            return "重点关注";
        }
        if ("超重".equals(bmiCategory) || "血糖偏高".equals(bloodSugarStatus)) {
            return "建议调整";
        }
        if ("偏瘦".equals(bmiCategory) || "血压偏低".equals(bloodPressureStatus)) {
            return "适度补充";
        }
        return "整体平稳";
    }

    private String buildSummaryText(
        HealthInfo healthInfo,
        String bmiCategory,
        String bloodPressureStatus,
        String bloodSugarStatus,
        String activityStatus
    ) {
        StringBuilder builder = new StringBuilder("系统分析显示：");
        builder.append("当前体型").append(bmiCategory).append("，");
        builder.append(bloodPressureStatus).append("，");
        builder.append(bloodSugarStatus).append("，");
        builder.append("运动状态为").append(activityStatus).append("。");
        return builder.toString();
    }

    private void addTag(List<String> tags, String value) {
        if (value == null || value.trim().isEmpty() || tags.contains(value)) {
            return;
        }
        tags.add(value);
    }
}
