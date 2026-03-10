package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.DietRecord;
import java.util.List;
import java.util.Date;

/**
 * 饮食记录Mapper接口
 */
public interface DietRecordMapper extends BaseMapper<DietRecord> {

    /**
     * 根据用户ID和日期查询饮食记录
     * @param userId 用户ID
     * @param recordDate 记录日期
     * @return 饮食记录列表
     */
    List<DietRecord> selectByUserIdAndDate(Long userId, Date recordDate);

    /**
     * 查询用户指定日期范围内的饮食记录
     * @param userId 用户ID
     * @param startDate 开始日期
     * @param endDate 结束日期
     * @return 饮食记录列表
     */
    List<DietRecord> selectByUserIdAndDateRange(Long userId, Date startDate, Date endDate);

    /**
     * 根据用户ID和餐型查询饮食记录
     * @param userId 用户ID
     * @param mealType 餐型
     * @param startDate 开始日期
     * @param endDate 结束日期
     * @return 饮食记录列表
     */
    List<DietRecord> selectByUserIdAndMealType(Long userId, String mealType, Date startDate, Date endDate);
}
