package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.health.entity.DietRecord;
import com.health.entity.DietRecordDetail;
import com.health.mapper.DietRecordMapper;
import com.health.mapper.DietRecordDetailMapper;
import com.health.service.DietRecordService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.Date;
import java.util.Calendar;

/**
 * 饮食记录服务实现类
 */
@Service
@Slf4j
public class DietRecordServiceImpl implements DietRecordService {

    @Autowired
    private DietRecordMapper dietRecordMapper;

    @Autowired
    private DietRecordDetailMapper dietRecordDetailMapper;

    @Transactional
    @Override
    public DietRecord saveDietRecord(DietRecord record, List<DietRecordDetail> details) {
        // 计算总热量
        double totalCalories = 0;
        for (DietRecordDetail detail : details) {
            if (detail.getCalories() != null) {
                totalCalories += detail.getCalories();
            }
        }
        record.setTotalCalories(totalCalories);
        
        // 保存记录
        dietRecordMapper.insert(record);
        
        // 保存详情
        for (DietRecordDetail detail : details) {
            detail.setRecordId(record.getId());
            dietRecordDetailMapper.insert(detail);
        }
        
        return record;
    }

    @Transactional
    @Override
    public DietRecord saveDietRecord(Long userId, Map<String, Object> recordData) {
        // 创建饮食记录
        DietRecord record = new DietRecord();
        record.setUserId(userId);
        record.setRecordDate(new Date());
        
        // 处理餐次类型
        if (recordData.containsKey("mealType")) {
            record.setMealType(recordData.get("mealType").toString());
        }
        
        // 处理详情列表
        List<DietRecordDetail> details = new ArrayList<>();
        if (recordData.containsKey("details")) {
            List<Map<String, Object>> detailList = (List<Map<String, Object>>) recordData.get("details");
            for (Map<String, Object> detailMap : detailList) {
                DietRecordDetail detail = new DietRecordDetail();
                if (detailMap.containsKey("foodName")) {
                    detail.setFoodName(detailMap.get("foodName").toString());
                }
                if (detailMap.containsKey("amount")) {
                    detail.setQuantity(Double.parseDouble(detailMap.get("amount").toString()));
                }
                if (detailMap.containsKey("calories")) {
                    detail.setCalories(Double.parseDouble(detailMap.get("calories").toString()));
                }
                if (detailMap.containsKey("protein")) {
                    detail.setProtein(Double.parseDouble(detailMap.get("protein").toString()));
                }
                if (detailMap.containsKey("carbs")) {
                    detail.setCarbs(Double.parseDouble(detailMap.get("carbs").toString()));
                }
                if (detailMap.containsKey("fat")) {
                    detail.setFat(Double.parseDouble(detailMap.get("fat").toString()));
                }
                details.add(detail);
            }
        }
        
        // 计算总热量
        double totalCalories = 0;
        for (DietRecordDetail detail : details) {
            if (detail.getCalories() != null) {
                totalCalories += detail.getCalories();
            }
        }
        record.setTotalCalories(totalCalories);
        
        // 保存记录
        dietRecordMapper.insert(record);
        
        // 保存详情
        for (DietRecordDetail detail : details) {
            detail.setRecordId(record.getId());
            dietRecordDetailMapper.insert(detail);
        }
        
        return record;
    }

    @Transactional
    @Override
    public DietRecord updateDietRecord(DietRecord record, List<DietRecordDetail> details) {
        // 计算总热量
        double totalCalories = 0;
        for (DietRecordDetail detail : details) {
            if (detail.getCalories() != null) {
                totalCalories += detail.getCalories();
            }
        }
        record.setTotalCalories(totalCalories);
        
        // 更新记录
        dietRecordMapper.updateById(record);
        
        // 删除旧的详情
        QueryWrapper<DietRecordDetail> wrapper = new QueryWrapper<>();
        wrapper.eq("record_id", record.getId());
        dietRecordDetailMapper.delete(wrapper);
        
        // 保存新的详情
        for (DietRecordDetail detail : details) {
            detail.setRecordId(record.getId());
            dietRecordDetailMapper.insert(detail);
        }
        
        return record;
    }

