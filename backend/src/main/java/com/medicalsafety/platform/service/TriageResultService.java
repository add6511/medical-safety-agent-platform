package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.AgentExecutionLog;
import com.medicalsafety.platform.entity.PreConsultation;
import com.medicalsafety.platform.entity.TriageResult;
import com.medicalsafety.platform.enums.AgentExecutionStatus;
import com.medicalsafety.platform.enums.PreConsultationStatus;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.enums.UrgencyLevel;
import com.medicalsafety.platform.exception.AccessDeniedException;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.AgentExecutionLogRepository;
import com.medicalsafety.platform.repository.PreConsultationRepository;
import com.medicalsafety.platform.repository.TriageResultRepository;
import com.medicalsafety.platform.security.RequestContextHelper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
public class TriageResultService {

    private static final Set<String> AI_OR_ADMIN_ROLES = Set.of(
            RoleType.AI_SERVICE.name(),
            RoleType.ADMIN.name()
    );
    private static final Set<String> STAFF_ROLES = Set.of(
            RoleType.MEDICAL_STAFF.name(),
            RoleType.ADMIN.name()
    );

    private final TriageResultRepository triageResultRepository;
    private final PreConsultationRepository preConsultationRepository;
    private final AgentExecutionLogRepository agentExecutionLogRepository;
    private final AuditLogService auditLogService;
    private final RequestContextHelper requestContextHelper;

    @Transactional
    public TriageResultResponse submitTriageResult(SubmitTriageResultRequest request, Long operatorId, List<String> roles) {
        if (!roles.stream().anyMatch(AI_OR_ADMIN_ROLES::contains)) {
            throw new AccessDeniedException("只有AI服务或管理员可以提交分诊结果");
        }

        PreConsultation pc = preConsultationRepository.findById(request.getPreConsultationId())
                .orElseThrow(() -> new ResourceNotFoundException("预问诊记录不存在"));

        if (pc.getStatus() != PreConsultationStatus.SYMPTOM_COLLECTED
                && pc.getStatus() != PreConsultationStatus.NEEDS_REVISION) {
            throw new BusinessException("INVALID_TRIAGE_STATE",
                    "只能在症状收集或需修改状态下提交分诊结果，当前状态: " + pc.getStatus());
        }

        UrgencyLevel urgencyLevel = parseUrgencyLevel(request.getUrgencyLevel());

        Optional<TriageResult> existing = triageResultRepository.findByPreConsultationId(request.getPreConsultationId());
        TriageResult result;
        if (existing.isPresent()) {
            result = existing.get();
            result.setUrgencyLevel(urgencyLevel);
            result.setSuggestedDepartment(request.getSuggestedDepartment());
            result.setRiskFlags(request.getRiskFlags());
            result.setReasoningSummary(request.getReasoningSummary());
            result.setReferenceSources(request.getReferenceSources());
        } else {
            result = TriageResult.builder()
                    .preConsultationId(request.getPreConsultationId())
                    .urgencyLevel(urgencyLevel)
                    .suggestedDepartment(request.getSuggestedDepartment())
                    .riskFlags(request.getRiskFlags())
                    .reasoningSummary(request.getReasoningSummary())
                    .referenceSources(request.getReferenceSources())
                    .build();
        }
        result = triageResultRepository.save(result);

        pc.setStatus(PreConsultationStatus.AI_TRIAGE_COMPLETED);
        preConsultationRepository.save(pc);

        auditLogService.log(operatorId, requestContextHelper.getCurrentUsername(), "SUBMIT_TRIAGE", "TRIAGE_RESULT", result.getId(), "提交分诊结果", requestContextHelper.getClientIp(), requestContextHelper.getTraceId());
        return toResponse(result);
    }


    @Transactional(readOnly = true)
    public TriageResultResponse getTriageResultByPreConsultation(Long preConsultationId, Long operatorId, List<String> roles) {
        TriageResult result = triageResultRepository.findByPreConsultationId(preConsultationId)
                .orElseThrow(() -> new ResourceNotFoundException("分诊结果不存在"));
        if (!roles.stream().anyMatch(STAFF_ROLES::contains)) {
            var pc = preConsultationRepository.findById(preConsultationId).orElseThrow();
            if (!pc.getPatientId().equals(operatorId)) {
                throw new AccessDeniedException("无权访问该分诊结果");
            }
        }
        return toResponse(result);
    }

    @Transactional
    public AgentExecutionLogResponse createAgentExecutionLog(CreateAgentExecutionLogRequest request, Long operatorId, List<String> roles) {
        if (!roles.stream().anyMatch(AI_OR_ADMIN_ROLES::contains)) {
            throw new AccessDeniedException("只有AI服务或管理员可以创建Agent执行记录");
        }
        if (!preConsultationRepository.existsById(request.getPreConsultationId())) {
            throw new ResourceNotFoundException("预问诊记录不存在");
        }
        AgentExecutionLog logEntry = AgentExecutionLog.builder()
                .preConsultationId(request.getPreConsultationId())
                .agentType(request.getAgentType())
                .inputSummary(request.getInputSummary())
                .status(AgentExecutionStatus.RUNNING)
                .build();
        logEntry = agentExecutionLogRepository.save(logEntry);
        auditLogService.log(operatorId, requestContextHelper.getCurrentUsername(), "CREATE", "AGENT_EXECUTION_LOG", logEntry.getId(),
                "Agent执行记录: " + logEntry.getAgentType(), requestContextHelper.getClientIp(), requestContextHelper.getTraceId());
        return toLogResponse(logEntry);
    }

