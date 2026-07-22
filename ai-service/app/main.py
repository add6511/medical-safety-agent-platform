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
from app.api.routes.knowledge import set_knowledge_service
from app.api.routes.preconsultation import set_preconsultation_service
from app.api.routes.triage import set_triage_service
from app.rag.embedding import create_embedding_provider
from app.rag.vector_store import create_vector_store
from app.services.knowledge_service import KnowledgeService
from app.services.preconsultation_service import PreconsultationService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化，关闭时清理"""
    # 启动阶段
    setup_logging()
    logger.info("服务启动中... 应用名称=%s, 版本=%s, 环境=%s", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)
    logger.info("AI模式=%s, 向量存储模式=%s, Embedding模式=%s", settings.AI_MODE, settings.VECTOR_STORE_MODE, settings.EMBEDDING_MODE)

    # 初始化 RAG 服务
    try:
        embedding_provider = create_embedding_provider()
        vector_store = create_vector_store()
        knowledge_service = KnowledgeService(vector_store, embedding_provider)
        set_knowledge_service(knowledge_service)
        logger.info("知识库服务初始化成功")

        # 初始化预问诊服务
        preconsultation_service = PreconsultationService(knowledge_service)
        set_preconsultation_service(preconsultation_service)
        logger.info("预问诊服务初始化成功")

        # 初始化分诊服务（复用预问诊服务）
        set_triage_service(preconsultation_service)
        logger.info("分诊服务初始化成功")
    except Exception as e:
        logger.error("知识库服务初始化失败: %s", type(e).__name__)
        # 不阻止服务启动，知识库接口将返回 503

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
            "**安全声明：本服务仅供教学演示，不提供真实诊断或替代医生。**\n\n"
            "知识库内容仅供教学参考，不构成诊断或治疗建议。"
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