    @Transactional
    @Override
    public boolean deleteDietRecord(Long id) {
        // 删除详情
        QueryWrapper<DietRecordDetail> wrapper = new QueryWrapper<>();
        wrapper.eq("record_id", id);
        dietRecordDetailMapper.delete(wrapper);
        
        // 删除记录
        return dietRecordMapper.deleteById(id) > 0;
    }

    @Transactional
    @Override
    public boolean deleteDietRecord(Long recordId, Long userId) {
        // 验证记录是否属于该用户
        QueryWrapper<DietRecord> wrapper = new QueryWrapper<>();
        wrapper.eq("id", recordId);
        wrapper.eq("user_id", userId);
        DietRecord record = dietRecordMapper.selectOne(wrapper);
        
        if (record == null) {
            throw new RuntimeException("记录不存在或无权限删除");
        }
        
        // 删除详情
        QueryWrapper<DietRecordDetail> detailWrapper = new QueryWrapper<>();
        detailWrapper.eq("record_id", recordId);
        dietRecordDetailMapper.delete(detailWrapper);
        
        // 删除记录
        return dietRecordMapper.deleteById(recordId) > 0;
    }

    @Override
    public DietRecord getDietRecordById(Long id) {
        return dietRecordMapper.selectById(id);
    }

    @Override
    public List<DietRecordDetail> getDietRecordDetails(Long recordId) {
        return dietRecordDetailMapper.selectByRecordId(recordId);
    }

    @Override
    public List<DietRecordDetail> getDietRecordDetails(Long recordId, Long userId) {
        // 验证记录是否属于该用户
        QueryWrapper<DietRecord> wrapper = new QueryWrapper<>();
        wrapper.eq("id", recordId);
        wrapper.eq("user_id", userId);
        DietRecord record = dietRecordMapper.selectOne(wrapper);
        
        if (record == null) {
            throw new RuntimeException("记录不存在或无权限查看");
        }
        
        return dietRecordDetailMapper.selectByRecordId(recordId);
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
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        Date startDate = null;
        Date endDate = null;
        
        try {
            if (startDateStr != null) {
                startDate = sdf.parse(startDateStr);
            }
            if (endDateStr != null) {
                endDate = sdf.parse(endDateStr);
            }
        } catch (ParseException e) {
            throw new RuntimeException("日期格式错误");
        }
        
        if (startDate != null && endDate != null) {
            return dietRecordMapper.selectByUserIdAndDateRange(userId, startDate, endDate);
        } else if (startDate != null) {
            return dietRecordMapper.selectByUserIdAndDateRange(userId, startDate, new Date());
        } else if (endDate != null) {
            return dietRecordMapper.selectByUserIdAndDateRange(userId, new Date(0), endDate);
        } else {
            return dietRecordMapper.selectByUserIdAndDateRange(userId, new Date(0), new Date());
        }
    }

    @Override
    public Map<String, Object> analyzeDietIntake(Long userId, Date startDate, Date endDate) {
        List<DietRecord> records = dietRecordMapper.selectByUserIdAndDateRange(userId, startDate, endDate);
        Map<String, Object> analysis = new HashMap<>();
        
        double totalCalories = 0;
        double totalProtein = 0;
        double totalCarbs = 0;
        double totalFat = 0;
        
        for (DietRecord record : records) {
            totalCalories += record.getTotalCalories() != null ? record.getTotalCalories() : 0;
            
            List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(record.getId());
            for (DietRecordDetail detail : details) {
                totalProtein += detail.getProtein() != null ? detail.getProtein() : 0;
                totalCarbs += detail.getCarbs() != null ? detail.getCarbs() : 0;
                totalFat += detail.getFat() != null ? detail.getFat() : 0;
            }
        }
        
        analysis.put("totalCalories", totalCalories);
        analysis.put("totalProtein", totalProtein);
        analysis.put("totalCarbs", totalCarbs);
        analysis.put("totalFat", totalFat);
        analysis.put("recordCount", records.size());
        
        return analysis;
    }

