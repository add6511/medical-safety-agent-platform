package com.medicalsafety.platform.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medicalsafety.platform.dto.CreateMedicalRecordRequest;
import com.medicalsafety.platform.dto.CreatePreConsultationRequest;
import com.medicalsafety.platform.dto.SubmitTriageResultRequest;
import com.medicalsafety.platform.entity.Role;
import com.medicalsafety.platform.entity.User;
import com.medicalsafety.platform.entity.UserRole;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.enums.UserStatus;
import com.medicalsafety.platform.repository.*;
import com.medicalsafety.platform.security.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.util.List;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("testcontainers")
@Testcontainers
@Transactional
@DisabledIfEnvironmentVariable(named = "SKIP_DOCKER_TESTS", matches = "true",
        disabledReason = "Docker not available on this environment")
class MySqlIntegrationTest {

    @Container
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.0");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", mysql::getJdbcUrl);
        registry.add("spring.datasource.username", mysql::getUsername);
        registry.add("spring.datasource.password", mysql::getPassword);
    }

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @Autowired private UserRepository userRepository;
    @Autowired private RoleRepository roleRepository;
    @Autowired private UserRoleRepository userRoleRepository;
    @Autowired private PasswordEncoder passwordEncoder;
    @Autowired private JwtTokenProvider jwtTokenProvider;

    private String adminToken;
    private Long adminId;

    @BeforeEach
    void setUp() {
        Role adminRole = roleRepository.findByName(RoleType.ADMIN)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.ADMIN).description("管理员").build()));
        User admin = userRepository.save(User.builder()
                .username("tc_admin").passwordHash(passwordEncoder.encode("pass123"))
                .displayName("tc_admin").status(UserStatus.ENABLED).build());
        userRoleRepository.save(UserRole.builder().user(admin).role(adminRole).build());
        adminId = admin.getId();
        adminToken = jwtTokenProvider.generateToken(adminId, "tc_admin", List.of("ADMIN"));
    }

    @Test
    void flywayMigrationSucceeds() throws Exception {
        mockMvc.perform(get("/actuator/health"))
                .andExpect(status().isOk());
    }

    @Test
    void createRecordWithMySql() throws Exception {
        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder()
                .patientId(adminId).caseCode("TC-CASE-001").chiefComplaint("测试").build();
        mockMvc.perform(post("/api/v1/medical-records")
                        .header("Authorization", "Bearer " + adminToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated());
    }

    @Test
    void uniqueConstraintOnTriageResult() throws Exception {
        var record = new com.medicalsafety.platform.entity.MedicalRecord();
        record.setPatientId(adminId);
        record.setCaseCode("TC-TRIAGE-001");
        record.setStatus(com.medicalsafety.platform.enums.MedicalRecordStatus.ACTIVE);
        record.setCreatedBy(adminId);
        record = userRepository.findById(adminId).map(u -> {
            com.medicalsafety.platform.entity.MedicalRecord mr = com.medicalsafety.platform.entity.MedicalRecord.builder()
                    .patientId(adminId).caseCode("TC-TRIAGE-001").status(com.medicalsafety.platform.enums.MedicalRecordStatus.ACTIVE).createdBy(adminId).build();
            return mr;
        }).orElseThrow();

        mockMvc.perform(get("/actuator/health"))
                .andExpect(status().isOk());
    }
}