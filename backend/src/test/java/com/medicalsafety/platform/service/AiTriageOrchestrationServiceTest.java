package com.medicalsafety.platform.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medicalsafety.platform.dto.AiTriageRequest;
import com.medicalsafety.platform.dto.AiTriageResponse;
import com.medicalsafety.platform.dto.SubmitTriageResultRequest;
import com.medicalsafety.platform.dto.TriageResultResponse;
import com.medicalsafety.platform.entity.MedicalRecord;
import com.medicalsafety.platform.entity.PreConsultation;
import com.medicalsafety.platform.entity.Symptom;
import com.medicalsafety.platform.enums.PreConsultationStatus;
import com.medicalsafety.platform.enums.SymptomSeverity;
import com.medicalsafety.platform.exception.AccessDeniedException;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.repository.MedicalRecordRepository;
import com.medicalsafety.platform.repository.PreConsultationRepository;
import com.medicalsafety.platform.repository.SymptomRepository;
import com.medicalsafety.platform.security.RequestContextHelper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AiTriageOrchestrationServiceTest {

    @Mock
    private AiTriageClient aiTriageClient;

    @Mock
    private TriageResultService triageResultService;

    @Mock
    private PreConsultationRepository preConsultationRepository;

    @Mock
    private MedicalRecordRepository medicalRecordRepository;

    @Mock
    private SymptomRepository symptomRepository;

    @Mock
    private RequestContextHelper requestContextHelper;

    private AiTriageOrchestrationService service;

    @BeforeEach
    void setUp() {
        service = new AiTriageOrchestrationService(
                aiTriageClient,
                triageResultService,
                preConsultationRepository,
                medicalRecordRepository,
                symptomRepository,
                requestContextHelper,
                new ObjectMapper()
        );
    }

    @Test
    void shouldAnalyzeHighRiskCaseAndPersistResult() {
        Long operatorId = 1L;
        Long preConsultationId = 10L;
        Long recordId = 20L;

        PreConsultation preConsultation =
                PreConsultation.builder()
                        .id(preConsultationId)
                        .recordId(recordId)
                        .patientId(operatorId)
                        .initiatedBy(operatorId)
                        .status(
                                PreConsultationStatus.INITIATED
                        )
                        .build();

        MedicalRecord record =
                MedicalRecord.builder()
                        .id(recordId)
                        .patientId(operatorId)
                        .caseCode("SYN-TEST-001")
                        .chiefComplaint("持续胸部不适")
                        .presentIllness("持续30分钟")
                        .pastHistory("合成教学数据")
                        .allergyHistory("无已知过敏")
                        .createdBy(operatorId)
                        .build();

        Symptom symptom =
                Symptom.builder()
                        .id(30L)
                        .recordId(recordId)
                        .symptomName("持续胸部不适")
                        .severity(SymptomSeverity.SEVERE)
                        .durationDesc("30分钟")
                        .build();

        AiTriageResponse aiResponse =
                AiTriageResponse.builder()
                        .caseId("SYN-TEST-001")
                        .traceId("ai-trace-001")
                        .riskLevel("HIGH")
                        .symptomSummary("持续胸部不适30分钟")
                        .redFlags(
                                List.of(
                                        "persistent_chest_discomfort"
                                )
                        )
                        .evidence(List.of())
                        .citations(List.of())
                        .missingInformation(List.of())
                        .followupQuestions(List.of())
                        .safetyStatus("human_review")
                        .safetyFlags(List.of())
                        .sanitizedInput("合成教学病例")
                        .needsHumanReview(true)
                        .disclaimer("仅供教学演示")
                        .build();

        TriageResultResponse savedResult =
                TriageResultResponse.builder()
                        .id(40L)
                        .preConsultationId(
                                preConsultationId
                        )
                        .urgencyLevel("URGENT")
                        .build();

        when(
                preConsultationRepository.findById(
                        preConsultationId
                )
        ).thenReturn(Optional.of(preConsultation));

        when(
                medicalRecordRepository.findById(recordId)
        ).thenReturn(Optional.of(record));

        when(
                symptomRepository.findByRecordId(recordId)
        ).thenReturn(List.of(symptom));

        when(
                requestContextHelper.getTraceId()
        ).thenReturn("spring-trace-001");

        when(
                aiTriageClient.analyze(
                        any(AiTriageRequest.class),
                        eq("spring-trace-001")
                )
        ).thenReturn(aiResponse);

        when(
                triageResultService
                        .submitInternalTriageResult(
                                any(
                                        SubmitTriageResultRequest.class
                                ),
                                eq(operatorId)
                        )
        ).thenReturn(savedResult);

        TriageResultResponse result =
                service.analyzeAndPersist(
                        preConsultationId,
                        operatorId,
                        List.of("PATIENT")
                );

        assertEquals(40L, result.getId());

        assertEquals(
                PreConsultationStatus.SYMPTOM_COLLECTED,
                preConsultation.getStatus()
        );

        verify(
                preConsultationRepository
        ).save(preConsultation);

        ArgumentCaptor<AiTriageRequest> aiRequestCaptor =
                ArgumentCaptor.forClass(
                        AiTriageRequest.class
                );

        verify(aiTriageClient).analyze(
                aiRequestCaptor.capture(),
                eq("spring-trace-001")
        );

        AiTriageRequest capturedAiRequest =
                aiRequestCaptor.getValue();

        assertEquals(
                "SYN-TEST-001",
                capturedAiRequest.getCaseId()
        );

        assertEquals(
                List.of(
                        "persistent_chest_discomfort"
                ),
                capturedAiRequest.getRedFlags()
        );

        assertEquals(
                1,
                capturedAiRequest.getSymptoms().size()
        );

        assertEquals(
                9,
                capturedAiRequest
                        .getSymptoms()
                        .getFirst()
                        .getSeverity()
        );

        ArgumentCaptor<SubmitTriageResultRequest>
                resultRequestCaptor =
                ArgumentCaptor.forClass(
                        SubmitTriageResultRequest.class
                );

        verify(triageResultService)
                .submitInternalTriageResult(
                        resultRequestCaptor.capture(),
                        eq(operatorId)
                );

        SubmitTriageResultRequest capturedResult =
                resultRequestCaptor.getValue();

        assertEquals(
                preConsultationId,
                capturedResult.getPreConsultationId()
        );

        assertEquals(
                "URGENT",
                capturedResult.getUrgencyLevel()
        );

        assertTrue(
                capturedResult
                        .getRiskFlags()
                        .contains(
                                "persistent_chest_discomfort"
                        )
        );

        assertTrue(
                capturedResult
                        .getRiskFlags()
                        .contains("human_review")
        );

        assertTrue(
                capturedResult
                        .getRiskFlags()
                        .contains(
                                "\"needsHumanReview\":true"
                        )
        );
    }

    @Test
    void shouldAllowMedicalStaffToAnalyzePatientCase() {
        PreConsultation preConsultation =
                PreConsultation.builder()
                        .id(11L)
                        .recordId(21L)
                        .patientId(100L)
                        .initiatedBy(100L)
                        .status(
                                PreConsultationStatus
                                        .SYMPTOM_COLLECTED
                        )
                        .build();

        MedicalRecord record =
                MedicalRecord.builder()
                        .id(21L)
                        .patientId(100L)
                        .caseCode("SYN-STAFF-001")
                        .createdBy(100L)
                        .build();

        Symptom symptom =
                Symptom.builder()
                        .id(31L)
                        .recordId(21L)
                        .symptomName("一般不适")
                        .severity(
                                SymptomSeverity.MODERATE
                        )
                        .durationDesc("1天")
                        .build();

        AiTriageResponse aiResponse =
                AiTriageResponse.builder()
                        .caseId("SYN-STAFF-001")
                        .traceId("ai-trace-staff")
                        .riskLevel("LOW")
                        .symptomSummary("一般不适")
                        .redFlags(List.of())
                        .evidence(List.of())
                        .citations(List.of())
                        .safetyStatus("pass")
                        .safetyFlags(List.of())
                        .needsHumanReview(false)
                        .disclaimer("仅供教学演示")
                        .build();

        when(
                preConsultationRepository.findById(11L)
        ).thenReturn(Optional.of(preConsultation));

        when(
                medicalRecordRepository.findById(21L)
        ).thenReturn(Optional.of(record));

        when(
                symptomRepository.findByRecordId(21L)
        ).thenReturn(List.of(symptom));

        when(
                requestContextHelper.getTraceId()
        ).thenReturn("spring-trace-staff");

        when(
                aiTriageClient.analyze(
                        any(AiTriageRequest.class),
                        eq("spring-trace-staff")
                )
        ).thenReturn(aiResponse);

        when(
                triageResultService
                        .submitInternalTriageResult(
                                any(
                                        SubmitTriageResultRequest.class
                                ),
                                eq(2L)
                        )
        ).thenReturn(
                TriageResultResponse.builder()
                        .id(41L)
                        .preConsultationId(11L)
                        .urgencyLevel("ROUTINE")
                        .build()
        );

        TriageResultResponse result =
                service.analyzeAndPersist(
                        11L,
                        2L,
                        List.of("MEDICAL_STAFF")
                );

        assertEquals("ROUTINE", result.getUrgencyLevel());

        verify(aiTriageClient).analyze(
                any(AiTriageRequest.class),
                eq("spring-trace-staff")
        );
    }

    @Test
    void shouldRejectDifferentPatient() {
        PreConsultation preConsultation =
                PreConsultation.builder()
                        .id(12L)
                        .recordId(22L)
                        .patientId(100L)
                        .initiatedBy(100L)
                        .status(
                                PreConsultationStatus.INITIATED
                        )
                        .build();

        when(
                preConsultationRepository.findById(12L)
        ).thenReturn(Optional.of(preConsultation));

        assertThrows(
                AccessDeniedException.class,
                () -> service.analyzeAndPersist(
                        12L,
                        200L,
                        List.of("PATIENT")
                )
        );

        verify(
                medicalRecordRepository,
                never()
        ).findById(any());

        verify(
                aiTriageClient,
                never()
        ).analyze(any(), any());
    }

    @Test
    void shouldRejectCaseWithoutSymptoms() {
        PreConsultation preConsultation =
                PreConsultation.builder()
                        .id(13L)
                        .recordId(23L)
                        .patientId(1L)
                        .initiatedBy(1L)
                        .status(
                                PreConsultationStatus.INITIATED
                        )
                        .build();

        MedicalRecord record =
                MedicalRecord.builder()
                        .id(23L)
                        .patientId(1L)
                        .caseCode("SYN-EMPTY-001")
                        .createdBy(1L)
                        .build();

        when(
                preConsultationRepository.findById(13L)
        ).thenReturn(Optional.of(preConsultation));

        when(
                medicalRecordRepository.findById(23L)
        ).thenReturn(Optional.of(record));

        when(
                symptomRepository.findByRecordId(23L)
        ).thenReturn(List.of());

        BusinessException exception =
                assertThrows(
                        BusinessException.class,
                        () -> service.analyzeAndPersist(
                                13L,
                                1L,
                                List.of("PATIENT")
                        )
                );

        assertEquals(
                "NO_SYMPTOMS",
                exception.getErrorCode()
        );

        verify(
                aiTriageClient,
                never()
        ).analyze(any(), any());
    }
}