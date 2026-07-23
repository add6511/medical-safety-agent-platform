package com.medicalsafety.platform.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medicalsafety.platform.dto.CreateMedicalRecordRequest;
import com.medicalsafety.platform.dto.CreatePreConsultationRequest;
import com.medicalsafety.platform.dto.CreateTriageResultRequest;
import com.medicalsafety.platform.entity.MedicalRecord;
import com.medicalsafety.platform.entity.PreConsultation;
import com.medicalsafety.platform.entity.Role;
import com.medicalsafety.platform.entity.User;
import com.medicalsafety.platform.entity.UserRole;
import com.medicalsafety.platform.enums.MedicalRecordStatus;
import com.medicalsafety.platform.enums.PreConsultationStatus;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.enums.UserStatus;
import com.medicalsafety.platform.repository.*;
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
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class AuthorizationIntegrationTest {

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @Autowired private UserRepository userRepository;
    @Autowired private RoleRepository roleRepository;
    @Autowired private UserRoleRepository userRoleRepository;
    @Autowired private MedicalRecordRepository medicalRecordRepository;
    @Autowired private PreConsultationRepository preConsultationRepository;
    @Autowired private AuditLogRepository auditLogRepository;
    @Autowired private PasswordEncoder passwordEncoder;
    @Autowired private JwtTokenProvider jwtTokenProvider;

    private Role patientRole;
    private Role medicalStaffRole;
    private Role adminRole;
    private String patientToken;
    private String medicalToken;
    private String adminToken;
    private Long patientId;
    private Long medicalId;
    private Long adminId;

    @BeforeEach
    void setUp() {
        patientRole = roleRepository.findByName(RoleType.PATIENT)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.PATIENT).description("患者").build()));
        medicalStaffRole = roleRepository.findByName(RoleType.MEDICAL_STAFF)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.MEDICAL_STAFF).description("医务人员").build()));
        adminRole = roleRepository.findByName(RoleType.ADMIN)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.ADMIN).description("管理员").build()));

        User patient = createUser("auth_patient", "pass123", patientRole);
        User medical = createUser("auth_medical", "pass123", medicalStaffRole);
        User admin = createUser("auth_admin", "pass123", adminRole);

        patientId = patient.getId();
        medicalId = medical.getId();
        adminId = admin.getId();

        patientToken = jwtTokenProvider.generateToken(patientId, "auth_patient", List.of("PATIENT"));
        medicalToken = jwtTokenProvider.generateToken(medicalId, "auth_medical", List.of("MEDICAL_STAFF"));
        adminToken = jwtTokenProvider.generateToken(adminId, "auth_admin", List.of("ADMIN"));
    }

    private User createUser(String username, String password, Role role) {
        User user = userRepository.save(User.builder()
                .username(username).passwordHash(passwordEncoder.encode(password))
                .displayName(username).status(UserStatus.ENABLED).build());
        userRoleRepository.save(UserRole.builder().user(user).role(role).build());
        return user;
    }

    @Test
    void unauthenticatedAccessReturns401() throws Exception {
        mockMvc.perform(get("/api/v1/medical-records/1"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void patientCanCreateOwnRecord() throws Exception {
        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder()
                .patientId(patientId).caseCode("AUTH-CASE-001").chiefComplaint("头痛").build();

        mockMvc.perform(post("/api/v1/medical-records")
                        .header("Authorization", "Bearer " + patientToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.caseCode").value("AUTH-CASE-001"));
    }

    @Test
    void patientCannotCreateRecordForOtherPatient() throws Exception {
        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder()
                .patientId(adminId).caseCode("AUTH-CASE-002").build();

        mockMvc.perform(post("/api/v1/medical-records")
                        .header("Authorization", "Bearer " + patientToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isForbidden());
    }

    @Test
    void patientCanReadOwnRecord() throws Exception {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(patientId).caseCode("AUTH-READ-001").status(MedicalRecordStatus.ACTIVE).createdBy(patientId).build());

        mockMvc.perform(get("/api/v1/medical-records/" + record.getId())
                        .header("Authorization", "Bearer " + patientToken))
                .andExpect(status().isOk());
    }

    @Test
    void patientCannotReadOtherPatientRecord() throws Exception {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(adminId).caseCode("AUTH-READ-002").status(MedicalRecordStatus.ACTIVE).createdBy(adminId).build());

        mockMvc.perform(get("/api/v1/medical-records/" + record.getId())
                        .header("Authorization", "Bearer " + patientToken))
                .andExpect(status().isForbidden());
    }

    @Test
    void patientCannotArchiveOtherPatientRecord() throws Exception {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(adminId).caseCode("AUTH-ARCH-001").status(MedicalRecordStatus.ACTIVE).createdBy(adminId).build());

        mockMvc.perform(put("/api/v1/medical-records/" + record.getId() + "/archive")
                        .header("Authorization", "Bearer " + patientToken))
                .andExpect(status().isForbidden());
    }

    @Test
    void patientCannotCreateTriageResult() throws Exception {
        CreateTriageResultRequest request = CreateTriageResultRequest.builder()
                .preConsultationId(1L).urgencyLevel("URGENT").build();

        mockMvc.perform(post("/api/v1/triage-results")
                        .header("Authorization", "Bearer " + patientToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isForbidden());
    }

    @Test
    void patientCannotCreateAgentExecutionLog() throws Exception {
        String body = objectMapper.writeValueAsString(
                java.util.Map.of("preConsultationId", 1, "agentType", "SAFETY_CHECK"));

        mockMvc.perform(post("/api/v1/triage-results/agent-logs")
                        .header("Authorization", "Bearer " + patientToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isForbidden());
    }

    @Test
    void patientCannotReviewPreConsultation() throws Exception {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(patientId).caseCode("AUTH-REV-001").status(MedicalRecordStatus.ACTIVE).createdBy(patientId).build());
        PreConsultation pc = preConsultationRepository.save(PreConsultation.builder()
                .recordId(record.getId()).patientId(patientId).initiatedBy(patientId).status(PreConsultationStatus.AI_TRIAGE_COMPLETED).build());

        String body = objectMapper.writeValueAsString(
                java.util.Map.of("reviewComment", "审核", "approved", true));

        mockMvc.perform(post("/api/v1/pre-consultations/" + pc.getId() + "/review")
                        .header("Authorization", "Bearer " + patientToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isForbidden());
    }

    @Test
    void medicalStaffCanReviewPreConsultation() throws Exception {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(patientId).caseCode("AUTH-REV-002").status(MedicalRecordStatus.ACTIVE).createdBy(patientId).build());
        PreConsultation pc = preConsultationRepository.save(PreConsultation.builder()
                .recordId(record.getId()).patientId(patientId).initiatedBy(patientId).status(PreConsultationStatus.AI_TRIAGE_COMPLETED).build());

        String body = objectMapper.writeValueAsString(
                java.util.Map.of("reviewComment", "审核通过", "approved", true));

        mockMvc.perform(post("/api/v1/pre-consultations/" + pc.getId() + "/review")
                        .header("Authorization", "Bearer " + medicalToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("MEDICAL_REVIEW_COMPLETED"));
    }

    @Test
    void adminCanReadAnyRecord() throws Exception {
        MedicalRecord record = medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(patientId).caseCode("AUTH-ADMIN-001").status(MedicalRecordStatus.ACTIVE).createdBy(patientId).build());

        mockMvc.perform(get("/api/v1/medical-records/" + record.getId())
                        .header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk());
    }

    @Test
    void auditLogWrittenAfterBusinessOperation() throws Exception {
        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder()
                .patientId(patientId).caseCode("AUDIT-CASE-001").chiefComplaint("测试").build();

        mockMvc.perform(post("/api/v1/medical-records")
                        .header("Authorization", "Bearer " + patientToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated());

        List<?> logs = auditLogRepository.findByAction("CREATE");
        assertFalse(logs.isEmpty());
    }
}