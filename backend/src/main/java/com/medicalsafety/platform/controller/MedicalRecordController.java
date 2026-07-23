package com.medicalsafety.platform.controller;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.service.MedicalRecordService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/medical-records")
@RequiredArgsConstructor
@Tag(name = "就诊记录管理", description = "就诊记录和症状信息管理接口")
public class MedicalRecordController {

    private final MedicalRecordService medicalRecordService;

    @PostMapping
    @Operation(summary = "创建就诊记录", description = "医务人员创建新的就诊记录")
    public ResponseEntity<MedicalRecordResponse> createRecord(
            @Valid @RequestBody CreateMedicalRecordRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(medicalRecordService.createRecord(request, getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取就诊记录", description = "根据ID获取就诊记录详情")
    public ResponseEntity<MedicalRecordResponse> getRecord(@PathVariable Long id) {
        return ResponseEntity.ok(medicalRecordService.getRecord(id, getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/case-code/{caseCode}")
    @Operation(summary = "按病例编码查询", description = "根据病例编码获取就诊记录")
    public ResponseEntity<MedicalRecordResponse> getRecordByCaseCode(@PathVariable String caseCode) {
        return ResponseEntity.ok(medicalRecordService.getRecordByCaseCode(caseCode, getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/patient/{patientId}")
    @Operation(summary = "获取患者的就诊记录", description = "根据患者ID获取所有就诊记录")
    public ResponseEntity<List<MedicalRecordResponse>> getRecordsByPatient(@PathVariable Long patientId) {
        return ResponseEntity.ok(medicalRecordService.getRecordsByPatient(patientId, getCurrentUserId(), getCurrentRoles()));
    }

    @PutMapping("/{id}/archive")
    @Operation(summary = "归档就诊记录", description = "将就诊记录标记为已归档")
    public ResponseEntity<MedicalRecordResponse> archiveRecord(@PathVariable Long id) {
        return ResponseEntity.ok(medicalRecordService.archiveRecord(id, getCurrentUserId(), getCurrentRoles()));
    }

    @PostMapping("/{recordId}/symptoms")
    @Operation(summary = "添加症状", description = "为就诊记录添加症状信息")
    public ResponseEntity<SymptomResponse> addSymptom(
            @PathVariable Long recordId,
            @Valid @RequestBody CreateSymptomRequest request) {
        request.setRecordId(recordId);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(medicalRecordService.addSymptom(request, getCurrentUserId(), getCurrentRoles()));
    }

    @GetMapping("/{recordId}/symptoms")
    @Operation(summary = "获取症状列表", description = "获取就诊记录下的所有症状")
    public ResponseEntity<List<SymptomResponse>> getSymptoms(@PathVariable Long recordId) {
        return ResponseEntity.ok(medicalRecordService.getSymptomsByRecord(recordId, getCurrentUserId(), getCurrentRoles()));
    }

    @DeleteMapping("/symptoms/{symptomId}")
    @Operation(summary = "删除症状", description = "删除指定症状记录")
    public ResponseEntity<Void> deleteSymptom(@PathVariable Long symptomId) {
        medicalRecordService.deleteSymptom(symptomId, getCurrentUserId(), getCurrentRoles());
        return ResponseEntity.noContent().build();
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
