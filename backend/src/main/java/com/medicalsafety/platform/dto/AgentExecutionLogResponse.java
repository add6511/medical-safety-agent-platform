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
public class AgentExecutionLogResponse {

    private Long id;
    private Long preConsultationId;
    private String agentType;
    private String inputSummary;
    private String outputSummary;
    private String status;
    private String errorMessage;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private Long durationMs;
}