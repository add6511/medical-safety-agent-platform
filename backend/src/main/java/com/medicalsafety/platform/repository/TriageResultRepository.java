package com.medicalsafety.platform.repository;

import com.medicalsafety.platform.entity.TriageResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface TriageResultRepository extends JpaRepository<TriageResult, Long> {

    Optional<TriageResult> findByPreConsultationId(Long preConsultationId);

    void deleteByPreConsultationId(Long preConsultationId);
}