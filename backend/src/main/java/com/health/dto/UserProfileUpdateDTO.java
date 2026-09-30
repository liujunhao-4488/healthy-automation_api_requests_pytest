package com.health.dto;

import lombok.Data;

import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;

@Data
public class UserProfileUpdateDTO {

    @Size(min = 1, max = 50, message = "用户名长度需在 1 到 50 个字符之间")
    private String username;

    // ⚠️ 故意不放行空串：手机号一旦绑定就不可解绑（解绑=业务上想不出来的场景，
    //    真要做得单独开接口，而不是让"空字符串"兼职）。null 的语义是"这个字段不改"。
    // 注意 @Pattern 只对 null 放行，空串是要参与匹配的 —— 所以 "" 会在这里被拦成 400，
    // 而不是走到 Service 里那个"清空"分支。
    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;

    @Size(max = 4194304, message = "头像内容不能超过 4MB")
    private String avatar;
}
