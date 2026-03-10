package com.health.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;
import java.time.LocalDate;
import java.time.LocalTime;

@Data
@TableName("diet_goal")
public class DietGoal {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String goalType;
    private Double targetWeight;
    private Double targetCalories;
    private Double proteinRatio;
    private Double carbsRatio;
    private Double fatRatio;
    private Double proteinTarget;
    private Double carbsTarget;
    private Double fatTarget;
    private Integer waterTarget;
    private Integer status;
    private LocalDate startDate;
    private LocalDate endDate;
    private Integer reminderEnabled;
    private LocalTime reminderTime;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

}
