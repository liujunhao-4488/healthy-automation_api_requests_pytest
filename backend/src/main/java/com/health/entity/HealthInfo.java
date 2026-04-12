package com.health.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("health_info")
public class HealthInfo {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Integer age;
    private String gender;
    private Double height;
    private Double weight;
    private Double bmi;
    private Double bmr;
    private String bloodPressure;
    private Double bloodSugar;
    private String activityLevel;
    private Integer exerciseDuration;
    private String exerciseType;
    private String chronicDiseases;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

}
