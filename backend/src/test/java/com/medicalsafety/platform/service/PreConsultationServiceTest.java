package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.MedicalRecord;
import com.medicalsafety.platform.entity.PreConsultation;
import com.medicalsafety.platform.enums.MedicalRecordStatus;
import com.medicalsafety.platform.enums.PreConsultationStatus;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.MedicalRecordRepository;
import com.medicalsafety.platform.repository.PreConsultationRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PreConsultationServiceTest {

    @Mock private PreConsultationRepository preConsultationRepository;
    @Mock private MedicalRecordRepository medicalRecordRepository;
    @Mock private AuditLogService auditLogService;
    @InjectMocks private PreConsultationService preConsultationService;

    private MedicalRecord testRecord;
    private PreConsultation testPC;
    private static final List<String> ADMIN_ROLES = List.of("ADMIN");
    private static final List<String> PATIENT_ROLES = List.of("PATIENT");

    @BeforeEach
    void setUp() {
        testRecord = MedicalRecord.builder().id(1L).patientId(100L).caseCode("CASE-001").status(MedicalRecordStatus.ACTIVE).createdBy(100L).build();
        testPC = PreConsultation.builder().id(1L).recordId(1L).patientId(100L).initiatedBy(100L).status(PreConsultationStatus.INITIATED).build();
    }

    @Test
    void createPreConsultationSuccess() {
        when(medicalRecordRepository.existsById(1L)).thenReturn(true);
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenReturn(testPC);
        CreatePreConsultationRequest request = CreatePreConsultationRequest.builder().recordId(1L).build();
        assertEquals("INITIATED", preConsultationService.createPreConsultation(request, 100L, PATIENT_ROLES).getStatus());
    }

    @Test
    void patientCannotCreatePreConsultationForOther() {
        when(medicalRecordRepository.existsById(1L)).thenReturn(true);
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        CreatePreConsultationRequest request = CreatePreConsultationRequest.builder().recordId(1L).build();
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> preConsultationService.createPreConsultation(request, 999L, PATIENT_ROLES));
    }

    @Test
    void transitionInitiatedToSymptomCollected() {
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenAnswer(inv -> inv.getArgument(0));
        assertEquals("SYMPTOM_COLLECTED", preConsultationService.transitionStatus(1L, PreConsultationStatus.SYMPTOM_COLLECTED, 100L, ADMIN_ROLES).getStatus());
    }

    @Test
    void patientCannotTransitionToNonCancelled() {
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> preConsultationService.transitionStatus(1L, PreConsultationStatus.SYMPTOM_COLLECTED, 100L, PATIENT_ROLES));
    }

    @Test
    void patientCanCancelOwnPreConsultation() {
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenAnswer(inv -> inv.getArgument(0));
        assertEquals("CANCELLED", preConsultationService.cancelPreConsultation(1L, 100L, PATIENT_ROLES).getStatus());
    }

    @Test
    void patientCannotCancelOtherPreConsultation() {
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> preConsultationService.cancelPreConsultation(1L, 999L, PATIENT_ROLES));
    }

    @Test
    void reviewPreConsultationSuccess() {
        testPC.setStatus(PreConsultationStatus.AI_TRIAGE_COMPLETED);
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenAnswer(inv -> inv.getArgument(0));
        ReviewPreConsultationRequest request = ReviewPreConsultationRequest.builder().reviewComment("通过").approved(true).build();
        assertEquals("MEDICAL_REVIEW_COMPLETED", preConsultationService.reviewPreConsultation(1L, request, 2L, ADMIN_ROLES).getStatus());
    }

    @Test
    void patientCannotReviewPreConsultation() {
        testPC.setStatus(PreConsultationStatus.AI_TRIAGE_COMPLETED);

        ReviewPreConsultationRequest request = ReviewPreConsultationRequest.builder().reviewComment("通过").approved(true).build();
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> preConsultationService.reviewPreConsultation(1L, request, 100L, PATIENT_ROLES));
    }

    @Test
    void fullStateMachineFlow() {
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenAnswer(inv -> inv.getArgument(0));
        testPC.setStatus(PreConsultationStatus.SYMPTOM_COLLECTED);
        assertEquals("AI_TRIAGE_COMPLETED", preConsultationService.transitionStatus(1L, PreConsultationStatus.AI_TRIAGE_COMPLETED, 1L, ADMIN_ROLES).getStatus());
        testPC.setStatus(PreConsultationStatus.AI_TRIAGE_COMPLETED);
        assertEquals("MEDICAL_REVIEW_COMPLETED", preConsultationService.transitionStatus(1L, PreConsultationStatus.MEDICAL_REVIEW_COMPLETED, 1L, ADMIN_ROLES).getStatus());
        testPC.setStatus(PreConsultationStatus.MEDICAL_REVIEW_COMPLETED);
        assertEquals("COMPLETED", preConsultationService.transitionStatus(1L, PreConsultationStatus.COMPLETED, 1L, ADMIN_ROLES).getStatus());
    }

    @Test
    void reviewPreConsultationWrongStateFails() {
        testPC.setStatus(PreConsultationStatus.INITIATED);
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        ReviewPreConsultationRequest request = ReviewPreConsultationRequest.builder().reviewComment("审核").approved(true).build();
        assertThrows(BusinessException.class, () -> preConsultationService.reviewPreConsultation(1L, request, 2L, ADMIN_ROLES));
    }
}
