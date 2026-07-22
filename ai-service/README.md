# 基层医疗安全型预问诊AI服务

## 模块用途

本模块是医疗安全Agent平台的AI服务组件，提供预问诊相关的AI能力接口，包括：
- 健康检查
- 知识库文档管理（导入、查询、删除）
- RAG 知识检索
- 合成安全规则引擎
- 多 Agent 安全审核流程
- 合成病例评测与报告生成

**安全边界声明：本服务仅供教学演示，不提供真实诊断或替代医生。所有AI输出仅供参考，不能作为医疗决策依据。知识库内容不构成诊断或治疗建议。**

**当前未内置真实医学指南，所有测试数据均为合成教学材料。**

## 技术栈

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic v2
- pydantic-settings
- langchain-text-splitters
- psycopg v3 + pgvector
- Pytest

## 安装步骤（Windows PowerShell）

### 1. 创建虚拟环境

```powershell
# 进入 ai-service 目录
cd ai-service

# 创建虚拟环境（优先使用 Python 3.11）
py -3.11 -m venv .venv

# 如果系统没有 py -3.11，使用：
# python -m venv .venv
```

### 2. 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

> 如果遇到执行策略错误，先运行：
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 3. 安装依赖

```powershell
# 安装开发依赖（包含生产依赖和测试工具）
pip install -r requirements-dev.txt
```

### 4. 配置环境变量

```powershell
# 复制示例配置文件
Copy-Item .env.example .env

# 按需编辑 .env 文件
notepad .env
```

## 启动服务

```powershell
# 确保虚拟环境已激活
.\.venv\Scripts\Activate.ps1

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker 构建与启动

```powershell
# 构建镜像
docker build -t medical-safety-ai:0.1.0 .

# 启动容器
docker run --rm -p 8000:8000 --name medical-safety-ai medical-safety-ai:0.1.0

# 带环境变量启动
docker run --rm -p 8000:8000 `
  -e APP_ENV=production `
  -e VECTOR_STORE_MODE=memory `
  -e EMBEDDING_MODE=mock `
  --name medical-safety-ai medical-safety-ai:0.1.0

# 健康检查
curl http://localhost:8000/health
```

## 访问地址

- 健康检查：http://localhost:8000/health
- Swagger 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc
- OpenAPI JSON：http://localhost:8000/openapi.json

## OpenAPI 导出

```powershell
# 确保虚拟环境已激活
.\.venv\Scripts\Activate.ps1

# 导出 OpenAPI JSON
python scripts/export_openapi.py

# 输出到 docs/openapi.json
```

## Smoke Test

```powershell
# 确保服务已启动，虚拟环境已激活
python scripts/smoke_test.py --base-url http://127.0.0.1:8000

# 或使用默认地址
python scripts/smoke_test.py
```

## Spring Boot 对接

后端通过 HTTP 调用本 AI 服务，前端不得直接调用。详见 `docs/INTEGRATION_GUIDE.md`。

关键要点：
- 传递 `X-Request-ID` 用于请求追踪
- AI 服务不可用时必须进入人工审核流程
- AI 调用失败不能自动降低风险等级
- 知识检索可重试，预问诊审核不应盲目重试

## 运行测试

```powershell
# 确保虚拟环境已激活
.\.venv\Scripts\Activate.ps1

# 运行测试（安静模式）
python -m pytest -q

# 运行测试（详细输出）
python -m pytest -v
```

## 运行评测

```powershell
# 运行合成病例评测
python -m app.evaluation --dataset evaluation/datasets/synthetic_cases_v1.json --output-dir reports/evaluation/latest

