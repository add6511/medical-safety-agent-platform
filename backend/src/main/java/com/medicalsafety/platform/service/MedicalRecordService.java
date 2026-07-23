package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.MedicalRecord;
import com.medicalsafety.platform.entity.Symptom;
import com.medicalsafety.platform.enums.MedicalRecordStatus;
import com.medicalsafety.platform.enums.SymptomSeverity;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.MedicalRecordRepository;
import com.medicalsafety.platform.repository.SymptomRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class MedicalRecordService {

    private final MedicalRecordRepository medicalRecordRepository;
    private final SymptomRepository symptomRepository;
    private AuditLogService auditLogService;

    public void setAuditLogService(AuditLogService auditLogService) {
        this.auditLogService = auditLogService;
    }

    @Transactional
    public MedicalRecordResponse createRecord(CreateMedicalRecordRequest request, Long operatorId) {
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
        logAudit(operatorId, "CREATE", "MEDICAL_RECORD", record.getId(), "创建就诊记录: " + record.getCaseCode());

        return toRecordResponse(record);
    }

    @Transactional(readOnly = true)
    public MedicalRecordResponse getRecord(Long id) {
        MedicalRecord record = findRecordOrThrow(id);
        return toRecordResponse(record);
    }

    @Transactional(readOnly = true)
    public MedicalRecordResponse getRecordByCaseCode(String caseCode) {
        MedicalRecord record = medicalRecordRepository.findByCaseCode(caseCode)
                .orElseThrow(() -> new ResourceNotFoundException("就诊记录不存在: " + caseCode));
        return toRecordResponse(record);
    }

    @Transactional(readOnly = true)
    public List<MedicalRecordResponse> getRecordsByPatient(Long patientId) {
        return medicalRecordRepository.findByPatientId(patientId).stream()
                .map(this::toRecordResponse)
                .toList();
    }

    @Transactional
    public MedicalRecordResponse archiveRecord(Long id, Long operatorId) {
        MedicalRecord record = findRecordOrThrow(id);
        record.setStatus(MedicalRecordStatus.ARCHIVED);
        record = medicalRecordRepository.save(record);
        logAudit(operatorId, "ARCHIVE", "MEDICAL_RECORD", record.getId(), "归档就诊记录: " + record.getCaseCode());
        return toRecordResponse(record);
    }

    @Transactional
    public SymptomResponse addSymptom(CreateSymptomRequest request, Long operatorId) {
        findRecordOrThrow(request.getRecordId());

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
        logAudit(operatorId, "CREATE", "SYMPTOM", symptom.getId(), "添加症状: " + symptom.getSymptomName());
        return toSymptomResponse(symptom);
    }

    @Transactional(readOnly = true)
    public List<SymptomResponse> getSymptomsByRecord(Long recordId) {
        return symptomRepository.findByRecordId(recordId).stream()
                .map(this::toSymptomResponse)
                .toList();
    }

    @Transactional
    public void deleteSymptom(Long symptomId, Long operatorId) {
        Symptom symptom = symptomRepository.findById(symptomId)
                .orElseThrow(() -> new ResourceNotFoundException("症状记录不存在"));
        symptomRepository.delete(symptom);
        logAudit(operatorId, "DELETE", "SYMPTOM", symptomId, "删除症状: " + symptom.getSymptomName());
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

    private void logAudit(Long userId, String action, String resourceType, Long resourceId, String detail) {
        if (auditLogService != null) {
            auditLogService.log(userId, null, action, resourceType, resourceId, detail, null, null);
        }
    }
}