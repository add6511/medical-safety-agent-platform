package com.medicalsafety.platform.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CreateMedicalRecordRequest {

    @NotNull(message = "患者ID不能为空")
    private Long patientId;

    @NotBlank(message = "病例编码不能为空")
    @Size(max = 50, message = "病例编码最长50字符")
    private String caseCode;

    @Size(max = 500, message = "主诉最长500字符")
    private String chiefComplaint;

    private String presentIllness;

    private String pastHistory;

    private String allergyHistory;
}