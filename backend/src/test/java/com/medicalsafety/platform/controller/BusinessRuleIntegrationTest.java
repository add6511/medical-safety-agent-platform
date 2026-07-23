package com.medicalsafety.platform.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.*;
import com.medicalsafety.platform.enums.*;
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
class BusinessRuleIntegrationTest {

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @Autowired private UserRepository userRepository;
    @Autowired private RoleRepository roleRepository;
    @Autowired private UserRoleRepository userRoleRepository;
    @Autowired private MedicalRecordRepository medicalRecordRepository;
    @Autowired private PreConsultationRepository preConsultationRepository;
    @Autowired private TriageResultRepository triageResultRepository;
    @Autowired private AgentExecutionLogRepository agentExecutionLogRepository;
    @Autowired private FollowupTaskRepository followupTaskRepository;
    @Autowired private AuditLogRepository auditLogRepository;
    @Autowired private PasswordEncoder passwordEncoder;
    @Autowired private JwtTokenProvider jwtTokenProvider;

    private Role patientRole;
    private Role medicalStaffRole;
    private Role followupStaffRole;
    private Role aiServiceRole;
    private Role adminRole;
    private Long patientId;
    private Long medicalId;
    private Long followupId;
    private Long aiServiceId;
    private Long adminId;
    private String patientToken;
    private String medicalToken;
    private String followupToken;
    private String aiServiceToken;
    private String adminToken;

