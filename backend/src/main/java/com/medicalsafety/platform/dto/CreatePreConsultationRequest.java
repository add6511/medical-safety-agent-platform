package com.medicalsafety.platform.dto;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CreatePreConsultationRequest {

    @NotNull(message = "就诊记录ID不能为空")
    private Long recordId;
}