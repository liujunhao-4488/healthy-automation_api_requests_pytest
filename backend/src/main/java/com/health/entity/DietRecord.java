package com.health.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;
import java.util.Date;
import java.util.List;

@Data
@TableName("diet_record")
public class DietRecord {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Date recordDate;
    private String mealType;
    private Double totalCalories;
    private Double totalProtein;
    private Double totalCarbs;
    private Double totalFat;
    private String notes;
    private Integer isDeleted;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

    @TableField(exist = false)
    private List<DietRecordDetail> details;

    @TableField(exist = false)
    private String mealName;

    @TableField(exist = false)
    private Double totalFiber;

    @TableField(exist = false)
    private Double totalSugar;

    @TableField(exist = false)
    private Double totalSodium;

    @TableField(exist = false)
    private Double totalGi;

}
