package com.medicalsafety.platform.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuditLogResponse {

    private Long id;
    private Long userId;
    private String username;
    private String action;
    private String resourceType;
    private Long resourceId;
    private String detail;
    private String ipAddress;
    private String traceId;
    private LocalDateTime createdAt;
}