package com.health.entity;

import com.baomidou.mybatisplus.annotation.FieldStrategy;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("user")
public class User {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String username;
    private String password;
    private String email;

    private String phone;

    // ⚠️ avatar 要支持"清空"（传空串 → 存 NULL），所以必须改掉默认的字段更新策略。
    // MyBatis-Plus 的 updateById 默认策略是 NOT_NULL —— 实体里为 null 的字段
    // 根本不会进 SET 子句。于是 Service 里写 setAvatar(null) 全是白搭：
    // 内存里改了，SQL 里没有，库里纹丝不动（"这个字段一旦有值就再也删不掉"）。
    // IGNORED = 不做 null 判断，null 也照写：update user set ..., avatar = null where id = ?
    // （phone 故意不配这个：它不允许解绑，见 UserProfileUpdateDTO 的 @Pattern）
    @TableField(updateStrategy = FieldStrategy.IGNORED)
    private String avatar;

    private String role;
    private Integer status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

}