# 查看报告
# reports/evaluation/latest/summary.json
# reports/evaluation/latest/case_results.csv
# reports/evaluation/latest/report.md
```

## 接口契约

详见 `docs/API_CONTRACT.md`，包含所有接口的请求/响应示例和字段说明。

## 环境变量说明

| 变量名 | 默认值 | 说明 |
|---|---|---|
| APP_NAME | 基层医疗安全型预问诊AI服务 | 应用名称 |
| APP_VERSION | 0.1.0 | 应用版本 |
| APP_ENV | development | 运行环境 |
| LOG_LEVEL | INFO | 日志级别 |
| AI_MODE | mock | AI 模式（mock/real） |
| CORS_ORIGINS | http://localhost:3000,http://localhost:5173 | CORS 允许的前端地址 |
| **RAG 相关** | | |
| VECTOR_STORE_MODE | memory | 向量存储模式（memory/pgvector） |
| EMBEDDING_MODE | mock | Embedding 模式（mock/openai_compatible） |
| EMBEDDING_DIMENSION | 384 | Embedding 向量维度（pgvector 模式必须为 384） |
| CHUNK_SIZE | 500 | 文档切分块大小 |
| CHUNK_OVERLAP | 80 | 块重叠大小（必须小于 CHUNK_SIZE） |
| VECTOR_DATABASE_URL | | pgvector 数据库连接 |
| EMBEDDING_BASE_URL | | Embedding 接口地址（openai_compatible 模式） |
| EMBEDDING_API_KEY | | Embedding API 密钥（仅从环境变量读取） |
| EMBEDDING_MODEL | | Embedding 模型名称 |
| **Agent 相关** | | |
| AGENT_MODE | mock | Agent 模式（mock/real） |
| SAFETY_RULESET_VERSION | synthetic-1.0.0 | 安全规则集版本 |
| MODEL_VERSION | mock-medical-agent-v1 | 模型版本标识 |
| PROMPT_VERSION | preconsultation-v1 | Prompt 版本标识 |
| ENABLE_MODEL_RISK_SUGGESTION | true | 是否启用模型风险建议 |

## RAG 处理流程

1. **文档导入**：通过 `POST /api/v1/knowledge/documents` 导入教学文档（JSON 格式）
2. **校验去重**：计算文档内容的 SHA-256 校验值，相同校验值的文档不重复创建
3. **文本切分**：使用 `RecursiveCharacterTextSplitter` 按中文语义边界切分文档
4. **向量化**：将每个知识块通过 Embedding 接口转换为向量
5. **存储**：将知识块元信息和向量存储到向量库
6. **检索**：通过 `POST /api/v1/knowledge/search` 进行语义相似度检索

## 多 Agent 审核流程

1. **IntakeAgent**：校验和规范化输入，识别症状和红旗
2. **RetrievalAgent**：调用知识库进行 RAG 检索
3. **RiskAssessmentAgent**：执行规则引擎，模型建议不可下调 HIGH/CRITICAL
4. **SafetyReviewAgent**：检查输出安全性，拦截不安全内容

## 向量存储模式

### memory 模式（默认）

- 所有数据存储在内存中，服务重启后数据丢失
- 适合本地开发和测试
- 无需数据库依赖
- 使用余弦相似度进行检索

### pgvector 模式

- 使用 PostgreSQL + pgvector 扩展存储向量
- 数据持久化，适合生产环境
- 需要先执行迁移脚本初始化数据库
- **EMBEDDING_DIMENSION 必须为 384**（与迁移脚本一致）

#### pgvector 迁移方法

```powershell
# 确保 PostgreSQL 已安装 pgvector 扩展
# 执行迁移脚本
psql -U your_user -d your_database -f migrations/001_pgvector.sql
```

## 接口示例

### 导入文档

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/documents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "高血压基层诊疗指南（合成教学材料）",
    "publisher": "教学演示机构",
    "source_url": "https://example.org/guidelines/hypertension",
    "document_version": "2024教学版",
    "content": "高血压的诊断标准：在未使用降压药物的情况下..."
  }'
```

### 预问诊审核

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

### 分诊分析

```bash
curl -X POST http://localhost:8000/api/v1/triage/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "synthetic-triage-001",
    "age": 30,
    "symptoms": [{"name": "头痛", "severity": 5, "duration": "2小时"}],
    "free_text": "合成教学病例。",
  }'
```

### 安全检查

```bash
curl -X POST http://localhost:8000/api/v1/safety/check \
  -H "Content-Type: application/json" \
  -d '{"text": "待审核文本内容"}'
```

## 安全限制

- 本服务仅供教学演示，不提供真实诊断或替代医生
- 当前未内置真实医学指南，所有测试数据均为合成教学材料
- 不接受患者姓名、身份证号、手机号等真实个人数据
- 知识库内容不构成诊断或治疗建议
- 检索接口只返回知识片段和来源，不生成诊断结论
- API 密钥只能从环境变量读取，禁止硬编码
- HIGH/CRITICAL 风险由规则引擎确定，不允许模型下调
- 所有评测结果不得宣传为真实临床准确率

## 目录结构

```
ai-service/
├── app/
│   ├── main.py                    # FastAPI 应用入口
│   ├── api/
│   │   ├── router.py              # 路由注册中心
│   │   └── routes/
│   │       ├── health.py          # 健康检查路由
│   │       ├── knowledge.py       # 知识库路由
│   │       └── preconsultation.py # 预问诊审核路由
│   ├── agents/                    # 多 Agent 审核流程
│   ├── core/
│   │   ├── config.py              # 配置管理
│   │   └── logging.py             # 日志配置
│   ├── evaluation/                # 评测模块
│   ├── rag/                       # RAG 检索组件
│   ├── rules/                     # 合成安全规则引擎
│   ├── schemas/                   # 数据模型
│   └── services/                  # 业务服务
├── docs/                          # 接口契约文档
├── evaluation/                    # 评测数据集和知识材料
├── migrations/                    # 数据库迁移脚本
├── reports/                       # 评测报告
├── scripts/                       # 工具脚本
├── tests/                         # 测试用例
├── Dockerfile                     # Docker 镜像构建
├── .dockerignore                  # Docker 构建排除
├── .env.example                   # 环境变量示例
├── .gitignore                     # Git 忽略规则
├── requirements.txt               # 生产依赖
├── requirements-dev.txt           # 开发依赖
└── README.md                      # 本文档
```
