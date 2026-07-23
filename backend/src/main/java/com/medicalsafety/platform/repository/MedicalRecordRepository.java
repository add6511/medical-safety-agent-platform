package com.medicalsafety.platform.repository;

import com.medicalsafety.platform.entity.MedicalRecord;
import com.medicalsafety.platform.enums.MedicalRecordStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface MedicalRecordRepository extends JpaRepository<MedicalRecord, Long> {

    Optional<MedicalRecord> findByCaseCode(String caseCode);

    List<MedicalRecord> findByPatientId(Long patientId);

    List<MedicalRecord> findByPatientIdAndStatus(Long patientId, MedicalRecordStatus status);

    boolean existsByCaseCode(String caseCode);
}