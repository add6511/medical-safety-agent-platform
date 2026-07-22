package com.medicalsafety.platform.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medicalsafety.platform.dto.LoginRequest;
import com.medicalsafety.platform.entity.Role;
import com.medicalsafety.platform.entity.User;
import com.medicalsafety.platform.entity.UserRole;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.enums.UserStatus;
import com.medicalsafety.platform.repository.RoleRepository;
import com.medicalsafety.platform.repository.UserRepository;
import com.medicalsafety.platform.repository.UserRoleRepository;
import com.medicalsafety.platform.security.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class AuthControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private UserRoleRepository userRoleRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    private Role adminRole;
    private Role patientRole;

    @BeforeEach
    void setUp() {
        adminRole = roleRepository.findByName(RoleType.ADMIN)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.ADMIN).description("管理员").build()));
        patientRole = roleRepository.findByName(RoleType.PATIENT)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.PATIENT).description("患者模拟用户").build()));
        roleRepository.findByName(RoleType.MEDICAL_STAFF)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.MEDICAL_STAFF).description("医务人员").build()));
        roleRepository.findByName(RoleType.FOLLOWUP_STAFF)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.FOLLOWUP_STAFF).description("随访人员").build()));
    }

    private User createTestUser(String username, String password, UserStatus status, Role role) {
        User user = userRepository.save(User.builder()
                .username(username)
                .passwordHash(passwordEncoder.encode(password))
                .displayName(username)
                .status(status)
                .build());
        userRoleRepository.save(UserRole.builder().user(user).role(role).build());
        return user;
    }

    @Test
    void loginSuccess() throws Exception {
        createTestUser("demo_admin", "password", UserStatus.ENABLED, adminRole);

        LoginRequest request = LoginRequest.builder().username("demo_admin").password("password").build();

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.tokenType").value("Bearer"))
                .andExpect(jsonPath("$.expiresIn").isNumber())
                .andExpect(jsonPath("$.userId").isNumber())
                .andExpect(jsonPath("$.username").value("demo_admin"))
                .andExpect(jsonPath("$.roles", hasItem("ADMIN")));
    }

    @Test
    void loginFailure() throws Exception {
        LoginRequest request = LoginRequest.builder().username("nonexistent").password("password").build();

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.errorCode").value("AUTHENTICATION_FAILED"));
    }

    @Test
    void loginWithWrongPassword() throws Exception {
        createTestUser("demo_admin2", "password", UserStatus.ENABLED, adminRole);

        LoginRequest request = LoginRequest.builder().username("demo_admin2").password("wrongpassword").build();

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void disabledUserCannotLogin() throws Exception {
        createTestUser("disabled_user", "password", UserStatus.DISABLED, patientRole);

        LoginRequest request = LoginRequest.builder().username("disabled_user").password("password").build();

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticatedAccessReturns401() throws Exception {
        mockMvc.perform(get("/api/v1/auth/me"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void authenticatedAccessToMe() throws Exception {
        User user = createTestUser("me_user", "password", UserStatus.ENABLED, adminRole);
        String token = jwtTokenProvider.generateToken(user.getId(), user.getUsername(), List.of("ADMIN"));

        mockMvc.perform(get("/api/v1/auth/me")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("me_user"))
                .andExpect(jsonPath("$.roles", hasItem("ADMIN")));
    }

    @Test
    void validationErrorReturns400() throws Exception {
        LoginRequest request = LoginRequest.builder().username("").password("").build();

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.errorCode").value("VALIDATION_ERROR"));
    }

    @Test
    void errorResponseStructure() throws Exception {
        LoginRequest request = LoginRequest.builder().username("nonexistent").password("password").build();

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.timestamp").isNotEmpty())
                .andExpect(jsonPath("$.status").isNumber())
                .andExpect(jsonPath("$.errorCode").isNotEmpty())
                .andExpect(jsonPath("$.message").isNotEmpty())
                .andExpect(jsonPath("$.path").isNotEmpty())
                .andExpect(jsonPath("$.traceId").isNotEmpty());
    }
}