    @Transactional
    public AgentExecutionLogResponse updateAgentExecutionLog(UpdateAgentExecutionLogRequest request, Long operatorId, List<String> roles) {
        if (!roles.stream().anyMatch(AI_OR_ADMIN_ROLES::contains)) {
            throw new AccessDeniedException("只有AI服务或管理员可以更新Agent执行记录");
        }
        AgentExecutionLog logEntry = agentExecutionLogRepository.findById(request.getAgentLogId())
                .orElseThrow(() -> new ResourceNotFoundException("Agent执行记录不存在"));
        if (logEntry.isFinished()) {
            throw new BusinessException("AGENT_LOG_ALREADY_FINISHED", "已结束的Agent执行记录不能重复更新");
        }
        AgentExecutionStatus newStatus = parseAgentStatus(request.getStatus());
        if (newStatus == AgentExecutionStatus.RUNNING) {
            throw new BusinessException("INVALID_AGENT_STATUS", "不能将记录更新为RUNNING状态");
        }
        if (newStatus == AgentExecutionStatus.COMPLETED) {
            if (request.getOutputSummary() == null || request.getOutputSummary().isBlank()) {
                throw new BusinessException("MISSING_OUTPUT_SUMMARY", "COMPLETED 状态必须提供 outputSummary");
            }
        }
        if (newStatus == AgentExecutionStatus.FAILED) {
            if (request.getErrorMessage() == null || request.getErrorMessage().isBlank()) {
                throw new BusinessException("MISSING_ERROR_MESSAGE", "FAILED 状态必须提供 errorMessage");
            }
        }
        logEntry.setStatus(newStatus);
        logEntry.setCompletedAt(LocalDateTime.now());
        if (request.getOutputSummary() != null) {
            logEntry.setOutputSummary(request.getOutputSummary());
        }
        if (newStatus == AgentExecutionStatus.FAILED && request.getErrorMessage() != null) {
            logEntry.setErrorMessage(request.getErrorMessage());
        }
        if (request.getDurationMs() != null) {
            if (request.getDurationMs() <= 0) {
                throw new BusinessException("INVALID_DURATION", "执行耗时必须为正数");
            }
            logEntry.setDurationMs(request.getDurationMs());
        }
        logEntry = agentExecutionLogRepository.save(logEntry);
        auditLogService.log(operatorId, requestContextHelper.getCurrentUsername(), "UPDATE", "AGENT_EXECUTION_LOG", logEntry.getId(),
                "Agent执行记录更新: " + newStatus, requestContextHelper.getClientIp(), requestContextHelper.getTraceId());
        return toLogResponse(logEntry);
    }

    @Transactional(readOnly = true)
    public List<AgentExecutionLogResponse> getAgentExecutionLogs(Long preConsultationId, Long operatorId, List<String> roles) {
        if (!roles.stream().anyMatch(STAFF_ROLES::contains) && !roles.stream().anyMatch(AI_OR_ADMIN_ROLES::contains)) {
            throw new AccessDeniedException("只有医务人员、AI服务或管理员可以查看Agent执行记录");
        }
        return agentExecutionLogRepository.findByPreConsultationId(preConsultationId).stream()
                .map(this::toLogResponse).toList();
    }

    private UrgencyLevel parseUrgencyLevel(String urgencyLevel) {
        if (urgencyLevel == null || urgencyLevel.isBlank()) return UrgencyLevel.ROUTINE;
        try { return UrgencyLevel.valueOf(urgencyLevel); }
        catch (IllegalArgumentException e) { throw new BusinessException("INVALID_URGENCY_LEVEL", "无效的紧急程度: " + urgencyLevel); }
    }

    private AgentExecutionStatus parseAgentStatus(String status) {
        if (status == null || status.isBlank()) return AgentExecutionStatus.RUNNING;
        try { return AgentExecutionStatus.valueOf(status); }
        catch (IllegalArgumentException e) { throw new BusinessException("INVALID_AGENT_STATUS", "无效的Agent执行状态: " + status); }
    }

    private TriageResultResponse toResponse(TriageResult result) {
        return TriageResultResponse.builder()
                .id(result.getId()).preConsultationId(result.getPreConsultationId())
                .urgencyLevel(result.getUrgencyLevel().name())
                .suggestedDepartment(result.getSuggestedDepartment())
                .riskFlags(result.getRiskFlags()).reasoningSummary(result.getReasoningSummary())
                .referenceSources(result.getReferenceSources()).createdAt(result.getCreatedAt())
                .build();
    }

    private AgentExecutionLogResponse toLogResponse(AgentExecutionLog logEntry) {
        return AgentExecutionLogResponse.builder()
                .id(logEntry.getId()).preConsultationId(logEntry.getPreConsultationId())
                .agentType(logEntry.getAgentType()).inputSummary(logEntry.getInputSummary())
                .outputSummary(logEntry.getOutputSummary()).status(logEntry.getStatus().name())
                .errorMessage(logEntry.getErrorMessage()).startedAt(logEntry.getStartedAt())
                .completedAt(logEntry.getCompletedAt()).durationMs(logEntry.getDurationMs())
                .build();
    }
}
