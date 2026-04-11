package com.health.dto;

import lombok.Data;

import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;

@Data
public class UserProfileUpdateDTO {

    @Size(min = 1, max = 50, message = "用户名长度需在 1 到 50 个字符之间")
    private String username;

    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;

    @Size(max = 4194304, message = "头像内容不能超过 4MB")
    private String avatar;
}
