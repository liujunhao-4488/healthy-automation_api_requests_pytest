package com.health.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("user_recipe_collect")
public class UserRecipeCollect {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long recipeId;
    private LocalDateTime createTime;
}
