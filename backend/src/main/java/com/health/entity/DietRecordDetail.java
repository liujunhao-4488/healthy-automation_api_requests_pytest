package com.health.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableField;
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
    private Double quantity;
    private String unit;
    private Double calories;
    private Double protein;
    private Double carbs;
    private Double fat;

    @TableField(exist = false)
    private Double fiber;

    private Long recipeId;
    private Integer isCustom;
    private Integer isDeleted;

    @TableField(exist = false)
    private Double sugar;

    @TableField(exist = false)
    private Double sodium;

    @TableField(exist = false)
    private Double gi;

}
