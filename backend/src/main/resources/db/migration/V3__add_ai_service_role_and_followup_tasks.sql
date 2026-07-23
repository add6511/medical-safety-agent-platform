INSERT IGNORE INTO roles (name, description) VALUES ('AI_SERVICE', 'AI服务');

ALTER TABLE pre_consultations ADD COLUMN version BIGINT NULL DEFAULT 0;

ALTER TABLE triage_results ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE triage_results ADD CONSTRAINT uk_triage_results_pre_consultation UNIQUE (pre_consultation_id);

CREATE TABLE IF NOT EXISTS followup_tasks (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    pre_consultation_id BIGINT      NOT NULL,
    assigned_to     BIGINT          NOT NULL,
    assigned_by     BIGINT          NOT NULL,
    task_type       VARCHAR(50)     NOT NULL,
    description     TEXT            NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'PENDING',
    completed_at    DATETIME        NULL,
    notes           TEXT            NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_followup_tasks_pre_consultation FOREIGN KEY (pre_consultation_id) REFERENCES pre_consultations (id) ON DELETE CASCADE,
    CONSTRAINT fk_followup_tasks_assignee FOREIGN KEY (assigned_to) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_followup_tasks_assigner FOREIGN KEY (assigned_by) REFERENCES users (id) ON DELETE RESTRICT,
    INDEX idx_followup_tasks_assigned_to (assigned_to),
    INDEX idx_followup_tasks_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;