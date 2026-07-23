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
public class UpdateAgentExecutionLogRequest {

    @NotNull(message = "Agent日志ID不能为空")
    private Long agentLogId;

    private String status;

    private String outputSummary;

    private String errorMessage;

    private Long durationMs;
}