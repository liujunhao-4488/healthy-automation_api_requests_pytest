package com.health.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("diet_record_detail")
public class DietRecordDetail {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long recordId;
    private Long ingredientId;
    private String foodName;
    private String category;
    private Double quantity;
    private String unit;
    private Double calories;
    private Double protein;
    private Double carbs;
    private Double fat;
    private Double fiber;
    private Long recipeId;
    private Integer isCustom;

}
