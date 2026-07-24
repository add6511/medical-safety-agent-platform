# Docker 部署图

```mermaid
graph TB
    subgraph Compose["Docker Compose [设计目标]"]
        subgraph Gateway["接入层"]
            Nginx["Nginx\n端口 80/443\n反向代理 + 静态文件"]
        end

        subgraph Apps["应用层"]
            Frontend["frontend\nVue 3 + Nginx\n端口 [设计目标]"]
            Backend["backend\nSpring Boot\n端口 8080"]
            AIService["ai-service\nFastAPI\n端口 8000"]
        end

        subgraph Storage["数据层"]
            MySQL[("MySQL 8.0\n端口 3306\n业务数据")]
            PGVector[("pgvector\nPostgreSQL 15\n端口 5432\n向量数据")]
            Redis[("Redis 7\n端口 6379\n缓存")]
        end
    end

    Client["客户端浏览器"] --> Nginx
    Nginx -->|"/"| Frontend
    Nginx -->|"/api/*"| Backend
    Backend -->|"内部调用"| AIService
    Backend --> MySQL
    Backend --> Redis
    AIService --> PGVector

    subgraph HealthCheck["健康检查"]
        HC1["frontend: GET /"]
        HC2["backend: GET /actuator/health"]
        HC3["ai-service: GET /health"]
        HC4["mysql: mysqladmin ping"]
        HC5["pgvector: pg_isready"]
        HC6["redis: redis-cli ping"]
    end

    HC1 -.-> Frontend
    HC2 -.-> Backend
    HC3 -.-> AIService
    HC4 -.-> MySQL
    HC5 -.-> PGVector
    HC6 -.-> Redis

    style Nginx fill:#4CAF50,color:#fff
    style Frontend fill:#2196F3,color:#fff
    style Backend fill:#FF9800,color:#fff
    style AIService fill:#9C27B0,color:#fff
    style MySQL fill:#F44336,color:#fff
    style PGVector fill:#3F51B5,color:#fff
    style Redis fill:#E91E63,color:#fff
```

## 说明

- **Docker Compose 整体为设计目标**，当前仅 AI 服务 Dockerfile 已就绪
- **Nginx 统一入口**：前端只调用后端，后端通过内部调用连接 AI 服务
- **AI 服务只连接 pgvector**，不直接连接 MySQL
- **健康检查**：每个服务有对应的健康检查端点，虚线连接到对应服务
- **设计目标容器**：Nginx、frontend（端口待定）、backend、MySQL、Redis
- **pgvector 及 AI 服务**：迁移脚本及存储适配代码已实现，容器编排和真实联调仍为设计目标
