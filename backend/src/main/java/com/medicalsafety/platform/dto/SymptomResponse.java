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
public class SymptomResponse {

    private Long id;
    private Long recordId;
    private String symptomName;
    private String bodyPart;
    private String severity;
    private String durationDesc;
    private LocalDateTime onsetTime;
    private String notes;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}