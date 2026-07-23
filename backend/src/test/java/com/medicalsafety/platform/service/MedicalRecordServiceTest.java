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
import com.medicalsafety.platform.security.RequestContextHelper;
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

    @Mock private MedicalRecordRepository medicalRecordRepository;
    @Mock private SymptomRepository symptomRepository;
    @Mock private AuditLogService auditLogService;
    @Mock private RequestContextHelper requestContextHelper;
    @InjectMocks private MedicalRecordService medicalRecordService;

    private MedicalRecord testRecord;
    private static final List<String> ADMIN_ROLES = List.of("ADMIN");
    private static final List<String> PATIENT_ROLES = List.of("PATIENT");

    @BeforeEach
    void setUp() {
        testRecord = MedicalRecord.builder().id(1L).patientId(100L).caseCode("CASE-001")
                .chiefComplaint("头痛").status(MedicalRecordStatus.ACTIVE).createdBy(100L).build();
    }

    @Test
    void createRecordSuccess() {
        when(medicalRecordRepository.existsByCaseCode("CASE-001")).thenReturn(false);
        when(medicalRecordRepository.save(any(MedicalRecord.class))).thenReturn(testRecord);
        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder().patientId(100L).caseCode("CASE-001").chiefComplaint("头痛").build();
        MedicalRecordResponse response = medicalRecordService.createRecord(request, 100L, PATIENT_ROLES);
        assertEquals("CASE-001", response.getCaseCode());
        verify(auditLogService).log(eq(100L), isNull(), eq("CREATE"), eq("MEDICAL_RECORD"), any(), any(), isNull(), isNull());
    }

    @Test
    void createRecordDuplicateCaseCodeThrows() {
        when(medicalRecordRepository.existsByCaseCode("CASE-001")).thenReturn(true);
        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder().patientId(100L).caseCode("CASE-001").build();
        assertThrows(BusinessException.class, () -> medicalRecordService.createRecord(request, 100L, PATIENT_ROLES));
    }

    @Test
    void patientCannotCreateRecordForOtherPatient() {
        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder().patientId(999L).caseCode("CASE-002").build();
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> medicalRecordService.createRecord(request, 100L, PATIENT_ROLES));
    }

    @Test
    void staffCanCreateRecordForAnyPatient() {
        when(medicalRecordRepository.existsByCaseCode("CASE-002")).thenReturn(false);
        MedicalRecord rec = MedicalRecord.builder().id(2L).patientId(999L).caseCode("CASE-002").status(MedicalRecordStatus.ACTIVE).createdBy(1L).build();
        when(medicalRecordRepository.save(any(MedicalRecord.class))).thenReturn(rec);
        CreateMedicalRecordRequest request = CreateMedicalRecordRequest.builder().patientId(999L).caseCode("CASE-002").build();
        assertDoesNotThrow(() -> medicalRecordService.createRecord(request, 1L, ADMIN_ROLES));
    }

    @Test
    void getRecordSuccess() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        when(symptomRepository.findByRecordId(1L)).thenReturn(List.of());
        assertEquals("CASE-001", medicalRecordService.getRecord(1L, 100L, PATIENT_ROLES).getCaseCode());
    }

    @Test
    void patientCannotReadOtherPatientRecord() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> medicalRecordService.getRecord(1L, 999L, PATIENT_ROLES));
    }

    @Test
    void staffCanReadAnyRecord() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        when(symptomRepository.findByRecordId(1L)).thenReturn(List.of());
        assertDoesNotThrow(() -> medicalRecordService.getRecord(1L, 1L, ADMIN_ROLES));
    }

    @Test
    void archiveRecordSuccess() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        when(medicalRecordRepository.save(any(MedicalRecord.class))).thenAnswer(inv -> inv.getArgument(0));
        when(symptomRepository.findByRecordId(1L)).thenReturn(List.of());
        assertEquals("ARCHIVED", medicalRecordService.archiveRecord(1L, 100L, PATIENT_ROLES).getStatus());
    }

    @Test
    void patientCannotArchiveOtherPatientRecord() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> medicalRecordService.archiveRecord(1L, 999L, PATIENT_ROLES));
    }

    @Test
    void addSymptomSuccess() {
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        Symptom symptom = Symptom.builder().id(1L).recordId(1L).symptomName("头痛").severity(SymptomSeverity.MODERATE).build();
        when(symptomRepository.save(any(Symptom.class))).thenReturn(symptom);
        CreateSymptomRequest request = CreateSymptomRequest.builder().recordId(1L).symptomName("头痛").severity("MODERATE").build();
        assertEquals("头痛", medicalRecordService.addSymptom(request, 100L, PATIENT_ROLES).getSymptomName());
    }

    @Test
    void deleteSymptomSuccess() {
        Symptom symptom = Symptom.builder().id(1L).recordId(1L).symptomName("头痛").severity(SymptomSeverity.MODERATE).build();
        when(symptomRepository.findById(1L)).thenReturn(Optional.of(symptom));
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        medicalRecordService.deleteSymptom(1L, 100L, PATIENT_ROLES);
        verify(symptomRepository).delete(symptom);
    }

    @Test
    void patientCannotDeleteOtherPatientSymptom() {
        Symptom symptom = Symptom.builder().id(1L).recordId(1L).symptomName("头痛").severity(SymptomSeverity.MODERATE).build();
        when(symptomRepository.findById(1L)).thenReturn(Optional.of(symptom));
        when(medicalRecordRepository.findById(1L)).thenReturn(Optional.of(testRecord));
        assertThrows(com.medicalsafety.platform.exception.AccessDeniedException.class,
                () -> medicalRecordService.deleteSymptom(1L, 999L, PATIENT_ROLES));
    }
}
