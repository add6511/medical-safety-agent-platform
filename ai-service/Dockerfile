# 基层医疗安全型预问诊AI服务 - Docker 镜像
# 安全声明：仅供教学演示，不提供真实诊断或替代医生

FROM python:3.11-slim AS base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

# 设置工作目录
WORKDIR /app

# 安装系统依赖（最小化）
RUN apt-get update && \
    apt-get install -y --no-install-recommends tini && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码（不复制 .venv、缓存、测试、环境变量）
COPY app/ app/
COPY migrations/ migrations/

# 创建非 root 用户（固定 UID 10001）
RUN groupadd -r appuser -g 10001 && \
    useradd -r -g appuser -u 10001 -d /app -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER 10001:10001

# 暴露端口
EXPOSE 8000

# 健康检查（使用 Python urllib，不依赖 curl）
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 使用 tini 作为 PID 1 进程
ENTRYPOINT ["tini", "--"]

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
