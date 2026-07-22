"""
API 路由注册中心
统一管理所有路由模块，使用 /api/v1 作为业务接口前缀
"""

from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.knowledge import router as knowledge_router

# 主路由：挂载所有子路由
api_router = APIRouter()

# 健康检查路由（不带版本前缀，直接挂在根路径）
api_router.include_router(health_router)

# 业务接口统一前缀路由
v1_router = APIRouter(prefix="/api/v1")

# 知识库路由
v1_router.include_router(knowledge_router)

# 后续在此处挂载其他业务路由，例如：
# v1_router.include_router(chat_router, prefix="/chat", tags=["问诊"])
# v1_router.include_router(safety_router, prefix="/safety", tags=["安全检查"])

api_router.include_router(v1_router)
