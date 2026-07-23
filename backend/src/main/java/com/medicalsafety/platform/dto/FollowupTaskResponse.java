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
public class FollowupTaskResponse {

    private Long id;
    private Long preConsultationId;
    private Long assignedTo;
    private Long assignedBy;
    private String taskType;
    private String description;
    private String status;
    private LocalDateTime completedAt;
    private String notes;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}