    @BeforeEach
    void setUp() {
        patientRole = roleRepository.findByName(RoleType.PATIENT)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.PATIENT).description("患者").build()));
        medicalStaffRole = roleRepository.findByName(RoleType.MEDICAL_STAFF)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.MEDICAL_STAFF).description("医务人员").build()));
        followupStaffRole = roleRepository.findByName(RoleType.FOLLOWUP_STAFF)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.FOLLOWUP_STAFF).description("随访人员").build()));
        aiServiceRole = roleRepository.findByName(RoleType.AI_SERVICE)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.AI_SERVICE).description("AI服务").build()));
        adminRole = roleRepository.findByName(RoleType.ADMIN)
                .orElseGet(() -> roleRepository.save(Role.builder().name(RoleType.ADMIN).description("管理员").build()));

        User patient = createUser("biz_patient", "pass123", patientRole);
        User medical = createUser("biz_medical", "pass123", medicalStaffRole);
        User followup = createUser("biz_followup", "pass123", followupStaffRole);
        User aiService = createUser("biz_ai", "pass123", aiServiceRole);
        User admin = createUser("biz_admin", "pass123", adminRole);

        patientId = patient.getId();
        medicalId = medical.getId();
        followupId = followup.getId();
        aiServiceId = aiService.getId();
        adminId = admin.getId();

        patientToken = jwtTokenProvider.generateToken(patientId, "biz_patient", List.of("PATIENT"));
        medicalToken = jwtTokenProvider.generateToken(medicalId, "biz_medical", List.of("MEDICAL_STAFF"));
        followupToken = jwtTokenProvider.generateToken(followupId, "biz_followup", List.of("FOLLOWUP_STAFF"));
        aiServiceToken = jwtTokenProvider.generateToken(aiServiceId, "biz_ai", List.of("AI_SERVICE"));
        adminToken = jwtTokenProvider.generateToken(adminId, "biz_admin", List.of("ADMIN"));
    }

    private User createUser(String username, String password, Role role) {
        User user = userRepository.save(User.builder()
                .username(username).passwordHash(passwordEncoder.encode(password))
                .displayName(username).status(UserStatus.ENABLED).build());
        userRoleRepository.save(UserRole.builder().user(user).role(role).build());
        return user;
    }

    private MedicalRecord createRecord(Long patientId) {
        return medicalRecordRepository.save(MedicalRecord.builder()
                .patientId(patientId).caseCode("BIZ-" + System.nanoTime())
                .status(MedicalRecordStatus.ACTIVE).createdBy(patientId).build());
    }

    private PreConsultation createPreConsultation(Long recordId, Long patientId, PreConsultationStatus status) {
        return preConsultationRepository.save(PreConsultation.builder()
                .recordId(recordId).patientId(patientId).initiatedBy(patientId).status(status).build());
    }

    @Test
    void disabledUserOldJwtReturns401() throws Exception {
        User user = createUser("disabled_user", "pass123", patientRole);
        String token = jwtTokenProvider.generateToken(user.getId(), "disabled_user", List.of("PATIENT"));

        mockMvc.perform(get("/api/v1/medical-records/patient/" + user.getId())
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());

        user.setStatus(UserStatus.DISABLED);
        userRepository.save(user);

        mockMvc.perform(get("/api/v1/medical-records/patient/" + user.getId())
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void roleRevokedOldJwtLosesAccess() throws Exception {
        User user = createUser("role_revoke_user", "pass123", medicalStaffRole);
        String token = jwtTokenProvider.generateToken(user.getId(), "role_revoke_user", List.of("MEDICAL_STAFF"));

        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.AI_TRIAGE_COMPLETED);

        mockMvc.perform(post("/api/v1/pre-consultations/" + pc.getId() + "/review")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(
                                java.util.Map.of("reviewComment", "审核", "approved", true))))
                .andExpect(status().isOk());

        userRoleRepository.deleteAll();
        UserRole newRole = UserRole.builder().user(user).role(patientRole).build();
        userRoleRepository.save(newRole);

        PreConsultation pc2 = createPreConsultation(record.getId(), patientId, PreConsultationStatus.AI_TRIAGE_COMPLETED);

        mockMvc.perform(post("/api/v1/pre-consultations/" + pc2.getId() + "/review")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(
                                java.util.Map.of("reviewComment", "审核", "approved", true))))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonAiServiceCannotCallInternalSubmit() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.SYMPTOM_COLLECTED);

        SubmitTriageResultRequest request = SubmitTriageResultRequest.builder()
                .preConsultationId(pc.getId()).urgencyLevel("URGENT").suggestedDepartment("内科").build();

        mockMvc.perform(post("/api/v1/triage-results/internal/submit")
                        .header("Authorization", "Bearer " + medicalToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isForbidden());
    }

    @Test
    void aiServiceCanCallInternalSubmit() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.SYMPTOM_COLLECTED);

        SubmitTriageResultRequest request = SubmitTriageResultRequest.builder()
                .preConsultationId(pc.getId()).urgencyLevel("URGENT").suggestedDepartment("内科").build();

        mockMvc.perform(post("/api/v1/triage-results/internal/submit")
                        .header("Authorization", "Bearer " + aiServiceToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.urgencyLevel").value("URGENT"));
    }

    @Test
    void agentLogCreateSuccessRunning() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.SYMPTOM_COLLECTED);

        String body = objectMapper.writeValueAsString(
                java.util.Map.of("preConsultationId", pc.getId(), "agentType", "SAFETY_CHECK", "status", "RUNNING"));

        mockMvc.perform(post("/api/v1/triage-results/internal/agent-logs")
                        .header("Authorization", "Bearer " + aiServiceToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status").value("RUNNING"));
    }

    @Test
    void agentLogUpdateToCompleted() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.SYMPTOM_COLLECTED);

        AgentExecutionLog logEntry = AgentExecutionLog.builder()
                .preConsultationId(pc.getId()).agentType("SAFETY_CHECK").status(AgentExecutionStatus.RUNNING).build();
        logEntry = agentExecutionLogRepository.save(logEntry);

        UpdateAgentExecutionLogRequest request = UpdateAgentExecutionLogRequest.builder()
                .agentLogId(logEntry.getId()).status("COMPLETED").outputSummary("检查完成").durationMs(1500L).build();

        mockMvc.perform(put("/api/v1/triage-results/internal/agent-logs")
                        .header("Authorization", "Bearer " + aiServiceToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("COMPLETED"));
    }

    @Test
    void agentLogUpdateToFailed() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.SYMPTOM_COLLECTED);

        AgentExecutionLog logEntry = AgentExecutionLog.builder()
                .preConsultationId(pc.getId()).agentType("SAFETY_CHECK").status(AgentExecutionStatus.RUNNING).build();
        logEntry = agentExecutionLogRepository.save(logEntry);

        UpdateAgentExecutionLogRequest request = UpdateAgentExecutionLogRequest.builder()
                .agentLogId(logEntry.getId()).status("FAILED").errorMessage("超时").build();

        mockMvc.perform(put("/api/v1/triage-results/internal/agent-logs")
                        .header("Authorization", "Bearer " + aiServiceToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("FAILED"));
    }

    @Test
    void agentLogCannotUpdateFinishedLog() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.SYMPTOM_COLLECTED);

        AgentExecutionLog logEntry = AgentExecutionLog.builder()
                .preConsultationId(pc.getId()).agentType("SAFETY_CHECK").status(AgentExecutionStatus.COMPLETED).build();
        logEntry = agentExecutionLogRepository.save(logEntry);

        UpdateAgentExecutionLogRequest request = UpdateAgentExecutionLogRequest.builder()
                .agentLogId(logEntry.getId()).status("FAILED").build();

        mockMvc.perform(put("/api/v1/triage-results/internal/agent-logs")
                        .header("Authorization", "Bearer " + aiServiceToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void illegalStateCannotSubmitTriageResult() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.INITIATED);

        SubmitTriageResultRequest request = SubmitTriageResultRequest.builder()
                .preConsultationId(pc.getId()).urgencyLevel("URGENT").build();

        mockMvc.perform(post("/api/v1/triage-results/internal/submit")
                        .header("Authorization", "Bearer " + aiServiceToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void duplicateSubmitDoesNotCreateSecondTriageResult() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.SYMPTOM_COLLECTED);

        SubmitTriageResultRequest request = SubmitTriageResultRequest.builder()
                .preConsultationId(pc.getId()).urgencyLevel("URGENT").suggestedDepartment("内科").build();

        mockMvc.perform(post("/api/v1/triage-results/internal/submit")
                        .header("Authorization", "Bearer " + aiServiceToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated());

        pc.setStatus(PreConsultationStatus.NEEDS_REVISION);
        preConsultationRepository.save(pc);

        SubmitTriageResultRequest request2 = SubmitTriageResultRequest.builder()
                .preConsultationId(pc.getId()).urgencyLevel("ROUTINE").suggestedDepartment("外科").build();

        mockMvc.perform(post("/api/v1/triage-results/internal/submit")
                        .header("Authorization", "Bearer " + aiServiceToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request2)))
                .andExpect(status().isCreated());

        List<TriageResult> results = triageResultRepository.findByPreConsultationId(pc.getId())
                .map(List::of).orElse(List.of());
        assertEquals(1, results.size(), "重复提交不应产生第二条分诊结果");
        assertEquals(UrgencyLevel.ROUTINE, results.get(0).getUrgencyLevel());
    }

    @Test
    void reviewNotApprovedGoesToNeedsRevision() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.AI_TRIAGE_COMPLETED);

        mockMvc.perform(post("/api/v1/pre-consultations/" + pc.getId() + "/review")
                        .header("Authorization", "Bearer " + medicalToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(
                                java.util.Map.of("reviewComment", "需要修改", "approved", false))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("NEEDS_REVISION"));
    }

    @Test
    void followupStaffCanOnlyHandleOwnTasks() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.MEDICAL_REVIEW_COMPLETED);

        FollowupTask task = FollowupTask.builder()
                .preConsultationId(pc.getId()).assignedTo(followupId).assignedBy(medicalId)
                .taskType("PHONE_FOLLOWUP").status(FollowupTaskStatus.PENDING).build();
        task = followupTaskRepository.save(task);

        mockMvc.perform(get("/api/v1/followup-tasks/" + task.getId())
                        .header("Authorization", "Bearer " + followupToken))
                .andExpect(status().isOk());

        User otherFollowup = createUser("biz_other_followup", "pass123", followupStaffRole);
        String otherToken = jwtTokenProvider.generateToken(otherFollowup.getId(), "biz_other_followup", List.of("FOLLOWUP_STAFF"));

        mockMvc.perform(get("/api/v1/followup-tasks/" + task.getId())
                        .header("Authorization", "Bearer " + otherToken))
                .andExpect(status().isForbidden());
    }

    @Test
    void followupStaffCanUpdateOwnTask() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.MEDICAL_REVIEW_COMPLETED);

        FollowupTask task = FollowupTask.builder()
                .preConsultationId(pc.getId()).assignedTo(followupId).assignedBy(medicalId)
                .taskType("PHONE_FOLLOWUP").status(FollowupTaskStatus.PENDING).build();
        task = followupTaskRepository.save(task);

        UpdateFollowupTaskRequest request = UpdateFollowupTaskRequest.builder()
                .taskId(task.getId()).status("IN_PROGRESS").notes("开始随访").build();

        mockMvc.perform(put("/api/v1/followup-tasks")
                        .header("Authorization", "Bearer " + followupToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("IN_PROGRESS"));
    }

    @Test
    void concurrentModificationReturns409() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.INITIATED);

        mockMvc.perform(put("/api/v1/pre-consultations/" + pc.getId() + "/transition")
                        .header("Authorization", "Bearer " + adminToken)
                        .param("status", "SYMPTOM_COLLECTED"))
                .andExpect(status().isOk());
    }

    @Test
    void auditLogFieldsPopulated() throws Exception {
        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder()
                .patientId(patientId).caseCode("AUDIT-FIELD-" + System.nanoTime()).chiefComplaint("审计测试").build();

        mockMvc.perform(post("/api/v1/medical-records")
                        .header("Authorization", "Bearer " + patientToken)
                        .header("X-Trace-Id", "test-trace-123")
                        .header("X-Forwarded-For", "192.168.1.1")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated());

        List<AuditLog> logs = auditLogRepository.findByAction("CREATE");
        assertFalse(logs.isEmpty());
        AuditLog lastLog = logs.get(logs.size() - 1);
        assertNotNull(lastLog.getTraceId(), "traceId 不应为空");
        assertNotNull(lastLog.getIpAddress(), "ipAddress 不应为空");
        assertNotNull(lastLog.getUsername(), "username 不应为空");
    }

    @Test
    void aiServiceCanCreateAgentLogViaInternalEndpoint() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.SYMPTOM_COLLECTED);

        String body = objectMapper.writeValueAsString(
                java.util.Map.of("preConsultationId", pc.getId(), "agentType", "RISK_ASSESSMENT", "status", "RUNNING"));

        mockMvc.perform(post("/api/v1/triage-results/internal/agent-logs")
                        .header("Authorization", "Bearer " + aiServiceToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isCreated());
    }

    @Test
    void patientCannotAccessInternalAgentLogs() throws Exception {
        String body = objectMapper.writeValueAsString(
                java.util.Map.of("preConsultationId", 1, "agentType", "SAFETY_CHECK"));

        mockMvc.perform(post("/api/v1/triage-results/internal/agent-logs")
                        .header("Authorization", "Bearer " + patientToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isForbidden());
    }

    @Test
    void needsRevisionCanTransitionToAiTriageCompleted() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.NEEDS_REVISION);

        mockMvc.perform(put("/api/v1/pre-consultations/" + pc.getId() + "/transition")
                        .header("Authorization", "Bearer " + adminToken)
                        .param("status", "AI_TRIAGE_COMPLETED"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("AI_TRIAGE_COMPLETED"));
    }

    @Test
    void medicalStaffCanCreateFollowupTask() throws Exception {
        MedicalRecord record = createRecord(patientId);
        PreConsultation pc = createPreConsultation(record.getId(), patientId, PreConsultationStatus.MEDICAL_REVIEW_COMPLETED);

        CreateFollowupTaskRequest request = CreateFollowupTaskRequest.builder()
                .preConsultationId(pc.getId()).assignedTo(followupId).taskType("PHONE_FOLLOWUP").description("电话随访").build();

        mockMvc.perform(post("/api/v1/followup-tasks")
                        .header("Authorization", "Bearer " + medicalToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status").value("PENDING"))
                .andExpect(jsonPath("$.assignedTo").value(followupId));
    }

    @Test
    void patientCannotCreateFollowupTask() throws Exception {
        CreateFollowupTaskRequest request = CreateFollowupTaskRequest.builder()
                .preConsultationId(1L).assignedTo(followupId).taskType("PHONE_FOLLOWUP").build();

        mockMvc.perform(post("/api/v1/followup-tasks")
                        .header("Authorization", "Bearer " + patientToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isForbidden());
    }
}