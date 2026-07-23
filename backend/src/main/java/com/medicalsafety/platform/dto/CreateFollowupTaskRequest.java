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
public class CreateFollowupTaskRequest {

    @NotNull(message = "预问诊ID不能为空")
    private Long preConsultationId;

    @NotNull(message = "被分配人ID不能为空")
    private Long assignedTo;

    @NotBlank(message = "任务类型不能为空")
    private String taskType;

    private String description;
}