package com.health.dto;

import lombok.Data;
import javax.validation.constraints.AssertTrue;
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

    /**
     * 跨字段业务校验：结束日期不能早于开始日期。
     *
     * 为什么用 @AssertTrue 而不是给单个字段加注解：
     *   这条规则同时依赖 startDate 和 endDate 两个字段，
     *   单字段注解（@NotNull/@Pattern 之类）表达不了"两者之间的关系"，
     *   Bean Validation 对这种场景的官方做法就是挂在 getter 上做类级校验。
     *
     * 为什么两个日期任一为空时直接放行：
     *   endDate 是可选字段（只有 goalType/targetCalories/startDate 是必填），
     *   目标可以长期有效、不设截止日期；
     *   startDate 为空的情况由字段上的 @NotNull 负责报错，这里不重复拦。
     *   （Bean Validation 规范里 null 对 @AssertTrue 视为通过，但显式写出来更好读。）
     *
     * 校验不通过时抛 MethodArgumentNotValidException，
     * 会被 GlobalExceptionHandler 统一包成 {"code":400,"message":"..."}，
     * 对外表现与必填校验完全一致，前端不用改。
     */
    @AssertTrue(message = "结束日期不能早于开始日期")
    public boolean isDateRangeValid() {
        if (startDate == null || endDate == null) {
            return true;
        }
        // 允许 endDate == startDate（当天的单日目标），只拦真正的倒挂
        return !endDate.isBefore(startDate);
    }

}
