package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.health.entity.DietRecord;
import com.health.entity.DietRecordDetail;
import com.health.entity.Ingredient;
import com.health.entity.Recipe;
import com.health.mapper.DietRecordDetailMapper;
import com.health.mapper.DietRecordMapper;
import com.health.mapper.IngredientMapper;
import com.health.mapper.RecipeMapper;
import com.health.service.DietRecordService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class DietRecordServiceImpl implements DietRecordService {

    private static final String DATE_PATTERN = "yyyy-MM-dd";

    @Autowired
    private DietRecordMapper dietRecordMapper;

    @Autowired
    private DietRecordDetailMapper dietRecordDetailMapper;

    @Autowired
    private RecipeMapper recipeMapper;

    @Autowired
    private IngredientMapper ingredientMapper;

    @Transactional
    @Override
    public DietRecord saveDietRecord(DietRecord record, List<DietRecordDetail> details) {
        applyRecordTotals(record, details);
        record.setIsDeleted(0);
        dietRecordMapper.insert(record);

        if (details != null) {
            for (DietRecordDetail detail : details) {
                detail.setRecordId(record.getId());
                detail.setIsDeleted(0);
                dietRecordDetailMapper.insert(detail);
            }
        }

        return record;
    }

    @Transactional
    @Override
    public DietRecord saveDietRecord(Long userId, Map<String, Object> recordData) {
        DietRecord record = new DietRecord();
        record.setUserId(userId);
        record.setRecordDate(new Date());

        if (recordData.containsKey("mealType") && recordData.get("mealType") != null) {
            record.setMealType(recordData.get("mealType").toString());
        }
        if (recordData.containsKey("notes") && recordData.get("notes") != null) {
            record.setNotes(recordData.get("notes").toString());
        }
        if (recordData.containsKey("date") && recordData.get("date") != null) {
            record.setRecordDate(parseRecordDate(recordData.get("date").toString()));
        }

        List<DietRecordDetail> details = buildDetails(recordData);
        applyRecordTotals(record, details);
        record.setIsDeleted(0);
        dietRecordMapper.insert(record);

        for (DietRecordDetail detail : details) {
            detail.setRecordId(record.getId());
            detail.setIsDeleted(0);
            dietRecordDetailMapper.insert(detail);
        }

        return record;
    }

    @Transactional
    @Override
    public DietRecord updateDietRecord(DietRecord record, List<DietRecordDetail> details) {
        applyRecordTotals(record, details);
        dietRecordMapper.updateById(record);

        QueryWrapper<DietRecordDetail> wrapper = new QueryWrapper<>();
        wrapper.eq("record_id", record.getId()).eq("is_deleted", 0);
        dietRecordDetailMapper.delete(wrapper);

        if (details != null) {
            for (DietRecordDetail detail : details) {
                detail.setRecordId(record.getId());
                detail.setIsDeleted(0);
                dietRecordDetailMapper.insert(detail);
            }
        }

        return record;
    }

    @Transactional
    @Override
    public boolean deleteDietRecord(Long id) {
        UpdateWrapper<DietRecordDetail> detailWrapper = new UpdateWrapper<>();
        detailWrapper.eq("record_id", id).eq("is_deleted", 0).set("is_deleted", 1);
        dietRecordDetailMapper.update(null, detailWrapper);

        UpdateWrapper<DietRecord> recordWrapper = new UpdateWrapper<>();
        recordWrapper.eq("id", id).eq("is_deleted", 0).set("is_deleted", 1);
        return dietRecordMapper.update(null, recordWrapper) > 0;
    }

    @Transactional
    @Override
    public boolean deleteDietRecord(Long recordId, Long userId) {
        QueryWrapper<DietRecord> wrapper = new QueryWrapper<>();
        wrapper.eq("id", recordId).eq("user_id", userId).eq("is_deleted", 0);
        DietRecord record = dietRecordMapper.selectOne(wrapper);

        if (record == null) {
            throw new RuntimeException("记录不存在或无权限删除");
        }

        UpdateWrapper<DietRecordDetail> detailWrapper = new UpdateWrapper<>();
        detailWrapper.eq("record_id", recordId).eq("is_deleted", 0).set("is_deleted", 1);
        dietRecordDetailMapper.update(null, detailWrapper);

        UpdateWrapper<DietRecord> recordWrapper = new UpdateWrapper<>();
        recordWrapper.eq("id", recordId).eq("user_id", userId).eq("is_deleted", 0).set("is_deleted", 1);
        return dietRecordMapper.update(null, recordWrapper) > 0;
    }

    @Override
    public DietRecord getDietRecordById(Long id) {
        DietRecord record = dietRecordMapper.selectById(id);
        if (record == null || Integer.valueOf(1).equals(record.getIsDeleted())) {
            return null;
        }

        List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(record.getId());
        enrichRecordDetails(details);
        record.setDetails(details);
        record.setMealName(resolveMealName(details));
        applyRecordHealthMetrics(record, details);
        return record;
    }

    @Override
    public List<DietRecordDetail> getDietRecordDetails(Long recordId) {
        List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(recordId);
        enrichRecordDetails(details);
        return details;
    }

    @Override
    public List<DietRecordDetail> getDietRecordDetails(Long recordId, Long userId) {
        QueryWrapper<DietRecord> wrapper = new QueryWrapper<>();
        wrapper.eq("id", recordId).eq("user_id", userId).eq("is_deleted", 0);
        DietRecord record = dietRecordMapper.selectOne(wrapper);

        if (record == null) {
            throw new RuntimeException("记录不存在或无权限查看");
        }

        List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(recordId);
        enrichRecordDetails(details);
        return details;
    }

    @Override
    public List<DietRecord> getDietRecordsByDate(Long userId, Date date) {
        return dietRecordMapper.selectByUserIdAndDate(userId, date);
    }

    @Override
    public List<DietRecord> getDietRecordsByDateRange(Long userId, Date startDate, Date endDate) {
        return dietRecordMapper.selectByUserIdAndDateRange(userId, startDate, endDate);
    }

    @Override
    public List<DietRecord> getDietRecordsByUserId(Long userId, String startDateStr, String endDateStr, Integer page, Integer pageSize) {
        Date startDate = null;
        Date endDate = null;

        try {
            SimpleDateFormat sdf = new SimpleDateFormat(DATE_PATTERN);
            if (startDateStr != null && !startDateStr.trim().isEmpty()) {
                startDate = sdf.parse(startDateStr);
            }
            if (endDateStr != null && !endDateStr.trim().isEmpty()) {
                endDate = sdf.parse(endDateStr);
            }
        } catch (ParseException e) {
            throw new RuntimeException("日期格式错误");
        }

        List<DietRecord> records;
        if (startDate != null && endDate != null) {
            records = dietRecordMapper.selectByUserIdAndDateRange(userId, startDate, endDate);
        } else if (startDate != null) {
            records = dietRecordMapper.selectByUserIdAndDateRange(userId, startDate, new Date());
        } else if (endDate != null) {
            records = dietRecordMapper.selectByUserIdAndDateRange(userId, new Date(0), endDate);
        } else {
            records = dietRecordMapper.selectByUserIdAndDateRange(userId, new Date(0), new Date());
        }

        fillRecordDetails(records);
        return records;
    }

    @Override
    public Map<String, Object> analyzeDietIntake(Long userId, Date startDate, Date endDate) {
        List<DietRecord> records = dietRecordMapper.selectByUserIdAndDateRange(userId, startDate, endDate);
        Map<String, Object> analysis = new HashMap<>();

        double totalCalories = 0;
        double totalProtein = 0;
        double totalCarbs = 0;
        double totalFat = 0;
        double totalFiber = 0;
        double totalSugar = 0;
        double totalSodium = 0;
        double weightedGiSum = 0;
        double giWeightSum = 0;

        for (DietRecord record : records) {
            totalCalories += safeValue(record.getTotalCalories());

            List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(record.getId());
            for (DietRecordDetail detail : details) {
                enrichDetailNutrition(detail);
                totalProtein += safeValue(detail.getProtein());
                totalCarbs += safeValue(detail.getCarbs());
                totalFat += safeValue(detail.getFat());
                totalFiber += safeValue(detail.getFiber());
                totalSugar += safeValue(detail.getSugar());
                totalSodium += safeValue(detail.getSodium());
                double detailGi = safeValue(detail.getGi());
                double giWeight = safeValue(detail.getCarbs());
                if (detailGi > 0 && giWeight > 0) {
                    weightedGiSum += detailGi * giWeight;
                    giWeightSum += giWeight;
                }
            }
        }

        analysis.put("totalCalories", totalCalories);
        analysis.put("totalProtein", totalProtein);
        analysis.put("totalCarbs", totalCarbs);
        analysis.put("totalFat", totalFat);
        analysis.put("totalFiber", totalFiber);
        analysis.put("totalSugar", totalSugar);
        analysis.put("totalSodium", totalSodium);
        analysis.put("avgGi", giWeightSum > 0 ? roundValue(weightedGiSum / giWeightSum, 2) : 0.0);
        analysis.put("recordCount", records.size());
        return analysis;
    }

    @Override
    public Map<String, Object> getDietTrendAnalysis(Long userId, String startDateStr, String endDateStr) {
        Date startDate = parseRecordDate(startDateStr);
        Date endDate = parseRecordDate(endDateStr);
        List<DietRecord> records = dietRecordMapper.selectByUserIdAndDateRange(userId, startDate, endDate);
        Map<String, Object> analysis = new HashMap<>();

        double totalCalories = 0;
        double totalProtein = 0;
        double totalCarbs = 0;
        double totalFat = 0;
        double totalFiber = 0;
        double totalSugar = 0;
        double totalSodium = 0;
        double weightedGiSum = 0;
        double giWeightSum = 0;
        Map<String, Map<String, Double>> dailyStats = new HashMap<>();
        SimpleDateFormat sdf = new SimpleDateFormat(DATE_PATTERN);

        for (DietRecord record : records) {
            String dateStr = sdf.format(record.getRecordDate());
            dailyStats.computeIfAbsent(dateStr, key -> {
                Map<String, Double> stats = new HashMap<>();
                stats.put("calories", 0.0);
                stats.put("protein", 0.0);
                stats.put("carbs", 0.0);
                stats.put("fat", 0.0);
                stats.put("fiber", 0.0);
                stats.put("sugar", 0.0);
                stats.put("sodium", 0.0);
                stats.put("giWeightSum", 0.0);
                stats.put("giCarbWeight", 0.0);
                return stats;
            });

            Map<String, Double> stats = dailyStats.get(dateStr);
            double calories = safeValue(record.getTotalCalories());
            stats.put("calories", stats.get("calories") + calories);
            totalCalories += calories;

            List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(record.getId());
            for (DietRecordDetail detail : details) {
                enrichDetailNutrition(detail);
                double protein = safeValue(detail.getProtein());
                double carbs = safeValue(detail.getCarbs());
                double fat = safeValue(detail.getFat());
                double fiber = safeValue(detail.getFiber());
                double sugar = safeValue(detail.getSugar());
                double sodium = safeValue(detail.getSodium());
                double gi = safeValue(detail.getGi());

                stats.put("protein", stats.get("protein") + protein);
                stats.put("carbs", stats.get("carbs") + carbs);
                stats.put("fat", stats.get("fat") + fat);
                stats.put("fiber", stats.get("fiber") + fiber);
                stats.put("sugar", stats.get("sugar") + sugar);
                stats.put("sodium", stats.get("sodium") + sodium);
                if (gi > 0 && carbs > 0) {
                    stats.put("giWeightSum", stats.get("giWeightSum") + gi * carbs);
                    stats.put("giCarbWeight", stats.get("giCarbWeight") + carbs);
                    weightedGiSum += gi * carbs;
                    giWeightSum += carbs;
                }

                totalProtein += protein;
                totalCarbs += carbs;
                totalFat += fat;
                totalFiber += fiber;
                totalSugar += sugar;
                totalSodium += sodium;
            }
        }

        for (Map<String, Double> stats : dailyStats.values()) {
            double dayGiWeight = stats.get("giCarbWeight");
            double dayGiSum = stats.get("giWeightSum");
            stats.put("gi", dayGiWeight > 0 ? roundValue(dayGiSum / dayGiWeight, 2) : 0.0);
            stats.remove("giWeightSum");
            stats.remove("giCarbWeight");
        }

        analysis.put("totalCalories", totalCalories);
        analysis.put("totalProtein", totalProtein);
        analysis.put("totalCarbs", totalCarbs);
        analysis.put("totalFat", totalFat);
        analysis.put("totalFiber", totalFiber);
        analysis.put("totalSugar", totalSugar);
        analysis.put("totalSodium", totalSodium);
        analysis.put("avgGi", giWeightSum > 0 ? roundValue(weightedGiSum / giWeightSum, 2) : 0.0);
        analysis.put("dailyStats", dailyStats);
        analysis.put("recordCount", records.size());
        return analysis;
    }

    @Override
    public List<Map<String, Object>> getDietTrend(Long userId, int days) {
        List<Map<String, Object>> trend = new ArrayList<>();
        SimpleDateFormat sdf = new SimpleDateFormat(DATE_PATTERN);

        for (int i = days - 1; i >= 0; i--) {
            Calendar calendar = Calendar.getInstance();
            calendar.setTime(new Date());
            calendar.add(Calendar.DAY_OF_YEAR, -i);
            Date date = calendar.getTime();

            List<DietRecord> records = dietRecordMapper.selectByUserIdAndDate(userId, date);
            double dailyCalories = 0;

            for (DietRecord record : records) {
                dailyCalories += safeValue(record.getTotalCalories());
            }

            Map<String, Object> dayData = new HashMap<>();
            dayData.put("date", sdf.format(date));
            dayData.put("calories", dailyCalories);
            trend.add(dayData);
        }

        return trend;
    }

    @Override
    public Map<String, Double> calculateDailyNutrition(Long userId, Date date) {
        List<DietRecord> records = dietRecordMapper.selectByUserIdAndDate(userId, date);
        Map<String, Double> nutrition = new HashMap<>();

        double totalCalories = 0;
        double totalProtein = 0;
        double totalCarbs = 0;
        double totalFat = 0;
        double totalFiber = 0;
        double totalSugar = 0;
        double totalSodium = 0;
        double weightedGiSum = 0;
        double giWeightSum = 0;

        for (DietRecord record : records) {
            totalCalories += safeValue(record.getTotalCalories());

            List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(record.getId());
            for (DietRecordDetail detail : details) {
                enrichDetailNutrition(detail);
                totalProtein += safeValue(detail.getProtein());
                totalCarbs += safeValue(detail.getCarbs());
                totalFat += safeValue(detail.getFat());
                totalFiber += safeValue(detail.getFiber());
                totalSugar += safeValue(detail.getSugar());
                totalSodium += safeValue(detail.getSodium());
                double detailGi = safeValue(detail.getGi());
                double giWeight = safeValue(detail.getCarbs());
                if (detailGi > 0 && giWeight > 0) {
                    weightedGiSum += detailGi * giWeight;
                    giWeightSum += giWeight;
                }
            }
        }

        nutrition.put("calories", totalCalories);
        nutrition.put("protein", totalProtein);
        nutrition.put("carbs", totalCarbs);
        nutrition.put("fat", totalFat);
        nutrition.put("fiber", totalFiber);
        nutrition.put("sugar", totalSugar);
        nutrition.put("sodium", totalSodium);
        nutrition.put("gi", giWeightSum > 0 ? roundValue(weightedGiSum / giWeightSum, 2) : 0.0);
        return nutrition;
    }


    @Override
    public List<String> getDietSuggestions(Long userId) {
        List<String> suggestions = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        try {
            Date endDate = new Date();
            Calendar cal = Calendar.getInstance();
            cal.add(Calendar.DAY_OF_MONTH, -7);
            Date startDate = cal.getTime();

            List<DietRecord> records = getDietRecordsByDateRange(userId, startDate, endDate);
            if (records == null || records.isEmpty()) {
                suggestions.add("保持饮食均衡，摄入更多样化食物");
                suggestions.add("增加蔬菜水果的摄入量");
                suggestions.add("控制油脂和盐分的摄入");
                suggestions.add("保持充足饮水");
                suggestions.add("规律饮食，避免暴饮暴食");
                return suggestions;
            }

            double totalCalories = 0;
            double totalProtein = 0;
            double totalCarbs = 0;
            double totalFat = 0;
            double totalFiber = 0;
            double totalSugar = 0;
            double totalSodium = 0;
            double weightedGiSum = 0;
            double giWeightSum = 0;
            int recordCount = 0;

            for (DietRecord record : records) {
                totalCalories += safeValue(record.getTotalCalories());
                List<DietRecordDetail> details = getDietRecordDetails(record.getId());
                for (DietRecordDetail detail : details) {
                    totalProtein += safeValue(detail.getProtein());
                    totalCarbs += safeValue(detail.getCarbs());
                    totalFat += safeValue(detail.getFat());
                    totalFiber += safeValue(detail.getFiber());
                    totalSugar += safeValue(detail.getSugar());
                    totalSodium += safeValue(detail.getSodium());
                    double detailGi = safeValue(detail.getGi());
                    double giWeight = safeValue(detail.getCarbs());
                    if (detailGi > 0 && giWeight > 0) {
                        weightedGiSum += detailGi * giWeight;
                        giWeightSum += giWeight;
                    }
                }
                recordCount++;
            }

            double avgCalories = recordCount > 0 ? totalCalories / recordCount : 0;
            double avgProtein = recordCount > 0 ? totalProtein / recordCount : 0;
            double avgCarbs = recordCount > 0 ? totalCarbs / recordCount : 0;
            double avgFat = recordCount > 0 ? totalFat / recordCount : 0;
            double avgFiber = recordCount > 0 ? totalFiber / recordCount : 0;
            double avgSugar = recordCount > 0 ? totalSugar / recordCount : 0;
            double avgSodium = recordCount > 0 ? totalSodium / recordCount : 0;
            double avgGi = giWeightSum > 0 ? weightedGiSum / giWeightSum : 0;

            if (avgCalories > 2500) {
                warnings.add("最近 7 天平均热量摄入偏高（" + String.format("%.0f", avgCalories) + " kcal），建议适当控制");
            } else if (avgCalories < 1200) {
                warnings.add("最近 7 天平均热量摄入偏低（" + String.format("%.0f", avgCalories) + " kcal），注意营养补足");
            } else {
                suggestions.add("热量摄入保持在合理范围内");
            }

            if (avgFat > 80) {
                warnings.add("脂肪摄入偏高，建议减少油炸食品和高脂肉类");
            }
            if (avgCarbs > 400) {
                warnings.add("碳水摄入偏高，建议适当减少主食量");
            }
            if (avgProtein < 50) {
                warnings.add("蛋白质摄入不足，建议增加蛋奶肉豆类食物");
            }
            if (avgFiber > 0 && avgFiber < 12) {
                warnings.add("膳食纤维摄入偏低，建议增加蔬菜、全谷物和豆类食物");
            }
            if (avgSugar > 30) {
                warnings.add("糖摄入偏高，建议减少含糖饮料和甜点");
            }
            if (avgSodium > 1500) {
                warnings.add("钠摄入偏高，建议减少浓汤、调味汁和加工食品");
            }
            if (avgGi >= 60) {
                warnings.add("近期饮食 GI 偏高，可适当用粗粮、豆类和高纤维食物替换部分精制碳水");
            }
            if (recordCount < 5) {
                warnings.add("最近饮食记录较少，建议坚持记录以便系统分析");
            }

            suggestions.add("保持饮食均衡，摄入更多样化食物");
            suggestions.add("增加蔬菜水果的摄入量");
            suggestions.add("控制油脂和盐分的摄入");
            suggestions.add("保持充足饮水");
            suggestions.add("规律饮食，避免暴饮暴食");

            List<String> result = new ArrayList<>();
            result.addAll(warnings);
            result.addAll(suggestions);
            return result;
        } catch (Exception e) {
            log.error("生成饮食建议失败: {}", e.getMessage(), e);
            suggestions.add("保持饮食均衡，摄入更多样化食物");
            suggestions.add("增加蔬菜水果的摄入量");
            suggestions.add("控制油脂和盐分的摄入");
            suggestions.add("保持充足饮水");
            suggestions.add("规律饮食，避免暴饮暴食");
            return suggestions;
        }
    }
    private List<DietRecordDetail> buildDetails(Map<String, Object> recordData) {
        List<DietRecordDetail> details = new ArrayList<>();
        if (!recordData.containsKey("details") || recordData.get("details") == null) {
            return details;
        }

        List<Map<String, Object>> detailList = (List<Map<String, Object>>) recordData.get("details");
        for (Map<String, Object> detailMap : detailList) {
            DietRecordDetail detail = new DietRecordDetail();
            if (detailMap.containsKey("foodName") && detailMap.get("foodName") != null) {
                detail.setFoodName(detailMap.get("foodName").toString());
            }
            if (detailMap.containsKey("ingredientId") && detailMap.get("ingredientId") != null
                    && !detailMap.get("ingredientId").toString().trim().isEmpty()) {
                detail.setIngredientId(Long.parseLong(detailMap.get("ingredientId").toString()));
            }
            if (detailMap.containsKey("recipeId") && detailMap.get("recipeId") != null
                    && !detailMap.get("recipeId").toString().trim().isEmpty()) {
                detail.setRecipeId(Long.parseLong(detailMap.get("recipeId").toString()));
            }
            if (detailMap.containsKey("amount") && detailMap.get("amount") != null) {
                detail.setQuantity(Double.parseDouble(detailMap.get("amount").toString()));
            }
            if (detailMap.containsKey("unit") && detailMap.get("unit") != null) {
                detail.setUnit(detailMap.get("unit").toString());
            }
            if (detailMap.containsKey("calories") && detailMap.get("calories") != null) {
                detail.setCalories(Double.parseDouble(detailMap.get("calories").toString()));
            }
            if (detailMap.containsKey("protein") && detailMap.get("protein") != null) {
                detail.setProtein(Double.parseDouble(detailMap.get("protein").toString()));
            }
            if (detailMap.containsKey("carbs") && detailMap.get("carbs") != null) {
                detail.setCarbs(Double.parseDouble(detailMap.get("carbs").toString()));
            }
            if (detailMap.containsKey("fat") && detailMap.get("fat") != null) {
                detail.setFat(Double.parseDouble(detailMap.get("fat").toString()));
            }
            if (detailMap.containsKey("fiber") && detailMap.get("fiber") != null) {
                detail.setFiber(Double.parseDouble(detailMap.get("fiber").toString()));
            }
            if (detailMap.containsKey("sugar") && detailMap.get("sugar") != null) {
                detail.setSugar(Double.parseDouble(detailMap.get("sugar").toString()));
            }
            if (detailMap.containsKey("sodium") && detailMap.get("sodium") != null) {
                detail.setSodium(Double.parseDouble(detailMap.get("sodium").toString()));
            }
            if (detailMap.containsKey("gi") && detailMap.get("gi") != null) {
                detail.setGi(Double.parseDouble(detailMap.get("gi").toString()));
            }
            if (detail.getQuantity() == null || detail.getQuantity() <= 0) {
                detail.setQuantity(1.0);
            }
            if (detail.getUnit() == null || detail.getUnit().trim().isEmpty()) {
                detail.setUnit("份");
            }
            detail.setIsDeleted(0);
            details.add(detail);
        }
        return details;
    }

    private void fillRecordDetails(List<DietRecord> records) {
        if (records == null || records.isEmpty()) {
            return;
        }

        for (DietRecord record : records) {
            if (record == null || record.getId() == null) {
                continue;
            }
            List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(record.getId());
            enrichRecordDetails(details);
            record.setDetails(details);
            record.setMealName(resolveMealName(details));
            applyRecordHealthMetrics(record, details);
        }
    }

    private String resolveMealName(List<DietRecordDetail> details) {
        if (details == null || details.isEmpty()) {
            return null;
        }

        for (DietRecordDetail detail : details) {
            if (detail == null || detail.getRecipeId() == null) {
                continue;
            }

            Recipe recipe = recipeMapper.selectById(detail.getRecipeId());
            if (recipe != null && recipe.getName() != null && !recipe.getName().trim().isEmpty()) {
                return recipe.getName().trim();
            }
        }

        return details.get(0).getFoodName();
    }

    private void applyRecordTotals(DietRecord record, List<DietRecordDetail> details) {
        double totalCalories = 0;
        double totalProtein = 0;
        double totalCarbs = 0;
        double totalFat = 0;
        double totalFiber = 0;
        double totalSugar = 0;
        double totalSodium = 0;
        double weightedGiSum = 0;
        double giWeightSum = 0;

        if (details != null) {
            for (DietRecordDetail detail : details) {
                if (detail == null) {
                    continue;
                }
                enrichDetailNutrition(detail);
                totalCalories += safeValue(detail.getCalories());
                totalProtein += safeValue(detail.getProtein());
                totalCarbs += safeValue(detail.getCarbs());
                totalFat += safeValue(detail.getFat());
            }
        }

        record.setTotalCalories(totalCalories);
        record.setTotalProtein(totalProtein);
        record.setTotalCarbs(totalCarbs);
        record.setTotalFat(totalFat);
        applyRecordHealthMetrics(record, details);
    }

    private void enrichRecordDetails(List<DietRecordDetail> details) {
        if (details == null || details.isEmpty()) {
            return;
        }
        for (DietRecordDetail detail : details) {
            enrichDetailNutrition(detail);
        }
    }

    private void enrichDetailNutrition(DietRecordDetail detail) {
        if (detail == null) {
            return;
        }
        if (detail.getIngredientId() == null) {
            if (detail.getFiber() == null) {
                detail.setFiber(0.0);
            }
            if (detail.getSugar() == null) {
                detail.setSugar(0.0);
            }
            if (detail.getSodium() == null) {
                detail.setSodium(0.0);
            }
            if (detail.getGi() == null) {
                detail.setGi(0.0);
            }
            return;
        }

        Ingredient ingredient = ingredientMapper.selectById(detail.getIngredientId());
        if (ingredient == null) {
            return;
        }

        double quantity = safeValue(detail.getQuantity());
        if (quantity <= 0) {
            quantity = 1.0;
        }
        double ratio = quantity / 100.0;

        if (detail.getFiber() == null || detail.getFiber() <= 0) {
            detail.setFiber(roundValue(safeValue(ingredient.getFiberPer100g()) * ratio, 2));
        }
        detail.setSugar(roundValue(safeValue(ingredient.getSugarPer100g()) * ratio, 2));
        detail.setSodium(roundValue(safeValue(ingredient.getSodiumPer100g()) * ratio, 2));
        detail.setGi(ingredient.getGiValue() == null ? 0.0 : ingredient.getGiValue().doubleValue());
    }

    private void applyRecordHealthMetrics(DietRecord record, List<DietRecordDetail> details) {
        if (record == null) {
            return;
        }

        double totalFiber = 0;
        double totalSugar = 0;
        double totalSodium = 0;
        double weightedGiSum = 0;
        double giWeightSum = 0;

        if (details != null) {
            for (DietRecordDetail detail : details) {
                if (detail == null) {
                    continue;
                }
                enrichDetailNutrition(detail);
                totalFiber += safeValue(detail.getFiber());
                totalSugar += safeValue(detail.getSugar());
                totalSodium += safeValue(detail.getSodium());
                double detailGi = safeValue(detail.getGi());
                double giWeight = safeValue(detail.getCarbs());
                if (detailGi > 0 && giWeight > 0) {
                    weightedGiSum += detailGi * giWeight;
                    giWeightSum += giWeight;
                }
            }
        }

        record.setTotalFiber(roundValue(totalFiber, 2));
        record.setTotalSugar(roundValue(totalSugar, 2));
        record.setTotalSodium(roundValue(totalSodium, 2));
        record.setTotalGi(giWeightSum > 0 ? roundValue(weightedGiSum / giWeightSum, 2) : 0.0);
    }

    private double roundValue(double value, int digits) {
        double factor = Math.pow(10, digits);
        return Math.round(value * factor) / factor;
    }

    private double safeValue(Double value) {
        return value == null ? 0 : value;
    }

    private Date parseRecordDate(String value) {
        try {
            return new SimpleDateFormat(DATE_PATTERN).parse(value);
        } catch (ParseException e) {
            throw new RuntimeException("日期格式错误");
        }
    }
}

