package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.DietRecordDetail;
import java.util.List;

/**
 * 饮食记录详情Mapper接口
 */
public interface DietRecordDetailMapper extends BaseMapper<DietRecordDetail> {

    /**
     * 根据记录ID查询详情
     * @param recordId 记录ID
     * @return 详情列表
     */
    List<DietRecordDetail> selectByRecordId(Long recordId);

    /**
     * 根据食谱ID查询详情
     * @param recipeId 食谱ID
     * @return 详情列表
     */
    List<DietRecordDetail> selectByRecipeId(Long recipeId);
}
