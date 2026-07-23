package com.medicalsafety.platform.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewPreConsultationRequest {

    @NotBlank(message = "审核意见不能为空")
    private String reviewComment;

    private Boolean approved;
}