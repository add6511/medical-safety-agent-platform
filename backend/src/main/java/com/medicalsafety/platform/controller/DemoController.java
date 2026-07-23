package com.medicalsafety.platform.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/demo")
@Tag(name = "权限测试", description = "仅用于验证RBAC权限控制，后续可删除")
public class DemoController {

    @GetMapping("/patient")
    @PreAuthorize("hasRole('PATIENT')")
    @Operation(summary = "患者角色测试接口", description = "仅PATIENT角色可访问")
    public ResponseEntity<Map<String, String>> patient() {
        return ResponseEntity.ok(Map.of("message", "PATIENT角色访问成功", "role", "PATIENT"));
    }

    @GetMapping("/medical")
    @PreAuthorize("hasRole('MEDICAL_STAFF')")
    @Operation(summary = "医务人员角色测试接口", description = "仅MEDICAL_STAFF角色可访问")
    public ResponseEntity<Map<String, String>> medical() {
        return ResponseEntity.ok(Map.of("message", "MEDICAL_STAFF角色访问成功", "role", "MEDICAL_STAFF"));
    }

    @GetMapping("/followup")
    @PreAuthorize("hasRole('FOLLOWUP_STAFF')")
    @Operation(summary = "随访人员角色测试接口", description = "仅FOLLOWUP_STAFF角色可访问")
    public ResponseEntity<Map<String, String>> followup() {
        return ResponseEntity.ok(Map.of("message", "FOLLOWUP_STAFF角色访问成功", "role", "FOLLOWUP_STAFF"));
    }

    @GetMapping("/admin")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "管理员角色测试接口", description = "仅ADMIN角色可访问")
    public ResponseEntity<Map<String, String>> admin() {
        return ResponseEntity.ok(Map.of("message", "ADMIN角色访问成功", "role", "ADMIN"));
    }
}