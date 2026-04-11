package com.health.service;

import com.health.dto.UserLoginDTO;
import com.health.dto.UserProfileUpdateDTO;
import com.health.dto.UserRegisterDTO;
import com.health.entity.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;

import java.util.List;

public interface UserService extends UserDetailsService {

    User register(UserRegisterDTO registerDTO);

    String login(UserLoginDTO loginDTO);

    UserDetails loadUserByUserId(Long userId);

    User findByEmail(String email);

    User findById(Long id);

    User updateProfile(Long userId, UserProfileUpdateDTO profileDTO);

    List<User> listUsers();

    User updateUserStatus(Long userId, Integer status);

    boolean isAdmin(User user);
}
