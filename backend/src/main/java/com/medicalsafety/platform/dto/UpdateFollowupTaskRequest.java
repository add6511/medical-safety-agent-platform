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
public class UpdateFollowupTaskRequest {

    @NotNull(message = "任务ID不能为空")
    private Long taskId;

    private String status;

    private String notes;
}