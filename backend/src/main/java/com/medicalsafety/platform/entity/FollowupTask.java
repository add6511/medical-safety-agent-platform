package com.medicalsafety.platform.entity;

import com.medicalsafety.platform.enums.FollowupTaskStatus;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "followup_tasks")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FollowupTask {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "pre_consultation_id", nullable = false)
    private Long preConsultationId;

    @Column(name = "assigned_to", nullable = false)
    private Long assignedTo;

    @Column(name = "assigned_by", nullable = false)
    private Long assignedBy;

    @Column(name = "task_type", nullable = false, length = 50)
    private String taskType;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private FollowupTaskStatus status;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
        if (this.status == null) {
            this.status = FollowupTaskStatus.PENDING;
        }
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}