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
public class CreateAgentExecutionLogRequest {

    @NotNull(message = "预问诊ID不能为空")
    private Long preConsultationId;

    @NotBlank(message = "Agent类型不能为空")
    private String agentType;

    private String inputSummary;

}