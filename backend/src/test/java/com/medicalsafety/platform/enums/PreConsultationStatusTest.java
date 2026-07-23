package com.medicalsafety.platform.enums;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PreConsultationStatusTest {

    @Test
    void initiatedCanTransitionToSymptomCollected() {
        assertTrue(PreConsultationStatus.INITIATED.canTransitionTo(PreConsultationStatus.SYMPTOM_COLLECTED));
    }

    @Test
    void initiatedCanTransitionToCancelled() {
        assertTrue(PreConsultationStatus.INITIATED.canTransitionTo(PreConsultationStatus.CANCELLED));
    }

    @Test
    void initiatedCannotTransitionToCompleted() {
        assertFalse(PreConsultationStatus.INITIATED.canTransitionTo(PreConsultationStatus.COMPLETED));
    }

    @Test
    void symptomCollectedCanTransitionToAiTriageCompleted() {
        assertTrue(PreConsultationStatus.SYMPTOM_COLLECTED.canTransitionTo(PreConsultationStatus.AI_TRIAGE_COMPLETED));
    }

    @Test
    void aiTriageCompletedCanTransitionToMedicalReviewCompleted() {
        assertTrue(PreConsultationStatus.AI_TRIAGE_COMPLETED.canTransitionTo(PreConsultationStatus.MEDICAL_REVIEW_COMPLETED));
    }

    @Test
    void aiTriageCompletedCanTransitionToNeedsRevision() {
        assertTrue(PreConsultationStatus.AI_TRIAGE_COMPLETED.canTransitionTo(PreConsultationStatus.NEEDS_REVISION));
    }

    @Test
    void needsRevisionCanTransitionToAiTriageCompleted() {
        assertTrue(PreConsultationStatus.NEEDS_REVISION.canTransitionTo(PreConsultationStatus.AI_TRIAGE_COMPLETED));
    }

    @Test
    void needsRevisionCanTransitionToCancelled() {
        assertTrue(PreConsultationStatus.NEEDS_REVISION.canTransitionTo(PreConsultationStatus.CANCELLED));
    }

    @Test
    void medicalReviewCompletedCanTransitionToCompleted() {
        assertTrue(PreConsultationStatus.MEDICAL_REVIEW_COMPLETED.canTransitionTo(PreConsultationStatus.COMPLETED));
    }

    @Test
    void completedCannotTransitionToAny() {
        assertFalse(PreConsultationStatus.COMPLETED.canTransitionTo(PreConsultationStatus.INITIATED));
        assertFalse(PreConsultationStatus.COMPLETED.canTransitionTo(PreConsultationStatus.CANCELLED));
    }

    @Test
    void cancelledCannotTransitionToAny() {
        assertFalse(PreConsultationStatus.CANCELLED.canTransitionTo(PreConsultationStatus.INITIATED));
    }

    @Test
    void anyStateCanCancelExceptCompletedAndCancelled() {
        assertTrue(PreConsultationStatus.INITIATED.canTransitionTo(PreConsultationStatus.CANCELLED));
        assertTrue(PreConsultationStatus.SYMPTOM_COLLECTED.canTransitionTo(PreConsultationStatus.CANCELLED));
        assertTrue(PreConsultationStatus.AI_TRIAGE_COMPLETED.canTransitionTo(PreConsultationStatus.CANCELLED));
        assertTrue(PreConsultationStatus.NEEDS_REVISION.canTransitionTo(PreConsultationStatus.CANCELLED));
        assertTrue(PreConsultationStatus.MEDICAL_REVIEW_COMPLETED.canTransitionTo(PreConsultationStatus.CANCELLED));
    }
}
