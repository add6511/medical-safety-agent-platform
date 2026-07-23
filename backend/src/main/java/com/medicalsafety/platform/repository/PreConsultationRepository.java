package com.medicalsafety.platform.repository;

import com.medicalsafety.platform.entity.PreConsultation;
import com.medicalsafety.platform.enums.PreConsultationStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PreConsultationRepository extends JpaRepository<PreConsultation, Long> {

    List<PreConsultation> findByRecordId(Long recordId);

    List<PreConsultation> findByPatientId(Long patientId);

    List<PreConsultation> findByStatus(PreConsultationStatus status);

    Optional<PreConsultation> findByIdAndPatientId(Long id, Long patientId);
}