    @Override
    public Map<String, Object> getDietTrendAnalysis(Long userId, String startDateStr, String endDateStr) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        Date startDate = null;
        Date endDate = null;
        
        try {
            startDate = sdf.parse(startDateStr);
            endDate = sdf.parse(endDateStr);
        } catch (ParseException e) {
            throw new RuntimeException("日期格式错误");
        }
        
        List<DietRecord> records = dietRecordMapper.selectByUserIdAndDateRange(userId, startDate, endDate);
        Map<String, Object> analysis = new HashMap<>();
        
        // 计算总营养摄入
        double totalCalories = 0;
        double totalProtein = 0;
        double totalCarbs = 0;
        double totalFat = 0;
        
        // 按日期分组统计
        Map<String, Map<String, Double>> dailyStats = new HashMap<>();
        
        for (DietRecord record : records) {
            String dateStr = sdf.format(record.getRecordDate());
            if (!dailyStats.containsKey(dateStr)) {
                dailyStats.put(dateStr, new HashMap<String, Double>() {{
                    put("calories", 0.0);
                    put("protein", 0.0);
                    put("carbs", 0.0);
                    put("fat", 0.0);
                }});
            }
            
            Map<String, Double> stats = dailyStats.get(dateStr);
            double calories = record.getTotalCalories() != null ? record.getTotalCalories() : 0;
            stats.put("calories", stats.get("calories") + calories);
            totalCalories += calories;
            
            List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(record.getId());
            for (DietRecordDetail detail : details) {
                double protein = detail.getProtein() != null ? detail.getProtein() : 0;
                double carbs = detail.getCarbs() != null ? detail.getCarbs() : 0;
                double fat = detail.getFat() != null ? detail.getFat() : 0;
                
                stats.put("protein", stats.get("protein") + protein);
                stats.put("carbs", stats.get("carbs") + carbs);
                stats.put("fat", stats.get("fat") + fat);
                
                totalProtein += protein;
                totalCarbs += carbs;
                totalFat += fat;
            }
        }
        
        analysis.put("totalCalories", totalCalories);
        analysis.put("totalProtein", totalProtein);
        analysis.put("totalCarbs", totalCarbs);
        analysis.put("totalFat", totalFat);
        analysis.put("dailyStats", dailyStats);
        analysis.put("recordCount", records.size());
        
