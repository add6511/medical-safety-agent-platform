package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.AgentExecutionLog;
import com.medicalsafety.platform.entity.TriageResult;
import com.medicalsafety.platform.enums.AgentExecutionStatus;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.enums.UrgencyLevel;
import com.medicalsafety.platform.exception.AccessDeniedException;
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
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
public class TriageResultService {

    private static final Set<String> STAFF_ROLES = Set.of(
            RoleType.MEDICAL_STAFF.name(),
            RoleType.ADMIN.name()
    );

    private final TriageResultRepository triageResultRepository;
    private final PreConsultationRepository preConsultationRepository;
    private final AgentExecutionLogRepository agentExecutionLogRepository;
    private final AuditLogService auditLogService;

    @Transactional
    public TriageResultResponse createTriageResult(CreateTriageResultRequest request, Long operatorId, List<String> roles) {
        if (!isStaff(roles)) {
            throw new AccessDeniedException("只有医务人员可以创建分诊结果");
        }

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
        auditLogService.log(operatorId, null, "CREATE", "TRIAGE_RESULT", result.getId(), "创建分诊结果", null, null);
        return toResponse(result);
    }

    @Transactional(readOnly = true)
    public TriageResultResponse getTriageResultByPreConsultation(Long preConsultationId, Long operatorId, List<String> roles) {
        TriageResult result = triageResultRepository.findByPreConsultationId(preConsultationId)
                .orElseThrow(() -> new ResourceNotFoundException("分诊结果不存在"));
        if (!isStaff(roles)) {
            var pc = preConsultationRepository.findById(preConsultationId).orElseThrow();
            if (!pc.getPatientId().equals(operatorId)) {
                throw new AccessDeniedException("无权访问该分诊结果");
            }
        }
        return toResponse(result);
    }

    @Transactional
    public AgentExecutionLogResponse createAgentExecutionLog(CreateAgentExecutionLogRequest request, Long operatorId, List<String> roles) {
        if (!isStaff(roles)) {
            throw new AccessDeniedException("只有医务人员可以创建Agent执行记录");
        }

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
        auditLogService.log(operatorId, null, "CREATE", "AGENT_EXECUTION_LOG", logEntry.getId(),
                "Agent执行记录: " + logEntry.getAgentType(), null, null);
        return toLogResponse(logEntry);
    }

    @Transactional(readOnly = true)
    public List<AgentExecutionLogResponse> getAgentExecutionLogs(Long preConsultationId, Long operatorId, List<String> roles) {
        if (!isStaff(roles)) {
            var pc = preConsultationRepository.findById(preConsultationId).orElseThrow();
            if (!pc.getPatientId().equals(operatorId)) {
                throw new AccessDeniedException("无权访问该Agent执行记录");
            }
        }
        return agentExecutionLogRepository.findByPreConsultationId(preConsultationId).stream()
                .map(this::toLogResponse)
                .toList();
    }

    private boolean isStaff(List<String> roles) {
        return roles.stream().anyMatch(STAFF_ROLES::contains);
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
}
