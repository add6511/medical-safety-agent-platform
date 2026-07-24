# 系统总体架构图

```mermaid
graph TB
    subgraph UserLayer["用户层"]
        Patient["患者浏览器"]
        Doctor["医务人员浏览器"]
        FollowUp["随访人员浏览器"]
        Admin["管理员浏览器"]
    end

    subgraph Gateway["接入层 [设计目标]"]
        Nginx["Nginx 反向代理\n端口 80/443"]
    end

    subgraph Frontend["前端 [已实现]"]
        Vue["Vue 3 + TypeScript\nElement Plus + ECharts\nVite 开发服务器 端口 5173\nMock 数据层"]
    end

    subgraph Backend["后端 [PR #10 开发中]"]
        SpringBoot["Spring Boot\n端口 8080\n用户认证 / 业务 CRUD"]
    end

    subgraph AIService["AI 服务 [已实现]"]
        FastAPI["FastAPI\n端口 8000\n多 Agent 安全审核"]
        RulesEngine["合成安全规则引擎"]
        RAG["RAG 知识检索\nEmbedding + 向量搜索"]
        Agents["多 Agent Pipeline\nIntake -> Retrieval\n-> Risk -> Safety"]
        LoRA["LoRA 微调模型\nQwen2.5-0.5B\nV1/V2 已完成"]
    end

    subgraph DataLayer["数据层"]
        MySQL[("MySQL\n业务数据 [设计目标]")]
        PGVector[("pgvector\nPostgreSQL 15\n知识块向量 [已实现]")]
        Redis[("Redis\n缓存/会话 [设计目标]")]
    end

    Patient --> Nginx
    Doctor --> Nginx
    FollowUp --> Nginx
    Admin --> Nginx
    Nginx --> Vue
    Nginx --> SpringBoot
    SpringBoot -->|"内部调用"| FastAPI
    SpringBoot --> MySQL
    SpringBoot --> Redis
    FastAPI --> PGVector
    FastAPI --> RulesEngine
    FastAPI --> RAG
    FastAPI --> Agents
    RAG --> PGVector
    Agents --> LoRA
```

## 说明

- **目标调用链**：前端 -> Spring Boot 后端 -> FastAPI AI 服务
- **FastAPI 不直接向普通前端公开**，应通过 Spring Boot 后端代理调用
- **当前状态**：前端使用 Mock 数据和占位接口，尚未完成真实接口联调
- **设计目标节点**：Nginx、Redis、MySQL、随访人员浏览器
- **已实现节点**：Vue 前端（Mock 数据层）、FastAPI AI 服务、pgvector 向量存储、LoRA 微调
- **PR #10 待审核**：Spring Boot 后端接口最终以合并版本为准
