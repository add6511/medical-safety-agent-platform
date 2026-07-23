"""
健康检查路由
提供 GET /health 接口，用于服务存活检测和状态监控
"""

from fastapi import APIRouter
from app.schemas.common import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["系统"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="返回服务运行状态、名称、版本和环境信息，用于服务存活检测。",
)
async def health_check() -> HealthResponse:
    """健康检查接口"""
    return HealthResponse(
        status="ok",
        service="medical-safety-ai-service",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )
