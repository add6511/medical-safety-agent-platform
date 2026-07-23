package com.medicalsafety.platform.service;

import com.medicalsafety.platform.dto.*;
import com.medicalsafety.platform.entity.MedicalRecord;
import com.medicalsafety.platform.entity.Symptom;
import com.medicalsafety.platform.enums.MedicalRecordStatus;
import com.medicalsafety.platform.enums.SymptomSeverity;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.MedicalRecordRepository;
import com.medicalsafety.platform.repository.SymptomRepository;
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
class MedicalRecordServiceTest {

    @Mock
    private MedicalRecordRepository medicalRecordRepository;

    @Mock
    private SymptomRepository symptomRepository;

    @Mock
    private AuditLogService auditLogService;

    @InjectMocks
    private MedicalRecordService medicalRecordService;

    private MedicalRecord testRecord;

    @BeforeEach
    void setUp() {
        medicalRecordService.setAuditLogService(auditLogService);

        testRecord = MedicalRecord.builder()
                .id(1L)
                .patientId(100L)
                .caseCode("CASE-001")
                .chiefComplaint("头痛")
                .presentIllness("持续3天")
                .status(MedicalRecordStatus.ACTIVE)
                .createdBy(1L)
                .build();
    }

    @Test
    void createRecordSuccess() {
        when(medicalRecordRepository.existsByCaseCode("CASE-001")).thenReturn(false);
        when(medicalRecordRepository.save(any(MedicalRecord.class))).thenReturn(testRecord);

        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder()
                .patientId(100L)
                .caseCode("CASE-001")
                .chiefComplaint("头痛")
                .build();

        MedicalRecordResponse response = medicalRecordService.createRecord(request, 1L);

        assertNotNull(response);
        assertEquals("CASE-001", response.getCaseCode());
        assertEquals("头痛", response.getChiefComplaint());
        verify(medicalRecordRepository).save(any(MedicalRecord.class));
    }

    @Test
    void createRecordDuplicateCaseCodeThrows() {
        when(medicalRecordRepository.existsByCaseCode("CASE-001")).thenReturn(true);

        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder()
                .patientId(100L)
                .caseCode("CASE-001")
                .build();

        assertThrows(BusinessException.class, () -> medicalRecordService.createRecord(request, 1L));
    }

    @Test
    void getRecordSuccess() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        when(symptomRepository.findByRecordId(1L)).thenReturn(List.of());

        MedicalRecordResponse response = medicalRecordService.getRecord(1L);

        assertNotNull(response);
        assertEquals(1L, response.getId());
        assertEquals("CASE-001", response.getCaseCode());
    }

    @Test
    void getRecordNotFoundThrows() {
        when(medicalRecordRepository.findById(999L)).thenReturn(Optional.empty());

        assertThrows(ResourceNotFoundException.class, () -> medicalRecordService.getRecord(999L));
    }

    @Test
    void getRecordByCaseCodeSuccess() {
        when(medicalRecordRepository.findByCaseCode("CASE-001")).thenReturn(Optional.of(testRecord));
        when(symptomRepository.findByRecordId(1L)).thenReturn(List.of());

        MedicalRecordResponse response = medicalRecordService.getRecordByCaseCode("CASE-001");

        assertNotNull(response);
        assertEquals("CASE-001", response.getCaseCode());
    }

    @Test
    void archiveRecordSuccess() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        when(medicalRecordRepository.save(any(MedicalRecord.class))).thenAnswer(inv -> inv.getArgument(0));
        when(symptomRepository.findByRecordId(1L)).thenReturn(List.of());

        MedicalRecordResponse response = medicalRecordService.archiveRecord(1L, 1L);

        assertEquals("ARCHIVED", response.getStatus());
    }

    @Test
    void addSymptomSuccess() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));

        Symptom symptom = Symptom.builder()
                .id(1L)
                .recordId(1L)
                .symptomName("头痛")
                .severity(SymptomSeverity.MODERATE)
                .build();
        when(symptomRepository.save(any(Symptom.class))).thenReturn(symptom);

        CreateSymptomRequest request = CreateSymptomRequest.builder()
                .recordId(1L)
                .symptomName("头痛")
                .severity("MODERATE")
                .build();

        SymptomResponse response = medicalRecordService.addSymptom(request, 1L);

        assertNotNull(response);
        assertEquals("头痛", response.getSymptomName());
        assertEquals("MODERATE", response.getSeverity());
    }

    @Test
    void addSymptomInvalidSeverityThrows() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));

        CreateSymptomRequest request = CreateSymptomRequest.builder()
                .recordId(1L)
                .symptomName("头痛")
                .severity("INVALID")
                .build();

        assertThrows(BusinessException.class, () -> medicalRecordService.addSymptom(request, 1L));
    }

    @Test
    void getSymptomsByRecord() {
        Symptom s1 = Symptom.builder().id(1L).recordId(1L).symptomName("头痛").severity(SymptomSeverity.MODERATE).build();
        Symptom s2 = Symptom.builder().id(2L).recordId(1L).symptomName("发热").severity(SymptomSeverity.MILD).build();
        when(symptomRepository.findByRecordId(1L)).thenReturn(List.of(s1, s2));

        List<SymptomResponse> symptoms = medicalRecordService.getSymptomsByRecord(1L);

        assertEquals(2, symptoms.size());
    }

    @Test
    void deleteSymptomSuccess() {
        Symptom symptom = Symptom.builder().id(1L).recordId(1L).symptomName("头痛").severity(SymptomSeverity.MODERATE).build();
        when(symptomRepository.findById(1L)).thenReturn(Optional.of(symptom));

        medicalRecordService.deleteSymptom(1L, 1L);

        verify(symptomRepository).delete(symptom);
    }
}