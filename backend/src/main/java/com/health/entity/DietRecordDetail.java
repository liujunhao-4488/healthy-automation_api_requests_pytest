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

    /*
     * 2026-11-02 修复：fiber / sugar / sodium / gi 原先标了 @TableField(exist = false)，
     * MyBatis-Plus 认为数据库里没有这些列，insert 时直接跳过，select 也不回填。
     *
     * 实际后果（联调实测）：
     *   提交明细 fiber=7.77 → submit 响应里 totalFiber=7.77（内存对象是对的）
     *   → 但重新 GET /record/list，明细 fiber 一律 0.0，totalFiber 也跟着变 0。
     *   膳食纤维、糖、钠、GI 这四项从来没进过库。
     *
     * 修复：给 diet_record_detail 表补上这四列（health_diet 与 health_diet_test
     * 均已执行 ALTER TABLE，老数据为 NULL），然后去掉注解，
     * 让这四个字段正常参与 insert / select。
     */
    private Double fiber;

    private Long recipeId;
    private Integer isCustom;
    private Integer isDeleted;

    private Double sugar;

    private Double sodium;

    private Double gi;

}
