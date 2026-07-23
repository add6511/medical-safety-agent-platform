package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.AuditLogResponse;
import com.medicalsafety.platform.entity.AuditLog;
import com.medicalsafety.platform.repository.AuditLogRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuditLogServiceTest {

    @Mock
    private AuditLogRepository auditLogRepository;

    @InjectMocks
    private AuditLogService auditLogService;

    @Test
    void logSuccess() {
        when(auditLogRepository.save(any(AuditLog.class))).thenAnswer(inv -> inv.getArgument(0));

        auditLogService.log(1L, "testuser", "CREATE", "MEDICAL_RECORD", 1L, "创建记录", "127.0.0.1", "trace-123");

        verify(auditLogRepository).save(any(AuditLog.class));
    }

    @Test
    void getLogsByUser() {
        AuditLog log1 = AuditLog.builder().id(1L).userId(1L).username("testuser").action("CREATE").resourceType("MEDICAL_RECORD").build();
        when(auditLogRepository.findByUserId(1L)).thenReturn(List.of(log1));

        List<AuditLogResponse> logs = auditLogService.getLogsByUser(1L);

        assertEquals(1, logs.size());
        assertEquals("CREATE", logs.get(0).getAction());
    }

    @Test
    void getLogsByResourceType() {
        AuditLog log1 = AuditLog.builder().id(1L).userId(1L).action("CREATE").resourceType("MEDICAL_RECORD").build();
        when(auditLogRepository.findByResourceType("MEDICAL_RECORD")).thenReturn(List.of(log1));

        List<AuditLogResponse> logs = auditLogService.getLogsByResourceType("MEDICAL_RECORD");

        assertEquals(1, logs.size());
        assertEquals("MEDICAL_RECORD", logs.get(0).getResourceType());
    }

    @Test
    void getLogsByAction() {
        AuditLog log1 = AuditLog.builder().id(1L).userId(1L).action("REVIEW").resourceType("PRE_CONSULTATION").build();
        when(auditLogRepository.findByAction("REVIEW")).thenReturn(List.of(log1));

        List<AuditLogResponse> logs = auditLogService.getLogsByAction("REVIEW");

        assertEquals(1, logs.size());
        assertEquals("REVIEW", logs.get(0).getAction());
    }
}