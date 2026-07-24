package com.medicalsafety.platform.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiTriageRequest {

    @JsonProperty("case_id")
    private String caseId;

    private Integer age;

    @Builder.Default
    private List<AiTriageSymptomRequest> symptoms = new ArrayList<>();

    @JsonProperty("red_flags")
    @Builder.Default
    private List<String> redFlags = new ArrayList<>();

    @JsonProperty("free_text")
    private String freeText;

    @JsonProperty("model_suggested_risk")
    private String modelSuggestedRisk;
}