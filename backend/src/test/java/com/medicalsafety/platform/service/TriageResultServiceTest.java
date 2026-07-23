package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.AgentExecutionLog;
import com.medicalsafety.platform.entity.TriageResult;
import com.medicalsafety.platform.enums.AgentExecutionStatus;
import com.medicalsafety.platform.enums.UrgencyLevel;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.AgentExecutionLogRepository;
import com.medicalsafety.platform.repository.PreConsultationRepository;
import com.medicalsafety.platform.repository.TriageResultRepository;
import org.junit.jupiter.api.BeforeEach;
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

    @Mock
    private TriageResultRepository triageResultRepository;

    @Mock
    private PreConsultationRepository preConsultationRepository;

    @Mock
    private AgentExecutionLogRepository agentExecutionLogRepository;

    @Mock
    private AuditLogService auditLogService;

    @InjectMocks
    private TriageResultService triageResultService;

    private TriageResult testResult;

    @BeforeEach
    void setUp() {
        triageResultService.setAuditLogService(auditLogService);

        testResult = TriageResult.builder()
                .id(1L)
                .preConsultationId(1L)
                .urgencyLevel(UrgencyLevel.URGENT)
                .suggestedDepartment("内科")
                .riskFlags("[\"高血压风险\"]")
                .reasoningSummary("患者有持续头痛和高血压病史")
                .referenceSources("[{\"source\":\"临床指南\",\"version\":\"2024\"}]")
                .build();
    }

    @Test
    void createTriageResultSuccess() {
        when(preConsultationRepository.existsById(1L)).thenReturn(true);
        when(triageResultRepository.save(any(TriageResult.class))).thenReturn(testResult);

        CreateTriageResultRequest request = CreateTriageResultRequest.builder()
                .preConsultationId(1L)
                .urgencyLevel("URGENT")
                .suggestedDepartment("内科")
                .riskFlags("[\"高血压风险\"]")
                .reasoningSummary("患者有持续头痛和高血压病史")
                .referenceSources("[{\"source\":\"临床指南\"}]")
                .build();

        TriageResultResponse response = triageResultService.createTriageResult(request, 1L);

        assertNotNull(response);
        assertEquals("URGENT", response.getUrgencyLevel());
        assertEquals("内科", response.getSuggestedDepartment());
        assertNotNull(response.getRiskFlags());
        assertNotNull(response.getReferenceSources());
    }

    @Test
    void createTriageResultPreConsultationNotFound() {
        when(preConsultationRepository.existsById(999L)).thenReturn(false);

        CreateTriageResultRequest request = CreateTriageResultRequest.builder()
                .preConsultationId(999L)
                .urgencyLevel("URGENT")
                .build();

        assertThrows(ResourceNotFoundException.class, () -> triageResultService.createTriageResult(request, 1L));
    }

    @Test
    void createTriageResultInvalidUrgencyLevel() {
        when(preConsultationRepository.existsById(1L)).thenReturn(true);

        CreateTriageResultRequest request = CreateTriageResultRequest.builder()
                .preConsultationId(1L)
                .urgencyLevel("INVALID")
                .build();

        assertThrows(BusinessException.class, () -> triageResultService.createTriageResult(request, 1L));
    }

    @Test
    void getTriageResultByPreConsultation() {
        when(triageResultRepository.findByPreConsultationId(1L)).thenReturn(Optional.of(testResult));

        TriageResultResponse response = triageResultService.getTriageResultByPreConsultation(1L);

        assertNotNull(response);
        assertEquals(1L, response.getPreConsultationId());
    }

    @Test
    void getTriageResultNotFound() {
        when(triageResultRepository.findByPreConsultationId(999L)).thenReturn(Optional.empty());

        assertThrows(ResourceNotFoundException.class, () -> triageResultService.getTriageResultByPreConsultation(999L));
    }

    @Test
    void createAgentExecutionLogSuccess() {
        when(preConsultationRepository.existsById(1L)).thenReturn(true);

        AgentExecutionLog logEntry = AgentExecutionLog.builder()
                .id(1L)
                .preConsultationId(1L)
                .agentType("SAFETY_CHECK")
                .inputSummary("症状输入")
                .outputSummary("安全检查完成")
                .status(AgentExecutionStatus.COMPLETED)
                .durationMs(1500L)
                .build();
        when(agentExecutionLogRepository.save(any(AgentExecutionLog.class))).thenReturn(logEntry);

        CreateAgentExecutionLogRequest request = CreateAgentExecutionLogRequest.builder()
                .preConsultationId(1L)
                .agentType("SAFETY_CHECK")
                .inputSummary("症状输入")
                .outputSummary("安全检查完成")
                .status("COMPLETED")
                .durationMs(1500L)
                .build();

        AgentExecutionLogResponse response = triageResultService.createAgentExecutionLog(request, 1L);

        assertNotNull(response);
        assertEquals("SAFETY_CHECK", response.getAgentType());
        assertEquals("COMPLETED", response.getStatus());
        assertEquals(1500L, response.getDurationMs());
    }

    @Test
    void createAgentExecutionLogInvalidStatus() {
        when(preConsultationRepository.existsById(1L)).thenReturn(true);

        CreateAgentExecutionLogRequest request = CreateAgentExecutionLogRequest.builder()
                .preConsultationId(1L)
                .agentType("SAFETY_CHECK")
                .status("INVALID")
                .build();

        assertThrows(BusinessException.class, () -> triageResultService.createAgentExecutionLog(request, 1L));
    }

    @Test
    void getAgentExecutionLogs() {
        AgentExecutionLog l1 = AgentExecutionLog.builder().id(1L).preConsultationId(1L).agentType("SAFETY_CHECK").status(AgentExecutionStatus.COMPLETED).build();
        AgentExecutionLog l2 = AgentExecutionLog.builder().id(2L).preConsultationId(1L).agentType("TRIAGE").status(AgentExecutionStatus.COMPLETED).build();
        when(agentExecutionLogRepository.findByPreConsultationId(1L)).thenReturn(List.of(l1, l2));

        List<AgentExecutionLogResponse> logs = triageResultService.getAgentExecutionLogs(1L);

        assertEquals(2, logs.size());
    }
}