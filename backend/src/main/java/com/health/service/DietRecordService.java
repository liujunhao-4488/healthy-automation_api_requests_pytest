package com.health.service;

import com.health.entity.DietRecord;
import com.health.entity.DietRecordDetail;
import java.util.List;
import java.util.Map;
import java.util.Date;

/**
 * 饮食记录服务接口
 */
public interface DietRecordService {

    /**
     * 保存饮食记录
     * @param record 饮食记录
     * @param details 记录详情
     * @return 保存后的饮食记录
     */
    DietRecord saveDietRecord(DietRecord record, List<DietRecordDetail> details);

    /**
     * 保存饮食记录（根据用户ID和记录数据）
     * @param userId 用户ID
     * @param recordData 记录数据
     * @return 保存后的饮食记录
     */
    DietRecord saveDietRecord(Long userId, Map<String, Object> recordData);

    /**
     * 更新饮食记录
     * @param record 饮食记录
     * @param details 记录详情
     * @return 更新后的饮食记录
     */
    DietRecord updateDietRecord(DietRecord record, List<DietRecordDetail> details);

    /**
     * 删除饮食记录
     * @param id 记录ID
     * @return 是否删除成功
     */
    boolean deleteDietRecord(Long id);

    /**
     * 删除饮食记录（验证用户权限）
     * @param recordId 记录ID
     * @param userId 用户ID
     * @return 是否删除成功
     */
    boolean deleteDietRecord(Long recordId, Long userId);

    /**
     * 根据ID获取饮食记录
     * @param id 记录ID
     * @return 饮食记录
     */
    DietRecord getDietRecordById(Long id);

    /**
     * 获取饮食记录详情
     * @param recordId 记录ID
     * @return 记录详情列表
     */
    List<DietRecordDetail> getDietRecordDetails(Long recordId);

    /**
     * 获取饮食记录详情（验证用户权限）
     * @param recordId 记录ID
     * @param userId 用户ID
     * @return 记录详情列表
     */
    List<DietRecordDetail> getDietRecordDetails(Long recordId, Long userId);

    /**
     * 获取用户当日饮食记录
     * @param userId 用户ID
     * @param date 日期
     * @return 饮食记录列表
     */
    List<DietRecord> getDietRecordsByDate(Long userId, Date date);

    /**
     * 获取用户指定日期范围的饮食记录
     * @param userId 用户ID
     * @param startDate 开始日期
     * @param endDate 结束日期
     * @return 饮食记录列表
     */
    List<DietRecord> getDietRecordsByDateRange(Long userId, Date startDate, Date endDate);

    /**
     * 获取用户饮食记录列表
     * @param userId 用户ID
     * @param startDateStr 开始日期字符串
     * @param endDateStr 结束日期字符串
     * @param page 页码
     * @param pageSize 每页大小
     * @return 饮食记录列表
     */
    List<DietRecord> getDietRecordsByUserId(Long userId, String startDateStr, String endDateStr, Integer page, Integer pageSize);

    /**
     * 分析用户饮食摄入
     * @param userId 用户ID
     * @param startDate 开始日期
     * @param endDate 结束日期
     * @return 饮食分析结果
     */
    Map<String, Object> analyzeDietIntake(Long userId, Date startDate, Date endDate);

    /**
     * 获取饮食趋势分析
     * @param userId 用户ID
     * @param startDateStr 开始日期字符串
     * @param endDateStr 结束日期字符串
     * @return 饮食趋势分析结果
     */
    Map<String, Object> getDietTrendAnalysis(Long userId, String startDateStr, String endDateStr);

    /**
     * 获取用户饮食趋势
     * @param userId 用户ID
     * @param days 天数
     * @return 饮食趋势数据
     */
    List<Map<String, Object>> getDietTrend(Long userId, int days);

    /**
     * 计算用户每日营养摄入总和
     * @param userId 用户ID
     * @param date 日期
     * @return 营养摄入总和
     */
    Map<String, Double> calculateDailyNutrition(Long userId, Date date);

    /**
     * 获取用户饮食建议
     * @param userId 用户ID
     * @return 饮食建议
     */
    List<String> getDietSuggestions(Long userId);
}
