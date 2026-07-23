package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.MedicalRecord;
import com.medicalsafety.platform.entity.Symptom;
import com.medicalsafety.platform.enums.MedicalRecordStatus;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.enums.SymptomSeverity;
import com.medicalsafety.platform.exception.AccessDeniedException;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.MedicalRecordRepository;
import com.medicalsafety.platform.repository.SymptomRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
public class MedicalRecordService {

    private static final Set<String> STAFF_ROLES = Set.of(
            RoleType.MEDICAL_STAFF.name(),
            RoleType.ADMIN.name()
    );

    private final MedicalRecordRepository medicalRecordRepository;
    private final SymptomRepository symptomRepository;
    private final AuditLogService auditLogService;

    @Transactional
    public MedicalRecordResponse createRecord(CreateMedicalRecordRequest request, Long operatorId, List<String> roles) {
        if (!isStaff(roles) && !request.getPatientId().equals(operatorId)) {
            throw new AccessDeniedException("患者只能创建自己的就诊记录");
        }

        if (medicalRecordRepository.existsByCaseCode(request.getCaseCode())) {
            throw new BusinessException("CASE_CODE_DUPLICATE", "病例编码已存在: " + request.getCaseCode());
        }

        MedicalRecord record = MedicalRecord.builder()
                .patientId(request.getPatientId())
                .caseCode(request.getCaseCode())
                .chiefComplaint(request.getChiefComplaint())
                .presentIllness(request.getPresentIllness())
                .pastHistory(request.getPastHistory())
                .allergyHistory(request.getAllergyHistory())
                .createdBy(operatorId)
                .build();

        record = medicalRecordRepository.save(record);
        auditLogService.log(operatorId, null, "CREATE", "MEDICAL_RECORD", record.getId(),
                "创建就诊记录: " + record.getCaseCode(), null, null);

        return toRecordResponse(record);
    }

    @Transactional(readOnly = true)
    public MedicalRecordResponse getRecord(Long id, Long operatorId, List<String> roles) {
        MedicalRecord record = findRecordOrThrow(id);
        checkReadAccess(record, operatorId, roles);
        return toRecordResponse(record);
    }

    @Transactional(readOnly = true)
    public MedicalRecordResponse getRecordByCaseCode(String caseCode, Long operatorId, List<String> roles) {
        MedicalRecord record = medicalRecordRepository.findByCaseCode(caseCode)
                .orElseThrow(() -> new ResourceNotFoundException("就诊记录不存在: " + caseCode));
        checkReadAccess(record, operatorId, roles);
        return toRecordResponse(record);
    }

    @Transactional(readOnly = true)
    public List<MedicalRecordResponse> getRecordsByPatient(Long patientId, Long operatorId, List<String> roles) {
        if (!isStaff(roles) && !patientId.equals(operatorId)) {
            throw new AccessDeniedException("患者只能查看自己的就诊记录");
        }
        return medicalRecordRepository.findByPatientId(patientId).stream()
                .map(this::toRecordResponse)
                .toList();
    }

    @Transactional
    public MedicalRecordResponse archiveRecord(Long id, Long operatorId, List<String> roles) {
        MedicalRecord record = findRecordOrThrow(id);
        checkOwnerOrStaff(record, operatorId, roles, "归档");
        record.setStatus(MedicalRecordStatus.ARCHIVED);
        record = medicalRecordRepository.save(record);
        auditLogService.log(operatorId, null, "ARCHIVE", "MEDICAL_RECORD", record.getId(),
                "归档就诊记录: " + record.getCaseCode(), null, null);
        return toRecordResponse(record);
    }

    @Transactional
    public SymptomResponse addSymptom(CreateSymptomRequest request, Long operatorId, List<String> roles) {
        MedicalRecord record = findRecordOrThrow(request.getRecordId());
        checkOwnerOrStaff(record, operatorId, roles, "添加症状");

        Symptom symptom = Symptom.builder()
                .recordId(request.getRecordId())
                .symptomName(request.getSymptomName())
                .bodyPart(request.getBodyPart())
                .severity(parseSeverity(request.getSeverity()))
                .durationDesc(request.getDurationDesc())
                .onsetTime(request.getOnsetTime())
                .notes(request.getNotes())
                .build();

        symptom = symptomRepository.save(symptom);
        auditLogService.log(operatorId, null, "CREATE", "SYMPTOM", symptom.getId(),
                "添加症状: " + symptom.getSymptomName(), null, null);
        return toSymptomResponse(symptom);
    }

