"""
API 路由注册中心
统一管理所有路由模块，使用 /api/v1 作为业务接口前缀
"""

from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.preconsultation import router as preconsultation_router
from app.api.routes.triage import router as triage_router
from app.api.routes.safety import router as safety_router

# 主路由：挂载所有子路由
api_router = APIRouter()

# 健康检查路由（不带版本前缀，直接挂在根路径）
api_router.include_router(health_router)

# 业务接口统一前缀路由
v1_router = APIRouter(prefix="/api/v1")

# 知识库路由
v1_router.include_router(knowledge_router)

# 预问诊审核路由
v1_router.include_router(preconsultation_router)

# 分诊分析路由
v1_router.include_router(triage_router)

# 安全检查路由
v1_router.include_router(safety_router)

api_router.include_router(v1_router)
