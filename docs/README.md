# 基层医疗安全型预问诊与随访平台 — 文档目录

本目录包含项目的规格文档和架构设计图。

## 文档结构

```
docs/
├── README.md                          # 本文件 — 文档目录说明
├── requirements-and-design.md         # 需求规格与系统总体设计
└── diagrams/                          # Mermaid 架构图
    ├── system-architecture.md         # 系统总体架构图
    ├── core-business-flow.md          # 核心业务流程图
    ├── database-er.md                 # 数据库 ER 图
    ├── preconsultation-sequence.md    # 预问诊业务时序图
    └── docker-deployment.md           # Docker 部署图
```

## 文档说明

### requirements-and-design.md

需求规格与系统总体设计文档，包含：

- 项目背景、目标和系统边界
- 四类用户角色与用户故事
- 功能需求与非功能需求
- 权限矩阵
- 核心业务状态说明
- 前端、后端、AI 服务的接口边界
- 数据安全、隐私脱敏、审计、异常处理要求
- 系统仅供教学演示的声明

**重要说明**：文档中明确区分了"当前已实现"和"设计目标"，未完成的功能（如随访管理、Docker 联调）均标记为"设计目标"。

### diagrams/

Mermaid 格式的架构图，可在 GitHub 或支持 Mermaid 的 Markdown 渲染器中正常显示：

1. **system-architecture.md** — 展示 Vue 前端、Spring Boot 后端、FastAPI AI 服务、MySQL、pgvector、Redis、Nginx 的整体架构关系

2. **core-business-flow.md** — 展示从患者填报到结果归档的完整业务流程，包括信息脱敏、症状结构化、红旗规则预筛、医疗 RAG、多 Agent 风险复核、安全审核等环节

3. **database-er.md** — 展示 PR #10 当前拟合并物理模型、AI pgvector 已实现模型、后续设计目标模型的实体关系

4. **preconsultation-sequence.md** — 展示患者、前端、后端、AI 服务、规则引擎、RAG、数据库、医务人员之间的预问诊业务时序交互

5. **docker-deployment.md** — 展示 Nginx、frontend、backend、ai-service、MySQL、pgvector、Redis 的容器部署架构和健康检查配置

## 使用说明

### 查看 Mermaid 图

在 GitHub 上直接查看 `.md` 文件即可自动渲染 Mermaid 图。

本地查看可使用：
- VS Code + Mermaid 插件
- Typora
- 任意支持 Mermaid 的 Markdown 编辑器

### 文档更新

文档应与代码保持同步更新。当接口或业务流程发生变化时，请同步更新对应的文档和图表。

## 相关链接

- [项目根目录 README](../README.md)
- [AI 服务文档](../ai-service/README.md)
- [AI 服务 API 契约](../ai-service/docs/API_CONTRACT.md)
- [AI 服务集成指南](../ai-service/docs/INTEGRATION_GUIDE.md)