    @Transactional(readOnly = true)
    public List<SymptomResponse> getSymptomsByRecord(Long recordId, Long operatorId, List<String> roles) {
        MedicalRecord record = findRecordOrThrow(recordId);
        checkReadAccess(record, operatorId, roles);
        return symptomRepository.findByRecordId(recordId).stream()
                .map(this::toSymptomResponse)
                .toList();
    }

    @Transactional
    public void deleteSymptom(Long symptomId, Long operatorId, List<String> roles) {
        Symptom symptom = symptomRepository.findById(symptomId)
                .orElseThrow(() -> new ResourceNotFoundException("症状记录不存在"));
        MedicalRecord record = findRecordOrThrow(symptom.getRecordId());
        checkOwnerOrStaff(record, operatorId, roles, "删除症状");
        symptomRepository.delete(symptom);
        auditLogService.log(operatorId, null, "DELETE", "SYMPTOM", symptomId,
                "删除症状: " + symptom.getSymptomName(), null, null);
    }

    private void checkReadAccess(MedicalRecord record, Long operatorId, List<String> roles) {
        if (isStaff(roles)) {
            return;
        }
        if (!record.getPatientId().equals(operatorId)) {
            throw new AccessDeniedException("无权访问该就诊记录");
        }
    }

    private void checkOwnerOrStaff(MedicalRecord record, Long operatorId, List<String> roles, String action) {
        if (isStaff(roles)) {
            return;
        }
        if (!record.getPatientId().equals(operatorId)) {
            throw new AccessDeniedException("无权" + action + "该就诊记录");
        }
    }

    private boolean isStaff(List<String> roles) {
        return roles.stream().anyMatch(STAFF_ROLES::contains);
    }

    private MedicalRecord findRecordOrThrow(Long id) {
        return medicalRecordRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("就诊记录不存在"));
    }

    private SymptomSeverity parseSeverity(String severity) {
        if (severity == null || severity.isBlank()) {
            return SymptomSeverity.MODERATE;
        }
        try {
            return SymptomSeverity.valueOf(severity);
        } catch (IllegalArgumentException e) {
            throw new BusinessException("INVALID_SEVERITY", "无效的严重程度: " + severity);
        }
    }

    private MedicalRecordResponse toRecordResponse(MedicalRecord record) {
        List<SymptomResponse> symptoms = symptomRepository.findByRecordId(record.getId()).stream()
                .map(this::toSymptomResponse)
                .toList();

        return MedicalRecordResponse.builder()
                .id(record.getId())
                .patientId(record.getPatientId())
                .caseCode(record.getCaseCode())
                .chiefComplaint(record.getChiefComplaint())
                .presentIllness(record.getPresentIllness())
                .pastHistory(record.getPastHistory())
                .allergyHistory(record.getAllergyHistory())
                .status(record.getStatus().name())
                .createdBy(record.getCreatedBy())
                .createdAt(record.getCreatedAt())
                .updatedAt(record.getUpdatedAt())
                .symptoms(symptoms)
                .build();
    }

    private SymptomResponse toSymptomResponse(Symptom symptom) {
        return SymptomResponse.builder()
                .id(symptom.getId())
                .recordId(symptom.getRecordId())
                .symptomName(symptom.getSymptomName())
                .bodyPart(symptom.getBodyPart())
                .severity(symptom.getSeverity().name())
                .durationDesc(symptom.getDurationDesc())
                .onsetTime(symptom.getOnsetTime())
                .notes(symptom.getNotes())
                .createdAt(symptom.getCreatedAt())
                .updatedAt(symptom.getUpdatedAt())
                .build();
    }
}
