package com.health.dto;

import lombok.Data;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

@Data
public class HealthInfoDTO {

    @NotNull(message = "年龄不能为空")
    private Integer age;

    @NotBlank(message = "性别不能为空")
    private String gender;

    @NotNull(message = "身高不能为空")
    private Double height;

    @NotNull(message = "体重不能为空")
    private Double weight;

    private Double waistCircumference;
    private Double bmi;
    private Double bmr;
    private String bloodType;
    private String bloodPressure;
    private Double bloodSugar;
    private String activityLevel;
    private Integer exerciseDuration;
    private String exerciseType;
    private String allergies;
    private String chronicDiseases;
    private String healthCondition;

}
