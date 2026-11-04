package com.health.config;

import com.health.security.JwtAuthorizationFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import javax.servlet.http.HttpServletResponse;
import java.util.Arrays;
import java.util.List;
import java.util.ArrayList;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Autowired
    private JwtAuthorizationFilter jwtAuthorizationFilter;

    @Value("${cors.allowed-origins:http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:5173,http://localhost:5174,http://127.0.0.1:5175,http://localhost:5175}")
    private String corsAllowedOrigins;

    @Value("${cors.allow-all-origins:false}")
    private boolean corsAllowAllOrigins;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration authConfig) throws Exception {
        return authConfig.getAuthenticationManager();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();

        if (corsAllowAllOrigins) {
            configuration.setAllowedOriginPatterns(Arrays.asList("*"));
        } else {
            List<String> origins = new ArrayList<>();
            for (String origin : corsAllowedOrigins.split(",")) {
                String trimmed = origin.trim();
                if (!trimmed.isEmpty()) {
                    origins.add(trimmed);
                }
            }
            configuration.setAllowedOrigins(origins);
        }

        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"));
        configuration.setAllowedHeaders(Arrays.asList("*"));
        configuration.setAllowCredentials(true);
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }

    /**
     * 权限不足（403）的统一响应。
     *
     * 原先用 response.sendError(SC_FORBIDDEN, "Forbidden")，
     * 这会把请求交给 Spring 的默认错误页，返回：
     *   {"timestamp":"...","status":403,"error":"Forbidden","path":"/api/admin/overview"}
     * —— 不是项目约定的信封 { code, message, data }，
     * 而且 message 是英文，前端 http.js 的兜底会把 "Forbidden" 直接展示给用户。
     *
     * 现在直接写 JSON，与其它接口保持一致，中文提示对用户友好。
     */
    @Bean
    public AccessDeniedHandler accessDeniedHandler() {
        return (request, response, accessDeniedException) -> {
            response.setStatus(HttpServletResponse.SC_FORBIDDEN);
            response.setContentType("application/json;charset=UTF-8");
            response.setCharacterEncoding("UTF-8");
            response.getWriter().write(
                "{\"code\":403,\"message\":\"当前账号没有该操作权限，请使用管理员账号登录\",\"data\":null}"
            );
        };
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .cors().and()
            .csrf().disable()
            .exceptionHandling()
            /*
             * 未认证（401）同样返回统一信封。
             * HttpStatusEntryPoint 只设状态码、不给响应体，
             * 前端 http.js 虽然对 401 有专门分支，但响应体为空会让
             * 调试时看不到任何原因。这里换成自定义 entryPoint。
             */
            .authenticationEntryPoint((request, response, authException) -> {
                response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                response.setContentType("application/json;charset=UTF-8");
                response.setCharacterEncoding("UTF-8");
                response.getWriter().write(
                    "{\"code\":401,\"message\":\"登录已过期，请重新登录\",\"data\":null}"
                );
            })
            .accessDeniedHandler(accessDeniedHandler())
            .and()
            .authorizeRequests()
            .antMatchers(HttpMethod.OPTIONS, "/**").permitAll()
            .antMatchers("/auth/**", "/api/auth/**").permitAll()
            .antMatchers("/public/**", "/api/public/**").permitAll()
            .antMatchers(
                "/admin/**",
                "/api/admin/**",
                "/user/admin/**",
                "/api/user/admin/**",
                "/notification/admin/**",
                "/api/notification/admin/**",
                "/article/admin/**",
                "/api/article/admin/**"
            ).hasRole("ADMIN")
            .anyRequest().authenticated()
            .and()
            .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .addFilterBefore(jwtAuthorizationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
