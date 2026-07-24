# 预问诊业务时序图

```mermaid
sequenceDiagram
    actor Patient as 患者
    participant FE as 前端
    participant BE as 后端 [PR #10]
    participant AI as AI 服务
    participant RE as 规则引擎
    participant RAG as RAG 检索
    participant DB as 数据库
    participant Doctor as 医务人员

    Patient->>FE: 填报症状信息
    FE->>BE: 提交业务数据 [PR #10 待审核]
    BE->>DB: 保存业务记录
    BE-->>FE: 返回记录 ID

    BE->>AI: POST /api/v1/preconsultation/review

    rect rgb(240, 248, 255)
        Note over AI, RE: 多 Agent Pipeline
        AI->>AI: IntakeAgent 输入校验 + PII 脱敏
        AI->>RAG: RetrievalAgent 知识检索
        RAG->>DB: 语义搜索 pgvector
        DB-->>RAG: 相关知识块
        RAG-->>AI: 检索结果 + 证据
        AI->>RE: RiskAssessmentAgent 规则匹配
        RE-->>AI: 规则结果 风险等级 + 红旗标识
        AI->>AI: SafetyReviewAgent 输出安全审核
        Note over AI: 确定性诊断拦截 / 药物处方拦截 / 风险降级阻止
    end

    AI-->>BE: 审核结果
    BE->>DB: 保存审核结果
    BE-->>FE: 返回完整结果

    FE->>Doctor: 通知待审核 [所有风险等级]
    Doctor->>FE: 审核决策 确认/调整/驳回/升级
    FE->>BE: 提交审核结果 [PR #10 待审核]
    BE->>DB: 更新审核状态
    BE-->>FE: 确认
    FE-->>Patient: 显示审核结果
```

## 说明

- **调用链**：患者 -> 前端 -> 后端保存业务数据 -> 后端调用 AI -> AI 执行规则/RAG/多 Agent -> 后端保存结果 -> 医务人员审核
- **所有风险等级均进入医务人员审核**，HIGH/CRITICAL 为强制优先审核
- **不使用虚构接口路径**：后端接口用逻辑名称标注，注明"PR #10 待审核"
- **AI 已实现接口**：`POST /api/v1/preconsultation/review`
- **数据库操作**：pgvector 用于知识检索，业务数据保存待 PR #10 后端实现
