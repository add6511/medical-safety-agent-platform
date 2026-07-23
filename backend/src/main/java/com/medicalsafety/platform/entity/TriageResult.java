package com.medicalsafety.platform.entity;

import com.medicalsafety.platform.enums.UrgencyLevel;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "triage_results")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TriageResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "pre_consultation_id", nullable = false, unique = true)
    private Long preConsultationId;

    @Enumerated(EnumType.STRING)
    @Column(name = "urgency_level", nullable = false, length = 20)
    private UrgencyLevel urgencyLevel;

    @Column(name = "suggested_department", length = 100)
    private String suggestedDepartment;

    @Column(name = "risk_flags", columnDefinition = "JSON")
    private String riskFlags;

    @Column(name = "reasoning_summary", columnDefinition = "TEXT")
    private String reasoningSummary;

    @Column(name = "reference_sources", columnDefinition = "JSON")
    private String referenceSources;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
        if (this.urgencyLevel == null) {
            this.urgencyLevel = UrgencyLevel.ROUTINE;
        }
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
