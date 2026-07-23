CREATE TABLE IF NOT EXISTS medical_records (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    patient_id      BIGINT          NOT NULL,
    case_code       VARCHAR(50)     NOT NULL,
    chief_complaint VARCHAR(500)    NULL,
    present_illness TEXT            NULL,
    past_history    TEXT            NULL,
    allergy_history TEXT            NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'ACTIVE',
    created_by      BIGINT          NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uk_medical_records_case_code UNIQUE (case_code),
    CONSTRAINT fk_medical_records_patient FOREIGN KEY (patient_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_medical_records_creator FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT,
    INDEX idx_medical_records_patient_id (patient_id),
    INDEX idx_medical_records_status (status),
    INDEX idx_medical_records_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS symptoms (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    record_id       BIGINT          NOT NULL,
    symptom_name    VARCHAR(200)    NOT NULL,
    body_part       VARCHAR(100)    NULL,
    severity        VARCHAR(20)     NOT NULL DEFAULT 'MODERATE',
    duration_desc   VARCHAR(200)    NULL,
    onset_time      DATETIME        NULL,
    notes           TEXT            NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_symptoms_record FOREIGN KEY (record_id) REFERENCES medical_records (id) ON DELETE CASCADE,
    INDEX idx_symptoms_record_id (record_id),
    INDEX idx_symptoms_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pre_consultations (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    record_id       BIGINT          NOT NULL,
    patient_id      BIGINT          NOT NULL,
    status          VARCHAR(30)     NOT NULL DEFAULT 'INITIATED',
    initiated_by    BIGINT          NOT NULL,
    reviewed_by     BIGINT          NULL,
    review_comment  TEXT            NULL,
    reviewed_at     DATETIME        NULL,
    completed_at    DATETIME        NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_pre_consultations_record FOREIGN KEY (record_id) REFERENCES medical_records (id) ON DELETE CASCADE,
    CONSTRAINT fk_pre_consultations_patient FOREIGN KEY (patient_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_pre_consultations_initiator FOREIGN KEY (initiated_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_pre_consultations_reviewer FOREIGN KEY (reviewed_by) REFERENCES users (id) ON DELETE SET NULL,
    INDEX idx_pre_consultations_record_id (record_id),
    INDEX idx_pre_consultations_patient_id (patient_id),
    INDEX idx_pre_consultations_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS triage_results (
    id                      BIGINT          NOT NULL AUTO_INCREMENT,
    pre_consultation_id     BIGINT          NOT NULL,
    urgency_level           VARCHAR(20)     NOT NULL DEFAULT 'ROUTINE',
    suggested_department    VARCHAR(100)    NULL,
    risk_flags              JSON            NULL,
    reasoning_summary       TEXT            NULL,
    reference_sources       JSON            NULL,
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_triage_results_pre_consultation FOREIGN KEY (pre_consultation_id) REFERENCES pre_consultations (id) ON DELETE CASCADE,
    INDEX idx_triage_results_pre_consultation_id (pre_consultation_id),
    INDEX idx_triage_results_urgency_level (urgency_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS agent_execution_logs (
    id                      BIGINT          NOT NULL AUTO_INCREMENT,
    pre_consultation_id     BIGINT          NOT NULL,
    agent_type              VARCHAR(50)     NOT NULL,
    input_summary           TEXT            NULL,
    output_summary          TEXT            NULL,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'RUNNING',
    error_message           TEXT            NULL,
    started_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at            DATETIME        NULL,
    duration_ms             BIGINT          NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_agent_logs_pre_consultation FOREIGN KEY (pre_consultation_id) REFERENCES pre_consultations (id) ON DELETE CASCADE,
    INDEX idx_agent_logs_pre_consultation_id (pre_consultation_id),
    INDEX idx_agent_logs_agent_type (agent_type),
    INDEX idx_agent_logs_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS audit_logs (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    user_id         BIGINT          NULL,
    username        VARCHAR(50)     NULL,
    action          VARCHAR(50)     NOT NULL,
    resource_type   VARCHAR(50)     NOT NULL,
    resource_id     BIGINT          NULL,
    detail          TEXT            NULL,
    ip_address      VARCHAR(45)     NULL,
    trace_id        VARCHAR(36)     NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_audit_logs_user_id (user_id),
    INDEX idx_audit_logs_action (action),
    INDEX idx_audit_logs_resource_type (resource_type),
    INDEX idx_audit_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;