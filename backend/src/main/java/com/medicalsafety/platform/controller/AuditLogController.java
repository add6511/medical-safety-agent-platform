package com.medicalsafety.platform.controller;

import com.medicalsafety.platform.dto.AuditLogResponse;
import com.medicalsafety.platform.service.AuditLogService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/audit-logs")
@RequiredArgsConstructor
@Tag(name = "审计日志", description = "操作审计日志查询接口")
public class AuditLogController {

    private final AuditLogService auditLogService;

    @GetMapping("/user/{userId}")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "按用户查询审计日志", description = "管理员查询指定用户的操作日志")
    public ResponseEntity<List<AuditLogResponse>> getByUser(@PathVariable Long userId) {
        return ResponseEntity.ok(auditLogService.getLogsByUser(userId));
    }

    @GetMapping("/resource/{resourceType}")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "按资源类型查询", description = "管理员查询指定资源类型的操作日志")
    public ResponseEntity<List<AuditLogResponse>> getByResourceType(@PathVariable String resourceType) {
        return ResponseEntity.ok(auditLogService.getLogsByResourceType(resourceType));
    }

    @GetMapping("/action/{action}")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "按操作类型查询", description = "管理员查询指定操作类型的日志")
    public ResponseEntity<List<AuditLogResponse>> getByAction(@PathVariable String action) {
        return ResponseEntity.ok(auditLogService.getLogsByAction(action));
    }
}