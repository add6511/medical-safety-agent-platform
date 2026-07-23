package com.medicalsafety.platform.repository;

import com.medicalsafety.platform.entity.AgentExecutionLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AgentExecutionLogRepository extends JpaRepository<AgentExecutionLog, Long> {

    List<AgentExecutionLog> findByPreConsultationId(Long preConsultationId);

    List<AgentExecutionLog> findByPreConsultationIdAndStatus(Long preConsultationId, com.medicalsafety.platform.enums.AgentExecutionStatus status);
}