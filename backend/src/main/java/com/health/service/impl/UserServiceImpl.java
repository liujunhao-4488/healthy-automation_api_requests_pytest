package com.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.health.dto.UserLoginDTO;
import com.health.dto.UserProfileUpdateDTO;
import com.health.dto.UserRegisterDTO;
import com.health.entity.User;
import com.health.mapper.UserMapper;
import com.health.service.UserService;
import com.health.utils.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;

@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {

    private static final String ROLE_ADMIN = "admin";
    private static final String ROLE_USER = "user";

    @Autowired
    private UserMapper userMapper;

    @Lazy
    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtUtil jwtUtil;

    @Override
    public User register(UserRegisterDTO registerDTO) {
        if (userMapper.selectOne(new QueryWrapper<User>().eq("username", registerDTO.getUsername())) != null) {
            throw new RuntimeException("用户名已存在");
        }

        if (userMapper.selectOne(new QueryWrapper<User>().eq("email", registerDTO.getEmail())) != null) {
            throw new RuntimeException("邮箱已被注册");
        }

        User user = new User();
        user.setUsername(registerDTO.getUsername());
        user.setPassword(passwordEncoder.encode(registerDTO.getPassword()));
        user.setEmail(registerDTO.getEmail());
        user.setPhone(registerDTO.getPhone());
        user.setRole(ROLE_USER);
        user.setStatus(1);

        userMapper.insert(user);
        return user;
    }

    @Override
    public String login(UserLoginDTO loginDTO) {
        User user = findByEmail(loginDTO.getEmail());
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        if (user.getStatus() != null && user.getStatus() == 0) {
            throw new RuntimeException("账号已被禁用");
        }

        if (!passwordEncoder.matches(loginDTO.getPassword(), user.getPassword())) {
            throw new RuntimeException("密码错误");
        }

        return jwtUtil.generateToken(user.getId());
    }

    @Override
    public UserDetails loadUserByUserId(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new UsernameNotFoundException("用户不存在");
        }
        return new org.springframework.security.core.userdetails.User(
            user.getUsername(),
            user.getPassword(),
            Collections.singletonList(new SimpleGrantedAuthority(isAdmin(user) ? "ROLE_ADMIN" : "ROLE_USER"))
        );
    }

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        User user = findByEmail(email);
        if (user == null) {
            throw new UsernameNotFoundException("用户不存在");
        }
        return new org.springframework.security.core.userdetails.User(
            user.getUsername(),
            user.getPassword(),
            Collections.singletonList(new SimpleGrantedAuthority(isAdmin(user) ? "ROLE_ADMIN" : "ROLE_USER"))
        );
    }

    @Override
    public User findByEmail(String email) {
        return userMapper.selectOne(new QueryWrapper<User>().eq("email", email));
    }

    @Override
    public User findById(Long id) {
        return userMapper.selectById(id);
    }

    @Override
    public User updateProfile(Long userId, UserProfileUpdateDTO profileDTO) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        if (profileDTO.getUsername() != null && !profileDTO.getUsername().trim().isEmpty()) {
            String nextUsername = profileDTO.getUsername().trim();
            User existingUser = userMapper.selectOne(new QueryWrapper<User>().eq("username", nextUsername));
            if (existingUser != null && !existingUser.getId().equals(userId)) {
                throw new RuntimeException("用户名已存在");
            }
            user.setUsername(nextUsername);
        }

        if (profileDTO.getPhone() != null) {
            String nextPhone = profileDTO.getPhone().trim();
            user.setPhone(nextPhone.isEmpty() ? null : nextPhone);
        }

        if (profileDTO.getAvatar() != null) {
            String nextAvatar = profileDTO.getAvatar().trim();
            user.setAvatar(nextAvatar.isEmpty() ? null : nextAvatar);
        }

        userMapper.updateById(user);
        return userMapper.selectById(userId);
    }

    @Override
    public List<User> listUsers() {
        return userMapper.selectList(new QueryWrapper<User>().orderByDesc("create_time"));
    }

    @Override
    public User updateUserStatus(Long userId, Integer status) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        if (isAdmin(user) && status != null && status == 0) {
            throw new RuntimeException("管理员账号不能被禁用");
        }

        user.setStatus(status);
        userMapper.updateById(user);
        return userMapper.selectById(userId);
    }

    @Override
    public String resolveRole(User user) {
        if (user == null) {
            return ROLE_USER;
        }
        return ROLE_ADMIN.equalsIgnoreCase(String.valueOf(user.getRole())) ? ROLE_ADMIN : ROLE_USER;
    }

    @Override
    public boolean isAdmin(User user) {
        return ROLE_ADMIN.equals(resolveRole(user));
    }
}
