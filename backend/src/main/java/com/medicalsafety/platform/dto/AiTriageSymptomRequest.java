package com.medicalsafety.platform.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiTriageSymptomRequest {

    private String name;

    private Integer severity;

    private String duration;
}