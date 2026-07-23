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
public class TriageResultResponse {

    private Long id;
    private Long preConsultationId;
    private String urgencyLevel;
    private String suggestedDepartment;
    private String riskFlags;
    private String reasoningSummary;
    private String referenceSources;
    private LocalDateTime createdAt;
}