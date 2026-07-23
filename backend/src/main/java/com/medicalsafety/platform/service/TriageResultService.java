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
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class TriageResultService {

    private final TriageResultRepository triageResultRepository;
    private final PreConsultationRepository preConsultationRepository;
    private final AgentExecutionLogRepository agentExecutionLogRepository;
    private AuditLogService auditLogService;

    public void setAuditLogService(AuditLogService auditLogService) {
        this.auditLogService = auditLogService;
    }

    @Transactional
    public TriageResultResponse createTriageResult(CreateTriageResultRequest request, Long operatorId) {
        if (!preConsultationRepository.existsById(request.getPreConsultationId())) {
            throw new ResourceNotFoundException("预问诊记录不存在");
        }

        UrgencyLevel urgencyLevel = parseUrgencyLevel(request.getUrgencyLevel());

        TriageResult result = TriageResult.builder()
                .preConsultationId(request.getPreConsultationId())
                .urgencyLevel(urgencyLevel)
                .suggestedDepartment(request.getSuggestedDepartment())
                .riskFlags(request.getRiskFlags())
                .reasoningSummary(request.getReasoningSummary())
                .referenceSources(request.getReferenceSources())
                .build();

        result = triageResultRepository.save(result);
        logAudit(operatorId, "CREATE", "TRIAGE_RESULT", result.getId(), "创建分诊结果");
        return toResponse(result);
    }

    @Transactional(readOnly = true)
    public TriageResultResponse getTriageResultByPreConsultation(Long preConsultationId) {
        TriageResult result = triageResultRepository.findByPreConsultationId(preConsultationId)
                .orElseThrow(() -> new ResourceNotFoundException("分诊结果不存在"));
        return toResponse(result);
    }

    @Transactional
    public AgentExecutionLogResponse createAgentExecutionLog(CreateAgentExecutionLogRequest request, Long operatorId) {
        if (!preConsultationRepository.existsById(request.getPreConsultationId())) {
            throw new ResourceNotFoundException("预问诊记录不存在");
        }

        AgentExecutionStatus status = parseAgentStatus(request.getStatus());

        AgentExecutionLog logEntry = AgentExecutionLog.builder()
                .preConsultationId(request.getPreConsultationId())
                .agentType(request.getAgentType())
                .inputSummary(request.getInputSummary())
                .outputSummary(request.getOutputSummary())
                .status(status)
                .errorMessage(request.getErrorMessage())
                .durationMs(request.getDurationMs())
                .build();

        if (status != AgentExecutionStatus.RUNNING) {
            logEntry.setCompletedAt(LocalDateTime.now());
        }

        logEntry = agentExecutionLogRepository.save(logEntry);
        logAudit(operatorId, "CREATE", "AGENT_EXECUTION_LOG", logEntry.getId(),
                "Agent执行记录: " + logEntry.getAgentType());
        return toLogResponse(logEntry);
    }

    @Transactional(readOnly = true)
    public List<AgentExecutionLogResponse> getAgentExecutionLogs(Long preConsultationId) {
        return agentExecutionLogRepository.findByPreConsultationId(preConsultationId).stream()
                .map(this::toLogResponse)
                .toList();
    }

    private UrgencyLevel parseUrgencyLevel(String urgencyLevel) {
        if (urgencyLevel == null || urgencyLevel.isBlank()) {
            return UrgencyLevel.ROUTINE;
        }
        try {
            return UrgencyLevel.valueOf(urgencyLevel);
        } catch (IllegalArgumentException e) {
            throw new BusinessException("INVALID_URGENCY_LEVEL", "无效的紧急程度: " + urgencyLevel);
        }
    }

    private AgentExecutionStatus parseAgentStatus(String status) {
        if (status == null || status.isBlank()) {
            return AgentExecutionStatus.RUNNING;
        }
        try {
            return AgentExecutionStatus.valueOf(status);
        } catch (IllegalArgumentException e) {
            throw new BusinessException("INVALID_AGENT_STATUS", "无效的Agent执行状态: " + status);
        }
    }

    private TriageResultResponse toResponse(TriageResult result) {
        return TriageResultResponse.builder()
                .id(result.getId())
                .preConsultationId(result.getPreConsultationId())
                .urgencyLevel(result.getUrgencyLevel().name())
                .suggestedDepartment(result.getSuggestedDepartment())
                .riskFlags(result.getRiskFlags())
                .reasoningSummary(result.getReasoningSummary())
                .referenceSources(result.getReferenceSources())
                .createdAt(result.getCreatedAt())
                .build();
    }

    private AgentExecutionLogResponse toLogResponse(AgentExecutionLog logEntry) {
        return AgentExecutionLogResponse.builder()
                .id(logEntry.getId())
                .preConsultationId(logEntry.getPreConsultationId())
                .agentType(logEntry.getAgentType())
                .inputSummary(logEntry.getInputSummary())
                .outputSummary(logEntry.getOutputSummary())
                .status(logEntry.getStatus().name())
                .errorMessage(logEntry.getErrorMessage())
                .startedAt(logEntry.getStartedAt())
                .completedAt(logEntry.getCompletedAt())
                .durationMs(logEntry.getDurationMs())
                .build();
    }

    private void logAudit(Long userId, String action, String resourceType, Long resourceId, String detail) {
        if (auditLogService != null) {
            auditLogService.log(userId, null, action, resourceType, resourceId, detail, null, null);
        }
    }
}