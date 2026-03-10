package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.Ingredient;
import java.util.List;

/**
 * 食材Mapper接口
 */
public interface IngredientMapper extends BaseMapper<Ingredient> {

    /**
     * 根据分类查询食材
     * @param category 食材分类
     * @return 食材列表
     */
    List<Ingredient> selectByCategory(String category);

    /**
     * 根据名称模糊查询食材
     * @param name 食材名称
     * @return 食材列表
     */
    List<Ingredient> selectByNameLike(String name);
}
