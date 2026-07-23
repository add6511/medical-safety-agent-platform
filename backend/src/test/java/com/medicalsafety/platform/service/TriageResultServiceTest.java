package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.AgentExecutionLog;
import com.medicalsafety.platform.entity.TriageResult;
import com.medicalsafety.platform.enums.AgentExecutionStatus;
import com.medicalsafety.platform.enums.UrgencyLevel;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.repository.AgentExecutionLogRepository;
import com.medicalsafety.platform.repository.PreConsultationRepository;
import com.medicalsafety.platform.repository.TriageResultRepository;
import com.medicalsafety.platform.security.RequestContextHelper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TriageResultServiceTest {

    @Mock private TriageResultRepository triageResultRepository;
    @Mock private PreConsultationRepository preConsultationRepository;
    @Mock private AgentExecutionLogRepository agentExecutionLogRepository;
    @Mock private AuditLogService auditLogService;
    @Mock private RequestContextHelper requestContextHelper;
    @InjectMocks private TriageResultService triageResultService;

    private static final List<String> ADMIN_ROLES = List.of("ADMIN");
    private static final List<String> PATIENT_ROLES = List.of("PATIENT");

    @Test
    void patientCannotCreateAgentExecutionLog() {
        CreateAgentExecutionLogRequest request = CreateAgentExecutionLogRequest.builder().preConsultationId(1L).agentType("SAFETY_CHECK").build();
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> triageResultService.createAgentExecutionLog(request, 100L, PATIENT_ROLES));
    }

    @Test
    void createAgentExecutionLogAlwaysRunning() {
        when(preConsultationRepository.existsById(1L)).thenReturn(true);
        AgentExecutionLog logEntry = AgentExecutionLog.builder().id(1L).preConsultationId(1L).agentType("SAFETY_CHECK").status(AgentExecutionStatus.RUNNING).build();
        when(agentExecutionLogRepository.save(any(AgentExecutionLog.class))).thenReturn(logEntry);
        CreateAgentExecutionLogRequest request = CreateAgentExecutionLogRequest.builder().preConsultationId(1L).agentType("SAFETY_CHECK").status("COMPLETED").build();
        AgentExecutionLogResponse response = triageResultService.createAgentExecutionLog(request, 1L, ADMIN_ROLES);
        assertEquals("RUNNING", response.getStatus());
    }

    @Test
    void getTriageResultByPreConsultation() {
        TriageResult result = TriageResult.builder().id(1L).preConsultationId(1L).urgencyLevel(UrgencyLevel.URGENT).build();
        when(triageResultRepository.findByPreConsultationId(1L)).thenReturn(Optional.of(result));
        assertNotNull(triageResultService.getTriageResultByPreConsultation(1L, 1L, ADMIN_ROLES));
    }

    @Test
    void getAgentExecutionLogsByStaff() {
        AgentExecutionLog l1 = AgentExecutionLog.builder().id(1L).preConsultationId(1L).agentType("SAFETY_CHECK").status(AgentExecutionStatus.COMPLETED).build();
        when(agentExecutionLogRepository.findByPreConsultationId(1L)).thenReturn(List.of(l1));
        assertEquals(1, triageResultService.getAgentExecutionLogs(1L, 1L, ADMIN_ROLES).size());
    }

    @Test
    void patientCannotViewAgentExecutionLogs() {
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> triageResultService.getAgentExecutionLogs(1L, 100L, PATIENT_ROLES));
    }

    @Test
    void updateAgentExecutionLogInvalidDuration() {
        AgentExecutionLog logEntry = AgentExecutionLog.builder().id(1L).preConsultationId(1L).agentType("SAFETY_CHECK").status(AgentExecutionStatus.RUNNING).build();
        when(agentExecutionLogRepository.findById(1L)).thenReturn(Optional.of(logEntry));
        UpdateAgentExecutionLogRequest request = UpdateAgentExecutionLogRequest.builder().agentLogId(1L).status("COMPLETED").durationMs(-100L).build();
        assertThrows(BusinessException.class, () -> triageResultService.updateAgentExecutionLog(request, 1L, ADMIN_ROLES));
    }

    @Test
    void updateAgentExecutionLogZeroDuration() {
        AgentExecutionLog logEntry = AgentExecutionLog.builder().id(1L).preConsultationId(1L).agentType("SAFETY_CHECK").status(AgentExecutionStatus.RUNNING).build();
        when(agentExecutionLogRepository.findById(1L)).thenReturn(Optional.of(logEntry));
        UpdateAgentExecutionLogRequest request = UpdateAgentExecutionLogRequest.builder().agentLogId(1L).status("COMPLETED").durationMs(0L).build();
        assertThrows(BusinessException.class, () -> triageResultService.updateAgentExecutionLog(request, 1L, ADMIN_ROLES));
    }
}
