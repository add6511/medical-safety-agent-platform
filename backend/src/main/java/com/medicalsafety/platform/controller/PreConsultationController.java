package com.medicalsafety.platform.controller;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.enums.PreConsultationStatus;
import com.medicalsafety.platform.service.PreConsultationService;
import com.medicalsafety.platform.service.AiTriageOrchestrationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/pre-consultations")
@RequiredArgsConstructor
@Tag(name = "预问诊管理", description = "预问诊流程和状态机接口")
public class PreConsultationController {

    private final PreConsultationService preConsultationService;
private final AiTriageOrchestrationService aiTriageOrchestrationService;

    @PostMapping
    @Operation(summary = "发起预问诊", description = "为就诊记录发起预问诊流程")
    public ResponseEntity<PreConsultationResponse> createPreConsultation(
            @Valid @RequestBody CreatePreConsultationRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(preConsultationService.createPreConsultation(request, getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取预问诊详情", description = "根据ID获取预问诊记录")
    public ResponseEntity<PreConsultationResponse> getPreConsultation(@PathVariable Long id) {
        return ResponseEntity.ok(preConsultationService.getPreConsultation(id, getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/record/{recordId}")
    @Operation(summary = "按就诊记录查询", description = "获取就诊记录下的所有预问诊")
    public ResponseEntity<List<PreConsultationResponse>> getByRecord(@PathVariable Long recordId) {
        return ResponseEntity.ok(preConsultationService.getPreConsultationsByRecord(recordId, getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/patient/{patientId}")
    @Operation(summary = "按患者查询", description = "获取患者的所有预问诊记录")
    public ResponseEntity<List<PreConsultationResponse>> getByPatient(@PathVariable Long patientId) {
        return ResponseEntity.ok(preConsultationService.getPreConsultationsByPatient(patientId, getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/status/{status}")
    @PreAuthorize("hasRole('MEDICAL_STAFF') or hasRole('ADMIN')")
    @Operation(summary = "按状态查询", description = "根据状态查询预问诊列表（医务人员/管理员）")
    public ResponseEntity<List<PreConsultationResponse>> getByStatus(@PathVariable PreConsultationStatus status) {
        return ResponseEntity.ok(preConsultationService.getPreConsultationsByStatus(status));
    }

    @PutMapping("/{id}/transition")
    @Operation(summary = "状态转换", description = "推进预问诊状态机")
    public ResponseEntity<PreConsultationResponse> transitionStatus(
            @PathVariable Long id,
            @RequestParam PreConsultationStatus status) {
        return ResponseEntity.ok(preConsultationService.transitionStatus(id, status, getCurrentUserId(), getCurrentRoles()));
    }

    @PostMapping("/{id}/review")
    @PreAuthorize("hasRole('MEDICAL_STAFF') or hasRole('ADMIN')")
    @Operation(summary = "审核预问诊", description = "医务人员审核预问诊结果（医务人员/管理员）")
    public ResponseEntity<PreConsultationResponse> reviewPreConsultation(
            @PathVariable Long id,
            @Valid @RequestBody ReviewPreConsultationRequest request) {
        return ResponseEntity.ok(preConsultationService.reviewPreConsultation(id, request, getCurrentUserId(), getCurrentRoles()));
    }
    @PostMapping("/{id}/ai-triage")
    @Operation(
            summary = "执行AI辅助分诊",
            description = "读取病例和症状，调用AI服务完成安全分诊并保存结果"
    )
    public ResponseEntity<TriageResultResponse> executeAiTriage(
            @PathVariable Long id) {

        return ResponseEntity.ok(
                aiTriageOrchestrationService
                        .analyzeAndPersist(
                                id,
                                getCurrentUserId(),
                                getCurrentRoles()
                        )
        );
    }
    @PutMapping("/{id}/cancel")
    @Operation(summary = "取消预问诊", description = "取消预问诊流程")
    public ResponseEntity<PreConsultationResponse> cancelPreConsultation(@PathVariable Long id) {
        return ResponseEntity.ok(preConsultationService.cancelPreConsultation(id, getCurrentUserId(), getCurrentRoles()));
    }

    private Long getCurrentUserId() {
        return (Long) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
    }

    private List<String> getCurrentRoles() {
        return SecurityContextHolder.getContext().getAuthentication().getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .map(a -> a.startsWith("ROLE_") ? a.substring(5) : a)
                .toList();
    }
}