        return analysis;
    }

    @Override
    public List<Map<String, Object>> getDietTrend(Long userId, int days) {
        List<Map<String, Object>> trend = new ArrayList<>();
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(new Date());
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        
        for (int i = days - 1; i >= 0; i--) {
            calendar.add(Calendar.DAY_OF_YEAR, -1);
            Date date = calendar.getTime();
            
            List<DietRecord> records = dietRecordMapper.selectByUserIdAndDate(userId, date);
            double dailyCalories = 0;
            
            for (DietRecord record : records) {
                dailyCalories += record.getTotalCalories() != null ? record.getTotalCalories() : 0;
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
        
        for (DietRecord record : records) {
            totalCalories += record.getTotalCalories() != null ? record.getTotalCalories() : 0;
            
            List<DietRecordDetail> details = dietRecordDetailMapper.selectByRecordId(record.getId());
            for (DietRecordDetail detail : details) {
                totalProtein += detail.getProtein() != null ? detail.getProtein() : 0;
                totalCarbs += detail.getCarbs() != null ? detail.getCarbs() : 0;
                totalFat += detail.getFat() != null ? detail.getFat() : 0;
            }
        }
        
        nutrition.put("calories", totalCalories);
        nutrition.put("protein", totalProtein);
        nutrition.put("carbs", totalCarbs);
        nutrition.put("fat", totalFat);
        
        return nutrition;
    }

    @Override
    public List<String> getDietSuggestions(Long userId) {
        List<String> suggestions = new ArrayList<>();
        List<String> warnings = new ArrayList<>();
        
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
            Date endDate = new Date();
            Calendar cal = Calendar.getInstance();
            cal.add(Calendar.DAY_OF_MONTH, -7);
            Date startDate = cal.getTime();
            
            List<DietRecord> records = getDietRecordsByDateRange(userId, startDate, endDate);
            
            if (records == null || records.isEmpty()) {
                suggestions.add("保持饮食均衡，摄入多样化的食物");
                suggestions.add("增加蔬菜水果的摄入量");
                suggestions.add("控制油脂和盐分的摄入");
                suggestions.add("保持足够的水分摄入");
                suggestions.add("规律饮食，避免暴饮暴食");
                return suggestions;
            }
            
            double totalCalories = 0;
            double totalProtein = 0;
            double totalCarbs = 0;
            double totalFat = 0;
            int recordCount = 0;
            
            for (DietRecord record : records) {
                totalCalories += record.getTotalCalories() != null ? record.getTotalCalories() : 0;
                List<DietRecordDetail> details = getDietRecordDetails(record.getId());
                for (DietRecordDetail detail : details) {
                    totalProtein += detail.getProtein() != null ? detail.getProtein() : 0;
                    totalCarbs += detail.getCarbs() != null ? detail.getCarbs() : 0;
                    totalFat += detail.getFat() != null ? detail.getFat() : 0;
                }
                recordCount++;
            }
            
            double avgCalories = recordCount > 0 ? totalCalories / recordCount : 0;
            double avgProtein = recordCount > 0 ? totalProtein / recordCount : 0;
            double avgCarbs = recordCount > 0 ? totalCarbs / recordCount : 0;
            double avgFat = recordCount > 0 ? totalFat / recordCount : 0;
            
            if (avgCalories > 2500) {
                warnings.add("⚠️ 您最近7天的平均热量摄入偏高(" + String.format("%.0f", avgCalories) + "kcal)，建议适当控制");
            } else if (avgCalories < 1200) {
                warnings.add("⚠️ 您最近7天的平均热量摄入偏低(" + String.format("%.0f", avgCalories) + "kcal)，注意营养补充");
            } else {
                suggestions.add("✓ 热量摄入保持在合理范围内");
            }
            
            if (avgFat > 80) {
                warnings.add("⚠️ 脂肪摄入偏高，建议减少油炸食品和高脂肪肉类");
            }
            
            if (avgCarbs > 400) {
                warnings.add("⚠️ 碳水化合物摄入偏高，建议适当减少主食量");
            }
            
            if (avgProtein < 50) {
                warnings.add("⚠️ 蛋白质摄入不足，建议增加蛋奶肉类的摄入");
            }
            
            if (recordCount < 5) {
                warnings.add("📝 饮食记录较少，建议每天记录饮食以便更好地分析");
            }
            
            suggestions.add("保持饮食均衡，摄入多样化的食物");
            suggestions.add("增加蔬菜水果的摄入量");
            suggestions.add("控制油脂和盐分的摄入");
            suggestions.add("保持足够的水分摄入");
            suggestions.add("规律饮食，避免暴饮暴食");
            
            List<String> result = new ArrayList<>();
            result.addAll(warnings);
            result.addAll(suggestions);
            return result;
            
        } catch (Exception e) {
            log.error("生成饮食建议失败: {}", e.getMessage());
            suggestions.add("保持饮食均衡，摄入多样化的食物");
            suggestions.add("增加蔬菜水果的摄入量");
            suggestions.add("控制油脂和盐分的摄入");
            suggestions.add("保持足够的水分摄入");
            suggestions.add("规律饮食，避免暴饮暴食");
            return suggestions;
        }
    }
}
