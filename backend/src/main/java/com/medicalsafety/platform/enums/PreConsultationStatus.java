package com.medicalsafety.platform.enums;

public enum PreConsultationStatus {
    INITIATED,
    SYMPTOM_COLLECTED,
    AI_TRIAGE_COMPLETED,
    NEEDS_REVISION,
    MEDICAL_REVIEW_COMPLETED,
    COMPLETED,
    CANCELLED;

    public boolean canTransitionTo(PreConsultationStatus target) {
        return switch (this) {
            case INITIATED -> target == SYMPTOM_COLLECTED || target == CANCELLED;
            case SYMPTOM_COLLECTED -> target == AI_TRIAGE_COMPLETED || target == CANCELLED;
            case AI_TRIAGE_COMPLETED -> target == MEDICAL_REVIEW_COMPLETED || target == NEEDS_REVISION || target == CANCELLED;
            case NEEDS_REVISION -> target == AI_TRIAGE_COMPLETED || target == CANCELLED;
            case MEDICAL_REVIEW_COMPLETED -> target == COMPLETED || target == CANCELLED;
            case COMPLETED, CANCELLED -> false;
        };
    }
}
