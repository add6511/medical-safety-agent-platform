package com.medicalsafety.platform.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medicalsafety.platform.entity.*;
import com.medicalsafety.platform.enums.*;
import com.medicalsafety.platform.repository.*;
import com.medicalsafety.platform.security.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
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
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.*;
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
    @Autowired private MedicalRecordRepository medicalRecordRepository;
    @Autowired private PreConsultationRepository preConsultationRepository;
    @Autowired private TriageResultRepository triageResultRepository;
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
    void uniqueConstraintOnTriageResultPreConsultationId() {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(adminId).caseCode("TC-UNIQUE-001")
                .status(MedicalRecordStatus.ACTIVE).createdBy(adminId).build());
        PreConsultation pc = preConsultationRepository.save(PreConsultation.builder()
                .recordId(record.getId()).patientId(adminId).initiatedBy(adminId)
                .status(PreConsultationStatus.AI_TRIAGE_COMPLETED).build());

        TriageResult result1 = TriageResult.builder()
                .preConsultationId(pc.getId())
                .urgencyLevel(UrgencyLevel.URGENT)
                .suggestedDepartment("内科")
                .build();
        triageResultRepository.save(result1);

        TriageResult result2 = TriageResult.builder()
                .preConsultationId(pc.getId())
                .urgencyLevel(UrgencyLevel.ROUTINE)
                .suggestedDepartment("外科")
                .build();

        assertThrows(DataIntegrityViolationException.class, () -> {
            triageResultRepository.saveAndFlush(result2);
        });
    }

    @Test
    void optimisticLockingFailureOnConcurrentPreConsultationUpdate() throws InterruptedException {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(adminId).caseCode("TC-OPTLOCK-001")
                .status(MedicalRecordStatus.ACTIVE).createdBy(adminId).build());
        PreConsultation pc = preConsultationRepository.save(PreConsultation.builder()
                .recordId(record.getId()).patientId(adminId).initiatedBy(adminId)
                .status(PreConsultationStatus.INITIATED).build());

        Long pcId = pc.getId();
        CountDownLatch latch = new CountDownLatch(2);
        AtomicReference<Exception> exception1 = new AtomicReference<>();
        AtomicReference<Exception> exception2 = new AtomicReference<>();

        ExecutorService executor = Executors.newFixedThreadPool(2);

        executor.submit(() -> {
            try {
                PreConsultation pc1 = preConsultationRepository.findById(pcId).orElseThrow();
                pc1.setStatus(PreConsultationStatus.SYMPTOM_COLLECTED);
                preConsultationRepository.saveAndFlush(pc1);
            } catch (Exception e) {
                exception1.set(e);
            } finally {
                latch.countDown();
            }
        });

        executor.submit(() -> {
            try {
                Thread.sleep(10);
                PreConsultation pc2 = preConsultationRepository.findById(pcId).orElseThrow();
                pc2.setStatus(PreConsultationStatus.CANCELLED);
                preConsultationRepository.saveAndFlush(pc2);
            } catch (Exception e) {
                exception2.set(e);
            } finally {
                latch.countDown();
            }
        });

        latch.await();
        executor.shutdown();

        boolean hasOptimisticLockFailure = (exception1.get() instanceof ObjectOptimisticLockingFailureException)
                || (exception2.get() instanceof ObjectOptimisticLockingFailureException);
        assertTrue(hasOptimisticLockFailure, "应该有乐观锁冲突异常");
    }

    @Test
    void preConsultationVersionColumnExists() {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(adminId).caseCode("TC-VERSION-001")
                .status(MedicalRecordStatus.ACTIVE).createdBy(adminId).build());
        PreConsultation pc = preConsultationRepository.save(PreConsultation.builder()
                .recordId(record.getId()).patientId(adminId).initiatedBy(adminId)
                .status(PreConsultationStatus.INITIATED).build());

        assertNotNull(pc.getVersion());

        pc.setStatus(PreConsultationStatus.SYMPTOM_COLLECTED);
        pc = preConsultationRepository.saveAndFlush(pc);

        assertTrue(pc.getVersion() >= 0);
    }

    @Test
    void triageResultUpdatedAtColumnExists() {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(adminId).caseCode("TC-UPDATED-001")
                .status(MedicalRecordStatus.ACTIVE).createdBy(adminId).build());
        PreConsultation pc = preConsultationRepository.save(PreConsultation.builder()
                .recordId(record.getId()).patientId(adminId).initiatedBy(adminId)
                .status(PreConsultationStatus.AI_TRIAGE_COMPLETED).build());

        TriageResult result = TriageResult.builder()
                .preConsultationId(pc.getId())
                .urgencyLevel(UrgencyLevel.URGENT)
                .build();
        result = triageResultRepository.saveAndFlush(result);

        assertNotNull(result.getCreatedAt());
        assertNotNull(result.getUpdatedAt());
    }
}
