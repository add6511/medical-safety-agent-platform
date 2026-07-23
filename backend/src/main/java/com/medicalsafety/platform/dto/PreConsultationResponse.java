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
public class PreConsultationResponse {

    private Long id;
    private Long recordId;
    private Long patientId;
    private String status;
    private Long initiatedBy;
    private Long reviewedBy;
    private String reviewComment;
    private LocalDateTime reviewedAt;
    private LocalDateTime completedAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}