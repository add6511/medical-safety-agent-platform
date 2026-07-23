# 基层医疗安全型预问诊AI服务 — API 接口契约

> **安全声明**：本服务仅供教学演示，所有示例均为合成教学数据，不构成真实诊断或治疗建议。

---

## 1. 概述

基层医疗安全型预问诊AI服务是一个面向教学演示场景的安全预问诊审核系统。本服务通过多Agent协作流程（输入校验 → 知识检索 → 风险评估 → 安全审核）对合成教学病例进行安全审核，并返回风险评估结果和相关知识引用。

**重要声明**：
- 本服务仅用于教学目的，所有病例数据均为合成生成
- 不提供真实医疗诊断，不替代医生专业判断
- 知识库内容仅供教学参考，不构成诊断或治疗建议

---

## 2. 通用约定

### 2.1 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://localhost:8000` |
| Content-Type | `application/json` |
| 字符编码 | UTF-8 |
| API 版本 | v1 |
| 协议 | HTTP/1.1 |

### 2.2 错误响应结构

所有错误响应均遵循以下统一结构：

```json
{
  "detail": "错误描述信息"
}
```

### 2.3 请求头规范

| 请求头 | 是否必须 | 说明 |
|--------|----------|------|
| Content-Type | 是 | 必须为 `application/json` |
| Accept | 否 | 建议为 `application/json` |
| X-Request-ID | 否 | 请求追踪标识，用于链路追踪 |

---

## 3. 接口列表

### 3.1 健康检查

#### `GET /health`

服务存活检测接口，用于监控系统健康状态。

**请求示例**

```http
GET /health HTTP/1.1
Host: localhost:8000
```

**响应示例**

```json
{
  "status": "ok",
  "service": "medical-safety-ai-service",
  "version": "0.1.0",
  "environment": "development"
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 服务状态，正常时为 `"ok"` |
| service | string | 服务名称标识 |
| version | string | 服务版本号 |
| environment | string | 运行环境（development/production） |

**状态码**

| 状态码 | 说明 |
|--------|------|
| 200 | 服务正常 |

---

### 3.2 导入知识文档

#### `POST /api/v1/knowledge/documents`

导入教学用指南文本到知识库。内容必须为合成教学材料，不接受真实患者数据。

**请求示例**

```json
{
  "title": "高血压基层诊疗指南（教学版）",
  "publisher": "中华医学会（示例）",
  "source_url": "https://example.org/guidelines/hypertension",
  "document_version": "2024教学版",
  "published_at": "2024-01-15T00:00:00Z",
  "content": "高血压定义为在未使用降压药物的情况下，非同日3次诊室血压测量..."
}
```

**请求字段说明**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| title | string | 是 | 1-500字符 | 文档标题 |
| publisher | string | 是 | 1-200字符 | 发布机构 |
| source_url | string | 是 | 1-2000字符，必须以 `http://` 或 `https://` 开头 | 来源链接 |
| document_version | string | 是 | 1-50字符 | 文档版本 |
| published_at | datetime | 否 | ISO 8601格式 | 发布时间 |
| content | string | 是 | 1-500000字符，不可为空白 | 文档正文内容 |

**响应示例**

```json
{
  "document_id": "doc_abc123def456",
  "checksum": "sha256:a1b2c3d4e5f6...",
  "chunk_count": 5,
  "duplicate": false
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| document_id | string | 文档唯一标识 |
| checksum | string | 文档 SHA-256 校验值 |
| chunk_count | int | 切分后的知识块数量 |
| duplicate | bool | 是否为重复导入（相同校验值） |

**状态码**

| 状态码 | 说明 |
|--------|------|
| 200 | 导入成功 |
| 422 | 请求参数校验失败 |
| 503 | 知识库服务未初始化 |

**错误场景**

| 错误信息 | 原因 |
|----------|------|
| `文档内容不能为空或纯空白` | content 字段为空或纯空白 |
| `source_url 必须以 http:// 或 https:// 开头` | URL格式不正确 |
| `知识库服务未初始化` | 服务启动时初始化失败 |

**幂等性说明**

相同校验值的文档重复导入时保持幂等，不重复创建数据，返回已存在的文档信息。

