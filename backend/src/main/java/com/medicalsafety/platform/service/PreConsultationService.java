package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.MedicalRecord;
import com.medicalsafety.platform.entity.PreConsultation;
import com.medicalsafety.platform.enums.PreConsultationStatus;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.exception.AccessDeniedException;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.MedicalRecordRepository;
import com.medicalsafety.platform.repository.PreConsultationRepository;
import com.medicalsafety.platform.security.RequestContextHelper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
public class PreConsultationService {

    private static final Set<String> STAFF_ROLES = Set.of(
            RoleType.MEDICAL_STAFF.name(),
            RoleType.ADMIN.name()
    );
    private static final Set<String> AI_OR_ADMIN_ROLES = Set.of(
            RoleType.AI_SERVICE.name(),
            RoleType.ADMIN.name()
    );

    private final PreConsultationRepository preConsultationRepository;
    private final MedicalRecordRepository medicalRecordRepository;
    private final AuditLogService auditLogService;
    private final RequestContextHelper requestContextHelper;

    @Transactional
    public PreConsultationResponse createPreConsultation(CreatePreConsultationRequest request, Long operatorId, List<String> roles) {
        if (!medicalRecordRepository.existsById(request.getRecordId())) {
            throw new ResourceNotFoundException("就诊记录不存在");
        }
        var record = medicalRecordRepository.findById(request.getRecordId()).orElseThrow();
        if (!isStaff(roles) && !record.getPatientId().equals(operatorId)) {
            throw new AccessDeniedException("患者只能为自己发起预问诊");
        }
        PreConsultation pc = PreConsultation.builder()
                .recordId(request.getRecordId())
                .patientId(record.getPatientId())
                .initiatedBy(operatorId)
                .status(PreConsultationStatus.INITIATED)
                .build();
        pc = preConsultationRepository.save(pc);
        auditLogService.log(operatorId, requestContextHelper.getCurrentUsername(), "CREATE", "PRE_CONSULTATION", pc.getId(), "发起预问诊", requestContextHelper.getClientIp(), requestContextHelper.getTraceId());
        return toResponse(pc);
    }

    @Transactional(readOnly = true)
    public PreConsultationResponse getPreConsultation(Long id, Long operatorId, List<String> roles) {
        PreConsultation pc = findOrThrow(id);
        checkReadAccess(pc, operatorId, roles);
        return toResponse(pc);
    }

    @Transactional(readOnly = true)
    public List<PreConsultationResponse> getPreConsultationsByRecord(Long recordId, Long operatorId, List<String> roles) {
        if (!medicalRecordRepository.existsById(recordId)) {
            throw new ResourceNotFoundException("就诊记录不存在");
        }
        var record = medicalRecordRepository.findById(recordId).orElseThrow();
        if (!isStaff(roles) && !record.getPatientId().equals(operatorId)) {
            throw new AccessDeniedException("无权查看该就诊记录的预问诊");
        }
        return preConsultationRepository.findByRecordId(recordId).stream().map(this::toResponse).toList();
    }

    @Transactional(readOnly = true)
    public List<PreConsultationResponse> getPreConsultationsByPatient(Long patientId, Long operatorId, List<String> roles) {
        if (!isStaff(roles) && !patientId.equals(operatorId)) {
            throw new AccessDeniedException("患者只能查看自己的预问诊");
        }
        return preConsultationRepository.findByPatientId(patientId).stream().map(this::toResponse).toList();
    }

    @Transactional(readOnly = true)
    public List<PreConsultationResponse> getPreConsultationsByStatus(PreConsultationStatus status) {
        return preConsultationRepository.findByStatus(status).stream().map(this::toResponse).toList();
    }

    @Transactional
    public PreConsultationResponse transitionStatus(Long id, PreConsultationStatus targetStatus, Long operatorId, List<String> roles) {
        try {
            PreConsultation pc = findOrThrow(id);
            checkOwnerOrStaff(pc, operatorId, roles, "修改状态");
            if (!isStaff(roles) && targetStatus != PreConsultationStatus.CANCELLED) {
                throw new AccessDeniedException("患者只能取消预问诊，不能修改状态");
            }
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
            auditLogService.log(operatorId, requestContextHelper.getCurrentUsername(), "STATUS_CHANGE", "PRE_CONSULTATION", pc.getId(),
                    String.format("状态变更: %s -> %s", currentStatus, targetStatus), requestContextHelper.getClientIp(), requestContextHelper.getTraceId());
            return toResponse(pc);
        } catch (OptimisticLockingFailureException e) {
            throw new BusinessException("CONCURRENT_MODIFICATION", "数据已被其他操作修改，请刷新后重试");
        }
    }

    @Transactional
    public PreConsultationResponse reviewPreConsultation(Long id, ReviewPreConsultationRequest request, Long reviewerId, List<String> roles) {
        if (!isStaff(roles)) {
            throw new AccessDeniedException("只有医务人员可以审核预问诊");
        }
        try {
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
            } else {
                pc.setStatus(PreConsultationStatus.NEEDS_REVISION);
            }
            pc = preConsultationRepository.save(pc);
            auditLogService.log(reviewerId, requestContextHelper.getCurrentUsername(), "REVIEW", "PRE_CONSULTATION", pc.getId(),
                    "审核预问诊: " + (Boolean.TRUE.equals(request.getApproved()) ? "通过" : "需修改"), requestContextHelper.getClientIp(), requestContextHelper.getTraceId());
            return toResponse(pc);
        } catch (OptimisticLockingFailureException e) {
            throw new BusinessException("CONCURRENT_MODIFICATION", "数据已被其他操作修改，请刷新后重试");
        }
    }

    @Transactional
    public PreConsultationResponse cancelPreConsultation(Long id, Long operatorId, List<String> roles) {
        return transitionStatus(id, PreConsultationStatus.CANCELLED, operatorId, roles);
    }

    public boolean isAiOrAdmin(List<String> roles) {
        return roles.stream().anyMatch(AI_OR_ADMIN_ROLES::contains);
    }

    private void checkReadAccess(PreConsultation pc, Long operatorId, List<String> roles) {
        if (isStaff(roles)) return;
        if (!pc.getPatientId().equals(operatorId)) {
            throw new AccessDeniedException("无权访问该预问诊");
        }
    }

    private void checkOwnerOrStaff(PreConsultation pc, Long operatorId, List<String> roles, String action) {
        if (isStaff(roles)) return;
        if (!pc.getPatientId().equals(operatorId)) {
            throw new AccessDeniedException("无权" + action + "该预问诊");
        }
    }

    private boolean isStaff(List<String> roles) {
        return roles.stream().anyMatch(STAFF_ROLES::contains);
    }

    private PreConsultation findOrThrow(Long id) {
        return preConsultationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("预问诊记录不存在"));
    }

    private PreConsultationResponse toResponse(PreConsultation pc) {
        return PreConsultationResponse.builder()
                .id(pc.getId()).recordId(pc.getRecordId()).patientId(pc.getPatientId())
                .status(pc.getStatus().name()).initiatedBy(pc.getInitiatedBy())
                .reviewedBy(pc.getReviewedBy()).reviewComment(pc.getReviewComment())
                .reviewedAt(pc.getReviewedAt()).completedAt(pc.getCompletedAt())
                .createdAt(pc.getCreatedAt()).updatedAt(pc.getUpdatedAt())
                .build();
    }
}
