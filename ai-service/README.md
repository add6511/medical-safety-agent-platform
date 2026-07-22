# 基层医疗安全型预问诊AI服务

## 模块用途

本模块是医疗安全Agent平台的AI服务组件，提供预问诊相关的AI能力接口，包括：
- 健康检查
- 知识库文档管理（导入、查询、删除）
- RAG 知识检索

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

## 访问地址

- 健康检查：http://localhost:8000/health
- Swagger 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

## 运行测试

```powershell
# 确保虚拟环境已激活
.\.venv\Scripts\Activate.ps1

# 运行测试（安静模式）
python -m pytest -q

# 运行测试（详细输出）
python -m pytest -v
```

## RAG 处理流程

1. **文档导入**：通过 `POST /api/v1/knowledge/documents` 导入教学文档（JSON 格式）
2. **校验去重**：计算文档内容的 SHA-256 校验值，相同校验值的文档不重复创建
3. **文本切分**：使用 `RecursiveCharacterTextSplitter` 按中文语义边界切分文档
4. **向量化**：将每个知识块通过 Embedding 接口转换为向量
5. **存储**：将知识块元信息和向量存储到向量库
6. **检索**：通过 `POST /api/v1/knowledge/search` 进行语义相似度检索

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

#### pgvector 迁移方法

```powershell
# 确保 PostgreSQL 已安装 pgvector 扩展
# 执行迁移脚本
psql -U your_user -d your_database -f migrations/001_pgvector.sql
```

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
| EMBEDDING_DIMENSION | 384 | Embedding 向量维度 |
| CHUNK_SIZE | 500 | 文档切分块大小 |
| CHUNK_OVERLAP | 80 | 块重叠大小（必须小于 CHUNK_SIZE） |
| VECTOR_DATABASE_URL | | pgvector 数据库连接 |
| EMBEDDING_BASE_URL | | Embedding 接口地址（openai_compatible 模式） |
| EMBEDDING_API_KEY | | Embedding API 密钥（仅从环境变量读取） |
| EMBEDDING_MODEL | | Embedding 模型名称 |

## API 接口示例

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

### 查询文档列表

```bash
curl http://localhost:8000/api/v1/knowledge/documents
```

### 知识检索

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "高血压的诊断标准是什么", "top_k": 5}'
```

### 删除文档

```bash
curl -X DELETE http://localhost:8000/api/v1/knowledge/documents/{document_id}
```

## 安全限制

- 本服务仅供教学演示，不提供真实诊断或替代医生
- 当前未内置真实医学指南，所有测试数据均为合成教学材料
- 不接受患者姓名、身份证号、手机号等真实个人数据
- 知识库内容不构成诊断或治疗建议
- 检索接口只返回知识片段和来源，不生成诊断结论
- API 密钥只能从环境变量读取，禁止硬编码

## 目录结构

```
ai-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py        # 路由注册中心
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py    # 健康检查路由
│   │       └── knowledge.py # 知识库路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   └── logging.py       # 日志配置
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── text_splitter.py # 文档切分
│   │   ├── embedding.py     # Embedding 接口及实现
│   │   └── vector_store.py  # 向量存储接口及实现
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py        # 通用数据模型
│   │   └── knowledge.py     # 知识库数据模型
│   └── services/
│       ├── __init__.py
│       └── knowledge_service.py  # 知识库业务服务
├── migrations/
│   └── 001_pgvector.sql     # pgvector 迁移脚本
├── tests/
│   ├── __init__.py
│   ├── test_health.py       # 健康检查测试
│   └── test_rag.py          # RAG 功能测试
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```
