package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.FollowupTask;
import com.medicalsafety.platform.enums.FollowupTaskStatus;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.exception.AccessDeniedException;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.FollowupTaskRepository;
import com.medicalsafety.platform.security.RequestContextHelper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
public class FollowupTaskService {

    private static final Set<String> MEDICAL_OR_ADMIN = Set.of(
            RoleType.MEDICAL_STAFF.name(),
            RoleType.ADMIN.name()
    );

    private final FollowupTaskRepository followupTaskRepository;
    private final AuditLogService auditLogService;
    private final RequestContextHelper requestContextHelper;

    @Transactional
    public FollowupTaskResponse createTask(CreateFollowupTaskRequest request, Long operatorId, List<String> roles) {
        if (!roles.stream().anyMatch(MEDICAL_OR_ADMIN::contains)) {
            throw new AccessDeniedException("只有医务人员可以分配随访任务");
        }
        FollowupTask task = FollowupTask.builder()
                .preConsultationId(request.getPreConsultationId())
                .assignedTo(request.getAssignedTo())
                .assignedBy(operatorId)
                .taskType(request.getTaskType())
                .description(request.getDescription())
                .status(FollowupTaskStatus.PENDING)
                .build();
        task = followupTaskRepository.save(task);
        auditLogService.log(operatorId, requestContextHelper.getCurrentUsername(), "CREATE", "FOLLOWUP_TASK", task.getId(), "分配随访任务", requestContextHelper.getClientIp(), requestContextHelper.getTraceId());
        return toResponse(task);
    }

    @Transactional(readOnly = true)
    public FollowupTaskResponse getTask(Long id, Long operatorId, List<String> roles) {
        FollowupTask task = findOrThrow(id);
        checkAccess(task, operatorId, roles);
        return toResponse(task);
    }

    @Transactional(readOnly = true)
    public List<FollowupTaskResponse> getMyTasks(Long operatorId, List<String> roles) {
        if (!roles.contains(RoleType.FOLLOWUP_STAFF.name()) && !roles.stream().anyMatch(MEDICAL_OR_ADMIN::contains)) {
            throw new AccessDeniedException("无权查看随访任务");
        }
        if (roles.stream().anyMatch(MEDICAL_OR_ADMIN::contains)) {
            return followupTaskRepository.findAll().stream().map(this::toResponse).toList();
        }
        return followupTaskRepository.findByAssignedTo(operatorId).stream().map(this::toResponse).toList();
    }

    @Transactional
    public FollowupTaskResponse updateTask(UpdateFollowupTaskRequest request, Long operatorId, List<String> roles) {
        FollowupTask task = findOrThrow(request.getTaskId());
        if (!roles.stream().anyMatch(MEDICAL_OR_ADMIN::contains) && !task.getAssignedTo().equals(operatorId)) {
            throw new AccessDeniedException("只能处理分配给自己的随访任务");
        }
        if (request.getStatus() != null) {
            FollowupTaskStatus newStatus;
            try { newStatus = FollowupTaskStatus.valueOf(request.getStatus()); }
            catch (IllegalArgumentException e) { throw new BusinessException("INVALID_TASK_STATUS", "无效的任务状态"); }
            if (task.getStatus() == FollowupTaskStatus.COMPLETED || task.getStatus() == FollowupTaskStatus.CANCELLED) {
                throw new BusinessException("TASK_ALREADY_FINISHED", "已结束的任务不能修改");
            }
            task.setStatus(newStatus);
            if (newStatus == FollowupTaskStatus.COMPLETED) {
                task.setCompletedAt(LocalDateTime.now());
            }
        }
        if (request.getNotes() != null) {
            task.setNotes(request.getNotes());
        }
        task = followupTaskRepository.save(task);
        auditLogService.log(operatorId, requestContextHelper.getCurrentUsername(), "UPDATE", "FOLLOWUP_TASK", task.getId(), "更新随访任务", requestContextHelper.getClientIp(), requestContextHelper.getTraceId());
        return toResponse(task);
    }

    private void checkAccess(FollowupTask task, Long operatorId, List<String> roles) {
        if (roles.stream().anyMatch(MEDICAL_OR_ADMIN::contains)) return;
        if (!task.getAssignedTo().equals(operatorId)) {
            throw new AccessDeniedException("只能查看分配给自己的随访任务");
        }
    }

    private FollowupTask findOrThrow(Long id) {
        return followupTaskRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("随访任务不存在"));
    }

    private FollowupTaskResponse toResponse(FollowupTask task) {
        return FollowupTaskResponse.builder()
                .id(task.getId()).preConsultationId(task.getPreConsultationId())
                .assignedTo(task.getAssignedTo()).assignedBy(task.getAssignedBy())
                .taskType(task.getTaskType()).description(task.getDescription())
                .status(task.getStatus().name()).completedAt(task.getCompletedAt())
                .notes(task.getNotes()).createdAt(task.getCreatedAt()).updatedAt(task.getUpdatedAt())
                .build();
    }
}