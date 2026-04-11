package com.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.health.entity.Ingredient;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 食材Mapper接口
 */
@Mapper
public interface IngredientMapper extends BaseMapper<Ingredient> {

    /**
     * 根据分类查询食材
     * @param category 食材分类
     * @return 食材列表
     */
    @Select("SELECT * FROM ingredient WHERE status = 1 AND category = #{category} ORDER BY update_time DESC, id DESC")
    List<Ingredient> selectByCategory(@Param("category") String category);

    /**
     * 根据名称模糊查询食材
     * @param name 食材名称
     * @return 食材列表
     */
    @Select("SELECT * FROM ingredient WHERE status = 1 AND name LIKE #{name} ORDER BY update_time DESC, id DESC")
    List<Ingredient> selectByNameLike(@Param("name") String name);
}
