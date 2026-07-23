package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.PreConsultation;
import com.medicalsafety.platform.enums.PreConsultationStatus;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.MedicalRecordRepository;
import com.medicalsafety.platform.repository.PreConsultationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class PreConsultationService {

    private final PreConsultationRepository preConsultationRepository;
    private final MedicalRecordRepository medicalRecordRepository;
    private AuditLogService auditLogService;

    public void setAuditLogService(AuditLogService auditLogService) {
        this.auditLogService = auditLogService;
    }

    @Transactional
    public PreConsultationResponse createPreConsultation(CreatePreConsultationRequest request, Long operatorId) {
        if (!medicalRecordRepository.existsById(request.getRecordId())) {
            throw new ResourceNotFoundException("就诊记录不存在");
        }


        var record = medicalRecordRepository.findById(request.getRecordId()).orElseThrow();

        PreConsultation pc = PreConsultation.builder()
                .recordId(request.getRecordId())
                .patientId(record.getPatientId())
                .initiatedBy(operatorId)
                .status(PreConsultationStatus.INITIATED)
                .build();

        pc = preConsultationRepository.save(pc);
        logAudit(operatorId, "CREATE", "PRE_CONSULTATION", pc.getId(), "发起预问诊");
        return toResponse(pc);
    }

    @Transactional(readOnly = true)
    public PreConsultationResponse getPreConsultation(Long id) {
        return toResponse(findOrThrow(id));
    }

    @Transactional(readOnly = true)
    public List<PreConsultationResponse> getPreConsultationsByRecord(Long recordId) {
        return preConsultationRepository.findByRecordId(recordId).stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<PreConsultationResponse> getPreConsultationsByPatient(Long patientId) {
        return preConsultationRepository.findByPatientId(patientId).stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<PreConsultationResponse> getPreConsultationsByStatus(PreConsultationStatus status) {
        return preConsultationRepository.findByStatus(status).stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional
    public PreConsultationResponse transitionStatus(Long id, PreConsultationStatus targetStatus, Long operatorId) {
        PreConsultation pc = findOrThrow(id);
        PreConsultationStatus currentStatus = pc.getStatus();

        if (!currentStatus.canTransitionTo(targetStatus)) {
            throw new BusinessException("INVALID_STATE_TRANSITION",
                    String.format("不允许从 %s 转换到 %s", currentStatus, targetStatus));
        }

        pc.setStatus(targetStatus);

        if (targetStatus == PreConsultationStatus.COMPLETED) {
            pc.setCompletedAt(LocalDateTime.now());
        }

        pc = preConsultationRepository.save(pc);
        logAudit(operatorId, "STATUS_CHANGE", "PRE_CONSULTATION", pc.getId(),
                String.format("状态变更: %s -> %s", currentStatus, targetStatus));
        return toResponse(pc);
    }

    @Transactional
    public PreConsultationResponse reviewPreConsultation(Long id, ReviewPreConsultationRequest request, Long reviewerId) {
        PreConsultation pc = findOrThrow(id);

        if (pc.getStatus() != PreConsultationStatus.AI_TRIAGE_COMPLETED) {
            throw new BusinessException("INVALID_REVIEW_STATE",
                    "只有AI分诊完成的预问诊才能审核，当前状态: " + pc.getStatus());
        }

        pc.setReviewedBy(reviewerId);
        pc.setReviewComment(request.getReviewComment());
        pc.setReviewedAt(LocalDateTime.now());

        if (Boolean.TRUE.equals(request.getApproved())) {
            pc.setStatus(PreConsultationStatus.MEDICAL_REVIEW_COMPLETED);
        }

        pc = preConsultationRepository.save(pc);
        logAudit(reviewerId, "REVIEW", "PRE_CONSULTATION", pc.getId(),
                "审核预问诊: " + (Boolean.TRUE.equals(request.getApproved()) ? "通过" : "记录意见"));
        return toResponse(pc);
    }

    @Transactional
    public PreConsultationResponse cancelPreConsultation(Long id, Long operatorId) {
        return transitionStatus(id, PreConsultationStatus.CANCELLED, operatorId);
    }

    private PreConsultation findOrThrow(Long id) {
        return preConsultationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("预问诊记录不存在"));
    }

    private PreConsultationResponse toResponse(PreConsultation pc) {
        return PreConsultationResponse.builder()
                .id(pc.getId())
                .recordId(pc.getRecordId())
                .patientId(pc.getPatientId())
                .status(pc.getStatus().name())
                .initiatedBy(pc.getInitiatedBy())
                .reviewedBy(pc.getReviewedBy())
                .reviewComment(pc.getReviewComment())
                .reviewedAt(pc.getReviewedAt())
                .completedAt(pc.getCompletedAt())
                .createdAt(pc.getCreatedAt())
                .updatedAt(pc.getUpdatedAt())
                .build();
    }

    private void logAudit(Long userId, String action, String resourceType, Long resourceId, String detail) {
        if (auditLogService != null) {
            auditLogService.log(userId, null, action, resourceType, resourceId, detail, null, null);
        }
    }
}