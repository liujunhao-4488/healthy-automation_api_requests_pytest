package com.health.dto;

import lombok.Data;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.time.LocalDate;
import java.time.LocalTime;

@Data
public class DietGoalDTO {

    @NotBlank(message = "目标类型不能为空")
    private String goalType;

    private Double targetWeight;

    @NotNull(message = "目标卡路里不能为空")
    private Double targetCalories;

    private Double proteinRatio;
    private Double carbsRatio;
    private Double fatRatio;
    private Double proteinTarget;
    private Double carbsTarget;
    private Double fatTarget;
    private Integer waterTarget;
    private Integer status;

    @NotNull(message = "开始日期不能为空")
    private LocalDate startDate;

    private LocalDate endDate;
    private Integer reminderEnabled;
    private LocalTime reminderTime;

}
