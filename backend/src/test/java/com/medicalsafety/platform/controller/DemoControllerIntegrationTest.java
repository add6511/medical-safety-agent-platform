package com.medicalsafety.platform.controller;

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
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class DemoControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

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

    @BeforeEach
    void setUp() {
        for (RoleType type : RoleType.values()) {
            roleRepository.findByName(type)
                    .orElseGet(() -> roleRepository.save(Role.builder().name(type).description(type.name()).build()));
        }
    }

    private String createTokenForRole(String username, RoleType roleType) {
        User user = userRepository.save(User.builder()
                .username(username)
                .passwordHash(passwordEncoder.encode("password"))
                .displayName(username)
                .status(UserStatus.ENABLED)
                .build());
        Role role = roleRepository.findByName(roleType).orElseThrow();
        userRoleRepository.save(UserRole.builder().user(user).role(role).build());
        return jwtTokenProvider.generateToken(user.getId(), user.getUsername(), List.of(roleType.name()));
    }

    @Test
    void patientCanAccessPatientEndpoint() throws Exception {
        String token = createTokenForRole("patient_user", RoleType.PATIENT);
        mockMvc.perform(get("/api/v1/demo/patient").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.role").value("PATIENT"));
    }

    @Test
    void medicalStaffCanAccessMedicalEndpoint() throws Exception {
        String token = createTokenForRole("medical_user", RoleType.MEDICAL_STAFF);
        mockMvc.perform(get("/api/v1/demo/medical").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.role").value("MEDICAL_STAFF"));
    }

    @Test
    void followupStaffCanAccessFollowupEndpoint() throws Exception {
        String token = createTokenForRole("followup_user", RoleType.FOLLOWUP_STAFF);
        mockMvc.perform(get("/api/v1/demo/followup").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.role").value("FOLLOWUP_STAFF"));
    }

    @Test
    void adminCanAccessAdminEndpoint() throws Exception {
        String token = createTokenForRole("admin_user", RoleType.ADMIN);
        mockMvc.perform(get("/api/v1/demo/admin").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.role").value("ADMIN"));
    }

    @Test
    void patientCannotAccessAdminEndpoint() throws Exception {
        String token = createTokenForRole("patient_user2", RoleType.PATIENT);
        mockMvc.perform(get("/api/v1/demo/admin").header("Authorization", "Bearer " + token))
                .andExpect(status().isForbidden());
    }

    @Test
    void unauthenticatedCannotAccessDemoEndpoint() throws Exception {
        mockMvc.perform(get("/api/v1/demo/admin"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void invalidTokenReturns401() throws Exception {
        mockMvc.perform(get("/api/v1/demo/admin").header("Authorization", "Bearer invalid.token.here"))
                .andExpect(status().isUnauthorized());
    }
}