# 数据库 ER 图

本图分为三个部分：

1. **PR #10 当前拟合并物理模型** — 待 PR #10 审核合并，字段以 PR #10 Entity 为准
2. **AI pgvector 已实现模型** — ai-service 中 migrations/001_pgvector.sql 定义的知识库表
3. **后续设计目标模型** — 尚未实现，以注释形式保留

> **注意**：PR #10 当前物理模型标注为待审核合并，最终以合并版本为准。

## PR #10 当前拟合并物理模型

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : has
    USERS ||--o{ MEDICAL_RECORDS : creates
    MEDICAL_RECORDS ||--o{ SYMPTOMS : contains
    MEDICAL_RECORDS ||--o{ PRE_CONSULTATIONS : generates
    PRE_CONSULTATIONS ||--o| TRIAGE_RESULTS : produces
    PRE_CONSULTATIONS ||--o{ AGENT_EXECUTION_LOGS : tracks
    PRE_CONSULTATIONS ||--o{ FOLLOWUP_TASKS : triggers
    USERS ||--o{ AUDIT_LOGS : generates

    USERS {
        bigint id PK
        varchar username UK
        varchar password_hash
        varchar display_name
        varchar case_code
        varchar status
        timestamp created_at
        timestamp updated_at
    }

    ROLES {
        bigint id PK
        varchar name UK
        varchar description
    }

    USER_ROLES {
        bigint user_id FK
        bigint role_id FK
    }

    MEDICAL_RECORDS {
        bigint id PK
        bigint patient_id FK
        varchar case_code
        varchar chief_complaint
        text present_illness
        text past_history
        text allergy_history
        varchar status
        bigint created_by FK
        timestamp created_at
        timestamp updated_at
    }

    SYMPTOMS {
        bigint id PK
        bigint record_id FK
        varchar symptom_name
        varchar body_part
        int severity
        varchar duration_desc
        varchar onset_time
        text notes
        timestamp created_at
        timestamp updated_at
    }

    PRE_CONSULTATIONS {
        bigint id PK
        bigint record_id FK
        bigint patient_id FK
        varchar status
        bigint initiated_by FK
        bigint reviewed_by FK
        text review_comment
        timestamp reviewed_at
        timestamp completed_at
        timestamp created_at
        timestamp updated_at
    }

    TRIAGE_RESULTS {
        bigint id PK
        bigint pre_consultation_id FK
        varchar urgency_level
        varchar suggested_department
        json risk_flags
        text reasoning_summary
        json reference_sources
        timestamp created_at
        timestamp updated_at
    }

    AGENT_EXECUTION_LOGS {
        bigint id PK
        bigint pre_consultation_id FK
        varchar agent_type
        text input_summary
        text output_summary
        varchar status
        text error_message
        timestamp started_at
        timestamp completed_at
        int duration_ms
    }

    AUDIT_LOGS {
        bigint id PK
        bigint user_id FK
        varchar username
        varchar action
        varchar resource_type
        varchar resource_id
        text detail
        varchar ip_address
        varchar trace_id
        timestamp created_at
    }

    FOLLOWUP_TASKS {
        bigint id PK
        bigint pre_consultation_id FK
        bigint assigned_to FK
        bigint assigned_by FK
        varchar task_type
        text description
        varchar status
        timestamp completed_at
        text notes
        timestamp created_at
        timestamp updated_at
    }
```

## AI pgvector 已实现模型

```mermaid
erDiagram
    KNOWLEDGE_DOCUMENTS ||--o{ KNOWLEDGE_CHUNKS : contains

    KNOWLEDGE_DOCUMENTS {
        varchar document_id PK
        varchar title
        varchar publisher
        varchar source_url
        varchar document_version
        timestamp published_at
        varchar checksum UK
        int chunk_count
        timestamp created_at
    }

    KNOWLEDGE_CHUNKS {
        varchar chunk_id PK
        varchar document_id FK
        int chunk_index
        text content
        varchar title
        varchar publisher
        varchar source_url
        varchar document_version
        timestamp published_at
        varchar checksum
        vector embedding
        timestamp created_at
    }
```

## 后续设计目标模型（尚未实现）

以下表为设计目标，尚未在任何代码中实现：

- **SIMULATED_PATIENTS** — 合成患者档案管理（独立于 MEDICAL_RECORDS）
- **VISITS** — 就诊记录管理
- **AGENT_RUNS** — Agent 执行记录（独立于 AGENT_EXECUTION_LOGS 的扩展设计）
- **CITATIONS** — 知识引用记录（独立关联检索结果）
- **FOLLOWUP_PLANS** — 随访计划管理（FOLLOWUP_TASKS 的上层计划实体）

> 这些表的具体字段和关联关系需在后续开发中根据实际需求确定。