---

### 3.3 查询文档列表

#### `GET /api/v1/knowledge/documents`

返回已导入的文档列表，不包含文档正文。

**请求示例**

```http
GET /api/v1/knowledge/documents HTTP/1.1
Host: localhost:8000
```

**响应示例**

```json
{
  "total": 2,
  "documents": [
    {
      "document_id": "doc_abc123def456",
      "title": "高血压基层诊疗指南（教学版）",
      "publisher": "中华医学会（示例）",
      "source_url": "https://example.org/guidelines/hypertension",
      "document_version": "2024教学版",
      "published_at": "2024-01-15T00:00:00Z",
      "checksum": "sha256:a1b2c3d4e5f6...",
      "chunk_count": 5,
      "created_at": "2024-01-20T10:30:00Z"
    }
  ]
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| total | int | 文档总数 |
| documents | array | 文档列表 |
| documents[].document_id | string | 文档唯一标识 |
| documents[].title | string | 文档标题 |
| documents[].publisher | string | 发布机构 |
| documents[].source_url | string | 来源链接 |
| documents[].document_version | string | 文档版本 |
| documents[].published_at | datetime | 发布时间 |
| documents[].checksum | string | 文档校验值 |
| documents[].chunk_count | int | 知识块数量 |
| documents[].created_at | datetime | 导入时间 |

**状态码**

| 状态码 | 说明 |
|--------|------|
| 200 | 查询成功 |
| 503 | 知识库服务未初始化 |

---

### 3.4 知识检索

#### `POST /api/v1/knowledge/search`

根据查询文本检索相关知识片段。检索结果只返回知识片段和来源，不生成诊断结论。

**请求示例**

```json
{
  "query": "高血压的诊断标准是什么",
  "top_k": 5
}
```

**请求字段说明**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| query | string | 是 | 1-1000字符，不可为空白 | 检索查询文本 |
| top_k | int | 否 | 1-10，默认为5 | 返回结果数量 |

**响应示例**

```json
{
  "query": "高血压的诊断标准是什么",
  "top_k": 5,
  "results": [
    {
      "chunk_id": "chunk_001",
      "document_id": "doc_abc123def456",
      "title": "高血压基层诊疗指南（教学版）",
      "content": "高血压定义为在未使用降压药物的情况下，非同日3次诊室血压测量...",
      "score": 0.89,
      "publisher": "中华医学会（示例）",
      "source_url": "https://example.org/guidelines/hypertension",
      "document_version": "2024教学版",
      "chunk_index": 0
    }
  ],
  "disclaimer": "检索结果仅供教学参考，不构成诊断或治疗建议。"
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| query | string | 原始查询 |
| top_k | int | 请求返回数量 |
| results | array | 检索结果列表 |
| results[].chunk_id | string | 知识块唯一标识 |
| results[].document_id | string | 所属文档标识 |
| results[].title | string | 文档标题 |
| results[].content | string | 知识块内容 |
| results[].score | float | 相似度得分（0-1） |
| results[].publisher | string | 发布机构 |
| results[].source_url | string | 来源链接 |
| results[].document_version | string | 文档版本 |
| results[].chunk_index | int | 块在文档中的序号 |
| disclaimer | string | 安全声明 |

**状态码**

| 状态码 | 说明 |
|--------|------|
| 200 | 检索成功 |
| 422 | 请求参数校验失败 |
| 503 | 知识库服务未初始化 |

---

### 3.5 删除文档

#### `DELETE /api/v1/knowledge/documents/{document_id}`

删除指定文档及其关联的所有知识块。

**请求示例**

```http
DELETE /api/v1/knowledge/documents/doc_abc123def456 HTTP/1.1
Host: localhost:8000
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| document_id | string | 文档唯一标识 |

**响应示例**

```json
{
  "message": "文档已删除",
  "document_id": "doc_abc123def456"
}
```

**状态码**

| 状态码 | 说明 |
|--------|------|
| 200 | 删除成功 |
| 404 | 文档不存在 |
| 503 | 知识库服务未初始化 |

**错误场景**

| 错误信息 | 原因 |
|----------|------|
| `文档不存在: {document_id}` | 指定的文档ID不存在 |

---

### 3.6 预问诊安全审核

#### `POST /api/v1/preconsultation/review`

对合成教学病例进行多Agent安全审核流程。审核流程：输入校验 → 知识检索 → 风险评估 → 安全审核。

**安全声明**：本接口仅供教学演示，不提供真实诊断或替代医生。

**请求示例**

```json
{
  "case_id": "synthetic-case-001",
  "age": 45,
  "symptoms": [
    {
      "name": "胸部不适",
      "severity": 7,
      "duration": "30分钟"
    }
  ],
  "red_flags": ["persistent_chest_discomfort"],
  "free_text": "这是一个合成教学病例，患者主诉胸部不适。",
  "model_suggested_risk": "LOW"
}
```

**请求字段说明**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| case_id | string | 是 | 1-100字符 | 病例标识（合成教学用） |
| age | int | 否 | 0-150 | 年龄 |
| symptoms | array | 否 | - | 症状列表 |
| symptoms[].name | string | 是 | 1-200字符 | 症状名称 |
| symptoms[].severity | int | 否 | 0-10，默认为5 | 严重程度 |
| symptoms[].duration | string | 否 | 1-100字符 | 持续时间 |
| red_flags | array | 否 | - | 红旗标识列表 |
| free_text | string | 否 | 1-5000字符 | 自由文本描述（合成教学病例） |
| model_suggested_risk | string | 否 | LOW/MEDIUM/HIGH/CRITICAL | 模型建议的风险等级 |

**合法的红旗标识值**

| 标识值 | 说明 |
|--------|------|
| consciousness_change | 意识状态改变 |
| severe_breathing_difficulty | 严重呼吸困难 |
| persistent_chest_discomfort | 持续性胸部不适 |
| uncontrolled_bleeding | 无法控制的出血 |
| self_harm_risk | 自伤风险 |
| pregnancy_emergency_signal | 妊娠紧急信号 |

**响应示例**

```json
{
  "case_id": "synthetic-case-001",
  "final_risk_level": "HIGH",
  "rule_risk_level": "HIGH",
  "model_suggested_risk": "LOW",
  "model_downgrade_blocked": true,
  "needs_human_review": true,
  "matched_rules": [
    {
      "rule_id": "RULE-001",
      "name": "持续性胸部不适红旗规则",
      "risk_level": "HIGH",
      "display_message": "存在持续性胸部不适，需立即人工评估",
      "priority": 1
    }
  ],
  "retrieved_evidence": [
    {
      "chunk_id": "chunk_001",
      "document_id": "doc_abc123def456",
      "title": "高血压基层诊疗指南（教学版）",
      "content": "对于胸痛患者，应首先排除急性冠脉综合征...",
      "score": 0.85,
      "publisher": "中华医学会（示例）",
      "source_url": "https://example.org/guidelines/hypertension",
      "document_version": "2024教学版",
      "chunk_index": 2
    }
  ],
  "safety_flags": ["RED_FLAG_DETECTED", "HIGH_RISK_RULE_MATCHED"],
  "safe_summary": "合成教学病例摘要：患者存在持续性胸部不适红旗标识，规则引擎判定为高风险，需人工审核。",
  "disclaimer": "本审核结果仅供教学演示，不构成真实医疗诊断或治疗建议。所有数据均为合成数据。",
  "agent_trace": [
    {
      "agent_name": "intake_agent",
      "status": "completed",
      "input_summary": "接收病例 synthetic-case-001",
      "output_summary": "输入校验通过",
      "started_at": "2024-01-20T10:30:00.000Z",
      "duration_ms": 45,
      "rule_ids": [],
      "error": null
    },
    {
      "agent_name": "retrieval_agent",
      "status": "completed",
      "input_summary": "检索关键词：胸部不适, 持续性",
      "output_summary": "检索到3条相关知识",
      "started_at": "2024-01-20T10:30:00.050Z",
      "duration_ms": 120,
      "rule_ids": [],
      "error": null
    },
    {
      "agent_name": "risk_agent",
      "status": "completed",
      "input_summary": "评估风险等级",
      "output_summary": "规则引擎判定 HIGH，模型建议 LOW",
      "started_at": "2024-01-20T10:30:00.180Z",
      "duration_ms": 200,
      "rule_ids": ["RULE-001"],
      "error": null
    },
    {
      "agent_name": "safety_agent",
      "status": "completed",
      "input_summary": "安全审核与摘要生成",
      "output_summary": "生成安全摘要，标记安全标志",
      "started_at": "2024-01-20T10:30:00.400Z",
      "duration_ms": 150,
      "rule_ids": [],
      "error": null
    }
  ],
  "ruleset_version": "v1.0.0",
  "model_version": "gpt-4o-2024-08-06",
  "prompt_version": "v1.0.0",
  "knowledge_base_version": "synthetic-v1"
}
```

**响应字段详细说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| case_id | string | 病例标识，与请求中一致 |
| final_risk_level | string | **最终确定的风险等级**。当规则引擎判定为 HIGH 或 CRITICAL 时，此值不会被模型下调，始终保持规则引擎的判定结果 |
| rule_risk_level | string | 规则引擎独立判定的风险等级 |
| model_suggested_risk | string | 模型建议的风险等级（可能为 null） |
| model_downgrade_blocked | bool | **模型降级是否被阻止**。当模型试图将 HIGH/CRITICAL 下调为更低等级时，系统会阻止降级，此字段为 `true` |
| needs_human_review | bool | **是否需要人工审核**。HIGH 和 CRITICAL 风险等级始终需要人工审核，此字段始终为 `true` |
| matched_rules | array | 命中的规则列表 |
| matched_rules[].rule_id | string | 规则唯一标识 |
| matched_rules[].name | string | 规则名称 |
| matched_rules[].risk_level | string | 该规则对应的风险等级 |
| matched_rules[].display_message | string | 规则触发时的展示信息 |
| matched_rules[].priority | int | 规则优先级 |
| retrieved_evidence | array | 检索到的知识引用列表 |
| retrieved_evidence[].chunk_id | string | 知识块唯一标识 |
| retrieved_evidence[].document_id | string | 所属文档标识 |
| retrieved_evidence[].title | string | 文档标题 |
| retrieved_evidence[].content | string | 知识块内容 |
| retrieved_evidence[].score | float | 相似度得分（0-1） |
| retrieved_evidence[].publisher | string | 发布机构 |
| retrieved_evidence[].source_url | string | 来源链接 |
| retrieved_evidence[].document_version | string | 文档版本 |
| retrieved_evidence[].chunk_index | int | 块在文档中的序号 |
| safety_flags | array | 安全审核标记列表 |
| safe_summary | string | 安全审核后的摘要文本 |
| disclaimer | string | 免责声明 |
| agent_trace | array | **Agent 审计记录**（不包含思维链或推理过程） |
| agent_trace[].agent_name | string | Agent 名称 |
| agent_trace[].status | string | 执行状态（completed/failed） |
| agent_trace[].input_summary | string | 输入摘要 |
| agent_trace[].output_summary | string | 输出摘要 |
| agent_trace[].started_at | datetime | 开始时间 |
| agent_trace[].duration_ms | int | 执行耗时（毫秒） |
| agent_trace[].rule_ids | array | 命中的规则ID列表 |
| agent_trace[].error | string | 错误信息（成功时为 null） |
| ruleset_version | string | 规则集版本 |
| model_version | string | 模型版本 |
| prompt_version | string | Prompt 版本 |
| knowledge_base_version | string | 知识库版本 |

**关键概念说明**

1. **final_risk_level（最终风险等级）**
   - 这是系统最终确定的风险等级
   - 当规则引擎判定为 HIGH 或 CRITICAL 时，此值不会被模型下调
   - 即使模型建议更低的风险等级，最终结果仍保持为 HIGH 或 CRITICAL

2. **model_downgrade_blocked（模型降级阻止）**
   - 当模型试图将 HIGH/CRITICAL 风险下调为更低等级时，系统会阻止这次降级
   - 此字段为 `true` 表示降级尝试被系统拦截
   - 这是安全机制的一部分，确保高风险病例不会被错误降级

3. **needs_human_review（需要人工审核）**
   - HIGH 和 CRITICAL 风险等级的病例始终需要人工审核
   - 系统不会自动处理这些高风险病例
   - 后端系统应根据此字段将病例路由至人工审核队列

4. **agent_trace（Agent 审计记录）**
   - 记录每个 Agent 的执行情况
   - 仅包含审计信息，不包含思维链（chain_of_thought）或推理过程
   - 用于追踪和调试审核流程

**状态码**

| 状态码 | 说明 |
|--------|------|
| 200 | 审核完成 |
| 422 | 请求参数校验失败 |
| 503 | 预问诊服务未初始化 |

**错误场景**

| 错误信息 | 原因 |
|----------|------|
| `非法红旗标识: {flag}，合法值: [...]` | red_flags 包含非法值 |
| `非法风险等级: {v}，合法值: LOW/MEDIUM/HIGH/CRITICAL` | model_suggested_risk 值不合法 |
| `预问诊服务未初始化` | 服务启动时初始化失败 |

---

### 3.7 分诊分析

#### `POST /api/v1/triage/analyze`

对合成教学病例进行分诊分析，复用多Agent安全审核流程。返回统一输出结构。

**安全声明**：本接口仅供教学演示，不提供真实诊断或替代医生。

**请求示例**

```json
{
  "case_id": "synthetic-triage-001",
  "age": 30,
  "symptoms": [
    {"name": "头痛", "severity": 5, "duration": "2小时"}
  ],
  "red_flags": [],
  "free_text": "合成教学病例。",
  "model_suggested_risk": "LOW"
}
```

请求字段与 `POST /api/v1/preconsultation/review` 一致。

**响应示例**

```json
{
  "case_id": "synthetic-triage-001",
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "risk_level": "LOW",
  "symptom_summary": "头痛（持续2小时，严重程度5/10）",
  "red_flags": [],
  "evidence": [],
  "citations": [],
  "missing_information": [],
  "followup_questions": [],
  "safety_status": "pass",
  "disclaimer": "以上内容仅供教学演示，不构成诊断或治疗建议。如需就医请咨询专业医疗机构。"
}
```

**统一输出字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| trace_id | string | 请求追踪ID（UUID4），每次请求唯一 |
| risk_level | string | 最终风险等级 |
| symptom_summary | string | 标准化症状摘要 |
| red_flags | array | 红旗标识列表 |
| evidence | array | 证据列表 |
| citations | array | 引用来源列表 |
| missing_information | array | 缺失信息字段 |
| followup_questions | array | 根据缺失字段生成的追问问题 |
| safety_status | string | 安全状态：pass / blocked / human_review |
| disclaimer | string | 免责声明 |

**状态码**

| 状态码 | 说明 |
|--------|------|
| 200 | 分析完成 |
| 422 | 请求参数校验失败 |
| 503 | 分诊服务未初始化 |

---

### 3.8 安全检查

#### `POST /api/v1/safety/check`

对待审核文本进行安全检查，不执行完整多Agent流程。

**安全声明**：本接口仅供教学演示，不提供真实诊断或替代医生。

**请求示例**

```json
{
  "text": "待审核的文本内容",
  "risk_level": "HIGH",
  "needs_human_review": false
}
```

**请求字段说明**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 待审核文本（1-10000字符） |
| risk_level | string | 否 | 当前风险等级（LOW/MEDIUM/HIGH/CRITICAL） |
| needs_human_review | bool | 否 | 当前是否标记需要人工审核 |

**响应示例**

```json
{
  "trace_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "safety_status": "blocked",
  "safety_flags": ["contains_definitive_diagnosis"],
  "sanitized_text": "[已拦截: 不允许确定性诊断表述]",
  "needs_human_review": false,
  "disclaimer": "以上内容仅供教学演示，不构成诊断或治疗建议。"
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| trace_id | string | 请求追踪ID（UUID4） |
| safety_status | string | 安全状态：pass / blocked / human_review |
| safety_flags | array | 安全标记列表 |
| sanitized_text | string | 清理后的文本（不安全内容已替换） |
| needs_human_review | bool | 是否需要人工审核 |
| disclaimer | string | 免责声明 |

**检查项**

| 检查项 | safety_flag 值 | 说明 |
|--------|----------------|------|
| 确定性疾病诊断 | contains_definitive_diagnosis | 如"你就是XX病" |
| 药物处方/剂量 | contains_prescription_or_dosage | 如"服用XX 500mg" |
| 取消人工审核 | cancel_human_review_detected | 如"不需要人工审核" |
| 高风险缺人工审核 | high_risk_missing_human_review | HIGH/CRITICAL但未标记审核 |

---

## 4. 安全字段说明

### 4.1 风险等级字段

| 字段 | 说明 | 安全规则 |
|------|------|----------|
| final_risk_level | 最终风险等级 | 不可被模型下调 |
| rule_risk_level | 规则引擎风险等级 | 独立于模型判定 |
| model_suggested_risk | 模型建议风险等级 | 仅供参考 |

### 4.2 安全控制字段

| 字段 | 说明 | 安全机制 |
|------|------|----------|
| model_downgrade_blocked | 模型降级是否被阻止 | 防止高风险被错误降级 |
| needs_human_review | 是否需要人工审核 | 高风险病例必须人工处理 |
| safety_flags | 安全审核标记 | 标识触发的安全规则类型 |

### 4.3 红旗标识

红旗标识代表需要立即关注的危险信号：

| 标识 | 说明 |
|------|------|
| consciousness_change | 意识状态改变 |
| severe_breathing_difficulty | 严重呼吸困难 |
| persistent_chest_discomfort | 持续性胸部不适 |
| uncontrolled_bleeding | 无法控制的出血 |
| self_harm_risk | 自伤风险 |
| pregnancy_emergency_signal | 妊娠紧急信号 |

---

## 5. 版本字段说明

所有版本字段用于追踪系统组件版本，确保可追溯性和一致性：

| 字段 | 说明 | 用途 |
|------|------|------|
| ruleset_version | 规则集版本 | 追踪规则引擎使用的规则版本 |
| model_version | 模型版本 | 追踪使用的AI模型版本 |
| prompt_version | Prompt 版本 | 追踪使用的提示词模板版本 |
| knowledge_base_version | 知识库版本 | 追踪知识库的数据版本 |

**版本字段格式建议**
- 语义化版本：`v1.0.0`
- 日期版本：`2024-01-15`
- 自定义标识：`synthetic-v1`

---

## 6. 合成教学声明

### 6.1 数据声明

本服务所有数据均为合成生成，包括但不限于：
- 病例数据
- 知识库内容
- 示例代码
- 测试数据

### 6.2 使用限制

本服务：
- 不提供真实医疗诊断
- 不替代医生专业判断
- 不用于实际医疗决策
- 仅用于教学演示目的

### 6.3 责任声明

使用本服务产生的任何结果：
- 不构成医疗建议
- 不承担医疗责任
- 不作为诊断依据
- 仅供学习参考

---

## 附录

### A. 完整请求示例

**导入知识文档**

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/documents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "高血压基层诊疗指南（教学版）",
    "publisher": "中华医学会（示例）",
    "source_url": "https://example.org/guidelines/hypertension",
    "document_version": "2024教学版",
    "content": "高血压定义为在未使用降压药物的情况下，非同日3次诊室血压测量..."
  }'
```

**预问诊安全审核**

```bash
curl -X POST http://localhost:8000/api/v1/preconsultation/review \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "synthetic-case-001",
    "age": 45,
    "symptoms": [{"name": "胸部不适", "severity": 7, "duration": "30分钟"}],
    "red_flags": ["persistent_chest_discomfort"],
    "free_text": "这是一个合成教学病例。",
    "model_suggested_risk": "LOW"
  }'
```

### B. 错误码汇总

| 状态码 | 含义 | 常见原因 |
|--------|------|----------|
| 200 | 成功 | 请求正常处理 |
| 404 | 资源不存在 | 文档ID不存在 |
| 422 | 参数校验失败 | 请求字段不符合约束 |
| 503 | 服务不可用 | 服务未初始化或正在启动 |

---

*文档版本：v1.0.0*  
*最后更新：2024-01-20*  
*安全声明：本服务仅供教学演示，不构成真实医疗诊断或治疗建议。*