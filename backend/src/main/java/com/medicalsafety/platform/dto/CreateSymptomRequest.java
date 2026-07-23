package com.medicalsafety.platform.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CreateSymptomRequest {

    @NotNull(message = "就诊记录ID不能为空")
    private Long recordId;

    @NotBlank(message = "症状名称不能为空")
    @Size(max = 200, message = "症状名称最长200字符")
    private String symptomName;

    @Size(max = 100, message = "部位最长100字符")
    private String bodyPart;

    private String severity;

    @Size(max = 200, message = "持续时间描述最长200字符")
    private String durationDesc;

    private LocalDateTime onsetTime;

    private String notes;
}