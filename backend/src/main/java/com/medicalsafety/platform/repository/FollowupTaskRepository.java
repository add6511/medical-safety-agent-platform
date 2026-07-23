package com.medicalsafety.platform.repository;

import com.medicalsafety.platform.entity.FollowupTask;
import com.medicalsafety.platform.enums.FollowupTaskStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface FollowupTaskRepository extends JpaRepository<FollowupTask, Long> {

    List<FollowupTask> findByAssignedTo(Long assignedTo);

    List<FollowupTask> findByAssignedToAndStatus(Long assignedTo, FollowupTaskStatus status);

    List<FollowupTask> findByPreConsultationId(Long preConsultationId);
}