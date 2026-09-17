package com.health.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("ingredient")
public class Ingredient {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String category;
    private String subCategory;
    @TableField("calories_per_100g")
    private Double caloriesPer100g;
    @TableField("protein_per_100g")
    private Double proteinPer100g;
    @TableField("carbs_per_100g")
    private Double carbsPer100g;
    @TableField("fat_per_100g")
    private Double fatPer100g;
    @TableField("fiber_per_100g")
    private Double fiberPer100g;
    @TableField("sugar_per_100g")
    private Double sugarPer100g;
    @TableField("sodium_per_100g")
    private Double sodiumPer100g;
    private Integer giValue;
    @TableField("cholesterol_per_100g")
    private Double cholesterolPer100g;
    private String description;
    private String imageUrl;
    private Integer status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

}
