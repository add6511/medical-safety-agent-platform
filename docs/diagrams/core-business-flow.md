# 核心业务流程图

```mermaid
flowchart TD
    A["患者填报症状"] --> B["信息脱敏\nPII 自动检测与替换"]
    B --> C["症状结构化\n提取关键信息"]
    C --> D["红旗规则预筛\n规则引擎匹配"]
    D --> E{"是否触发红旗?"}
    E -->|"是"| F["标记 HIGH/CRITICAL 风险"]
    E -->|"否"| G["继续评估"]
    F --> H["医疗 RAG 检索\n相关指南与证据"]
    G --> H
    H --> I["多 Agent 风险复核\nIntakeAgent -> RetrievalAgent\n-> RiskAssessmentAgent\n-> SafetyReviewAgent"]
    I --> J["安全审核\n确定性诊断拦截\n药物处方拦截\n风险降级阻止"]
    J --> K["生成审核报告\n风险等级/证据/建议"]
    K --> L["进入医务人员审核"]
    L --> M{"风险等级?"}
    M -->|"HIGH/CRITICAL"| N["强制优先审核\n必须处理"]
    M -->|"LOW/MEDIUM"| O["常规审核\n确认/调整"]
    N --> P["医务人员审核决策\n确认/调整/驳回/升级"]
    O --> P
    P --> Q["随访计划\n设计目标"]
    Q --> R["结果归档\n审计日志记录"]

    style F fill:#ff6b6b,color:#fff
    style N fill:#ff6b6b,color:#fff
    style Q fill:#868e96,color:#fff,stroke-dasharray: 5 5
    style R fill:#868e96,color:#fff,stroke-dasharray: 5 5
```

## 说明

- **所有 AI 结果均进入医务人员审核**，不跳过人工审核环节
- **HIGH/CRITICAL** 风险标记为强制优先审核，必须处理
- **LOW/MEDIUM** 风险为常规审核，同样必须经过审核
- **随访计划**和**结果归档**标记为设计目标（虚线样式）
- **红旗规则预筛**由确定性规则引擎执行，不依赖 AI 模型
- **风险降级阻止**：HIGH/CRITICAL 风险不允许被模型下调
