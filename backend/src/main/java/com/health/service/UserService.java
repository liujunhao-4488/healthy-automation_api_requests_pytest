package com.health.service;

import com.health.entity.User;
import com.health.dto.UserRegisterDTO;
import com.health.dto.UserLoginDTO;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;

public interface UserService extends UserDetailsService {

    // 用户注册
    User register(UserRegisterDTO registerDTO);

    // 用户登录
    String login(UserLoginDTO loginDTO);

    // 根据用户 ID 加载用户信息
    UserDetails loadUserByUserId(Long userId);

    // 根据邮箱查询用户
    User findByEmail(String email);

    // 根据用户 ID 查询用户
    User findById(Long id);

}
