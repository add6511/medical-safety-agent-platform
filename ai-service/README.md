# 基层医疗安全型预问诊AI服务

## 模块用途

本模块是医疗安全Agent平台的AI服务组件，提供预问诊相关的AI能力接口。

**安全边界声明：本服务仅供教学演示，不提供真实诊断或替代医生。所有AI输出仅供参考，不能作为医疗决策依据。**

## 技术栈

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic v2
- pydantic-settings
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
│   │       └── health.py    # 健康检查路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   └── logging.py       # 日志配置
│   └── schemas/
│       ├── __init__.py
│       └── common.py        # 通用数据模型
├── tests/
│   ├── __init__.py
│   └── test_health.py       # 健康检查测试
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```
