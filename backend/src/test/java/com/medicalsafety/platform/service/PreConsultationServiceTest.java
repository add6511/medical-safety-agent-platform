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

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PreConsultationServiceTest {

    @Mock
    private PreConsultationRepository preConsultationRepository;

    @Mock
    private MedicalRecordRepository medicalRecordRepository;

    @Mock
    private AuditLogService auditLogService;

    @InjectMocks
    private PreConsultationService preConsultationService;

    private MedicalRecord testRecord;
    private PreConsultation testPC;

    @BeforeEach
    void setUp() {
        preConsultationService.setAuditLogService(auditLogService);

        testRecord = MedicalRecord.builder()
                .id(1L)
                .patientId(100L)
                .caseCode("CASE-001")
                .status(MedicalRecordStatus.ACTIVE)
                .createdBy(1L)
                .build();

        testPC = PreConsultation.builder()
                .id(1L)
                .recordId(1L)
                .patientId(100L)
                .initiatedBy(1L)
                .status(PreConsultationStatus.INITIATED)
                .build();
    }

    @Test
    void createPreConsultationSuccess() {
        when(medicalRecordRepository.existsById(1L)).thenReturn(true);
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenReturn(testPC);

        CreatePreConsultationRequest request = CreatePreConsultationRequest.builder().recordId(1L).build();
        PreConsultationResponse response = preConsultationService.createPreConsultation(request, 1L);

        assertNotNull(response);
        assertEquals("INITIATED", response.getStatus());
    }

    @Test
    void createPreConsultationRecordNotFound() {
        when(medicalRecordRepository.existsById(999L)).thenReturn(false);

        CreatePreConsultationRequest request = CreatePreConsultationRequest.builder().recordId(999L).build();
        assertThrows(ResourceNotFoundException.class, () -> preConsultationService.createPreConsultation(request, 1L));
    }

    @Test
    void transitionInitiatedToSymptomCollected() {
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenAnswer(inv -> inv.getArgument(0));

        PreConsultationResponse response = preConsultationService.transitionStatus(1L, PreConsultationStatus.SYMPTOM_COLLECTED, 1L);

        assertEquals("SYMPTOM_COLLECTED", response.getStatus());
    }

    @Test
    void transitionInitiatedToAiTriageCompletedFails() {
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));

        assertThrows(BusinessException.class,
                () -> preConsultationService.transitionStatus(1L, PreConsultationStatus.AI_TRIAGE_COMPLETED, 1L));
    }

    @Test
    void transitionCompletedToAnyFails() {
        testPC.setStatus(PreConsultationStatus.COMPLETED);
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));

        assertThrows(BusinessException.class,
                () -> preConsultationService.transitionStatus(1L, PreConsultationStatus.INITIATED, 1L));
    }

    @Test
    void fullStateMachineFlow() {
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenAnswer(inv -> inv.getArgument(0));

        PreConsultationResponse r1 = preConsultationService.transitionStatus(1L, PreConsultationStatus.SYMPTOM_COLLECTED, 1L);
        assertEquals("SYMPTOM_COLLECTED", r1.getStatus());

        testPC.setStatus(PreConsultationStatus.SYMPTOM_COLLECTED);
        PreConsultationResponse r2 = preConsultationService.transitionStatus(1L, PreConsultationStatus.AI_TRIAGE_COMPLETED, 1L);
        assertEquals("AI_TRIAGE_COMPLETED", r2.getStatus());

        testPC.setStatus(PreConsultationStatus.AI_TRIAGE_COMPLETED);
        PreConsultationResponse r3 = preConsultationService.transitionStatus(1L, PreConsultationStatus.MEDICAL_REVIEW_COMPLETED, 1L);
        assertEquals("MEDICAL_REVIEW_COMPLETED", r3.getStatus());

        testPC.setStatus(PreConsultationStatus.MEDICAL_REVIEW_COMPLETED);
        PreConsultationResponse r4 = preConsultationService.transitionStatus(1L, PreConsultationStatus.COMPLETED, 1L);
        assertEquals("COMPLETED", r4.getStatus());
    }

    @Test
    void cancelFromInitiated() {
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenAnswer(inv -> inv.getArgument(0));

        PreConsultationResponse response = preConsultationService.cancelPreConsultation(1L, 1L);
        assertEquals("CANCELLED", response.getStatus());
    }

    @Test
    void cancelFromCompletedFails() {
        testPC.setStatus(PreConsultationStatus.COMPLETED);
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));

        assertThrows(BusinessException.class, () -> preConsultationService.cancelPreConsultation(1L, 1L));
    }

    @Test
    void reviewPreConsultationSuccess() {
        testPC.setStatus(PreConsultationStatus.AI_TRIAGE_COMPLETED);
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));
        when(preConsultationRepository.save(any(PreConsultation.class))).thenAnswer(inv -> inv.getArgument(0));

        ReviewPreConsultationRequest request = ReviewPreConsultationRequest.builder()
                .reviewComment("审核通过")
                .approved(true)
                .build();

        PreConsultationResponse response = preConsultationService.reviewPreConsultation(1L, request, 2L);

        assertEquals("MEDICAL_REVIEW_COMPLETED", response.getStatus());
        assertEquals(2L, response.getReviewedBy());
        assertEquals("审核通过", response.getReviewComment());
    }

    @Test
    void reviewPreConsultationWrongStateFails() {
        testPC.setStatus(PreConsultationStatus.INITIATED);
        when(preConsultationRepository.findById(1L)).thenReturn(Optional.of(testPC));

        ReviewPreConsultationRequest request = ReviewPreConsultationRequest.builder()
                .reviewComment("审核")
                .approved(true)
                .build();

        assertThrows(BusinessException.class, () -> preConsultationService.reviewPreConsultation(1L, request, 2L));
    }
}