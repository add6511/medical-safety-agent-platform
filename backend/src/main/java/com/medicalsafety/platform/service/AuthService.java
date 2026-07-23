package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.LoginRequest;
import com.medicalsafety.platform.dto.LoginResponse;
import com.medicalsafety.platform.dto.UserInfoResponse;
import com.medicalsafety.platform.entity.User;
import com.medicalsafety.platform.enums.UserStatus;
import com.medicalsafety.platform.repository.UserRepository;
import com.medicalsafety.platform.repository.UserRoleRepository;
import com.medicalsafety.platform.security.JwtTokenProvider;
import com.medicalsafety.platform.security.SecurityAuditLogger;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final UserRoleRepository userRoleRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final SecurityAuditLogger auditLogger;

    public LoginResponse login(LoginRequest request) {
        User user = userRepository.findByUsername(request.getUsername()).orElse(null);

        if (user == null) {
            auditLogger.logLoginFailed(request.getUsername(), "用户不存在");
            throw new com.medicalsafety.platform.exception.AuthenticationException("用户名或密码错误");
        }

        if (user.getStatus() == UserStatus.DISABLED) {
            auditLogger.logDisabledUserLogin(request.getUsername());
            throw new com.medicalsafety.platform.exception.AuthenticationException("用户名或密码错误");
        }

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            auditLogger.logLoginFailed(request.getUsername(), "密码错误");
            throw new com.medicalsafety.platform.exception.AuthenticationException("用户名或密码错误");
        }

        List<String> roles = getUserRoles(user.getId());
        String token = jwtTokenProvider.generateToken(user.getId(), user.getUsername(), roles);

        auditLogger.logLoginSuccess(user.getUsername());

        return LoginResponse.builder()
                .accessToken(token)
                .tokenType("Bearer")
                .expiresIn(jwtTokenProvider.getExpiration() / 1000)
                .userId(user.getId())
                .username(user.getUsername())
                .roles(roles)
                .build();
    }

    public UserInfoResponse getCurrentUser(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new com.medicalsafety.platform.exception.ResourceNotFoundException("用户不存在"));

        List<String> roles = getUserRoles(user.getId());

        return UserInfoResponse.builder()
                .userId(user.getId())
                .username(user.getUsername())
                .displayName(user.getDisplayName())
                .caseCode(user.getCaseCode())
                .status(user.getStatus().name())
                .roles(roles)
                .build();
    }

    private List<String> getUserRoles(Long userId) {
        return userRoleRepository.findByUserId(userId).stream()
                .map(ur -> ur.getRole().getName().name())
                .toList();
    }
}