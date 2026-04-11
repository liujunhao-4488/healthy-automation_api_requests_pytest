package com.health.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("user_diet_preference")
public class UserDietPreference {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String dietType;
    private String allergies;
    private String dislikes;
    private String favorites;
    private Integer mealFrequency;
    private Integer snackPreference;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
