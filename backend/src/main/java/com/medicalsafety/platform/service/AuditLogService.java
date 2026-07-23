package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.AuditLogResponse;
import com.medicalsafety.platform.entity.AuditLog;
import com.medicalsafety.platform.repository.AuditLogRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuditLogService {

    private final AuditLogRepository auditLogRepository;

    public void log(Long userId, String username, String action, String resourceType,
                    Long resourceId, String detail, String ipAddress, String traceId) {
        AuditLog auditLog = AuditLog.builder()
                .userId(userId)
                .username(username)
                .action(action)
                .resourceType(resourceType)
                .resourceId(resourceId)
                .detail(detail)
                .ipAddress(ipAddress)
                .traceId(traceId)
                .build();

        auditLogRepository.save(auditLog);
        log.info("AUDIT_LOG | user={} | action={} | resource={}/{} | detail={}",
                username, action, resourceType, resourceId, detail);
    }

    public List<AuditLogResponse> getLogsByUser(Long userId) {
        return auditLogRepository.findByUserId(userId).stream()
                .map(this::toResponse)
                .toList();
    }

    public List<AuditLogResponse> getLogsByResourceType(String resourceType) {
        return auditLogRepository.findByResourceType(resourceType).stream()
                .map(this::toResponse)
                .toList();
    }

    public List<AuditLogResponse> getLogsByAction(String action) {
        return auditLogRepository.findByAction(action).stream()
                .map(this::toResponse)
                .toList();
    }

    private AuditLogResponse toResponse(AuditLog auditLog) {
        return AuditLogResponse.builder()
                .id(auditLog.getId())
                .userId(auditLog.getUserId())
                .username(auditLog.getUsername())
                .action(auditLog.getAction())
                .resourceType(auditLog.getResourceType())
                .resourceId(auditLog.getResourceId())
                .detail(auditLog.getDetail())
                .ipAddress(auditLog.getIpAddress())
                .traceId(auditLog.getTraceId())
                .createdAt(auditLog.getCreatedAt())
                .build();
    }
}