package com.health.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("recipe")
public class Recipe {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String description;
    private String category;
    private String cuisineType;
    private Integer cookingTime;
    private String difficulty;
    private Integer servings;
    private Double totalCalories;
    private Double caloriesPerServing;
    private Double protein;
    private Double carbs;
    private Double fat;
    private Double fiber;
    private String instructions;
    private String tips;
    private String imageUrl;
    private Long creatorId;
    private Integer isCustom;
    private Double score;
    private Integer scoreCount;
    private Integer viewCount;
    private Integer collectCount;
    private String suitableFor;
    private String goalType;
    private Integer status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

    @TableField(exist = false)
    private Double sugar;

    @TableField(exist = false)
    private Double sodium;

    @TableField(exist = false)
    private Double gi;

}
