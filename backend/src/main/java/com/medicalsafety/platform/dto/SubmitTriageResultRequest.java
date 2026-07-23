package com.medicalsafety.platform.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SubmitTriageResultRequest {

    @NotNull(message = "预问诊ID不能为空")
    private Long preConsultationId;

    @NotBlank(message = "紧急程度不能为空")
    private String urgencyLevel;

    private String suggestedDepartment;

    private String riskFlags;

    private String reasoningSummary;

    private String referenceSources;
}