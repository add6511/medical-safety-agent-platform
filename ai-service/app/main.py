"""
FastAPI 应用入口
基层医疗安全型预问诊AI服务

安全声明：本服务仅供教学演示，不提供真实诊断或替代医生。
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化，关闭时清理"""
    # 启动阶段
    setup_logging()
    logger.info("服务启动中... 应用名称=%s, 版本=%s, 环境=%s", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)
    logger.info("AI模式=%s", settings.AI_MODE)
    yield
    # 关闭阶段
    logger.info("服务正在关闭...")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例"""
    app = FastAPI(
        title="基层医疗安全型预问诊AI服务",
        version=settings.APP_VERSION,
        description=(
            "基层医疗安全型预问诊AI服务接口文档。\n\n"
            "**安全声明：本服务仅供教学演示，不提供真实诊断或替代医生。**"
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router)

    return app


# 应用实例（供 uvicorn 直接引用）
app = create_app()
