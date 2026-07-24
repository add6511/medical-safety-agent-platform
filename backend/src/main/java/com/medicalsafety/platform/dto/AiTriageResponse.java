package com.medicalsafety.platform.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AiTriageResponse {

    @JsonProperty("case_id")
    private String caseId;

    @JsonProperty("trace_id")
    private String traceId;

    @JsonProperty("risk_level")
    private String riskLevel;

    @JsonProperty("symptom_summary")
    private String symptomSummary;

    @JsonProperty("red_flags")
    @Builder.Default
    private List<String> redFlags = new ArrayList<>();

    @Builder.Default
    private List<Map<String, Object>> evidence = new ArrayList<>();

    @Builder.Default
    private List<Map<String, Object>> citations = new ArrayList<>();

    @JsonProperty("missing_information")
    @Builder.Default
    private List<String> missingInformation = new ArrayList<>();

    @JsonProperty("followup_questions")
    @Builder.Default
    private List<String> followupQuestions = new ArrayList<>();

    @JsonProperty("safety_status")
    private String safetyStatus;

    @JsonProperty("safety_flags")
    @Builder.Default
    private List<String> safetyFlags = new ArrayList<>();

    @JsonProperty("sanitized_input")
    private String sanitizedInput;

    @JsonProperty("needs_human_review")
    private Boolean needsHumanReview;

    private String disclaimer;
}