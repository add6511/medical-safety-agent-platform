package com.medicalsafety.platform.repository;

import com.medicalsafety.platform.entity.Symptom;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SymptomRepository extends JpaRepository<Symptom, Long> {

    List<Symptom> findByRecordId(Long recordId);

    void deleteByRecordId(Long recordId);
}