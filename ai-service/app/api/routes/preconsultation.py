"""
预问诊审核 API 路由
提供 POST /api/v1/preconsultation/review 接口

安全声明：本接口仅供教学演示，不提供真实诊断或替代医生。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.schemas.preconsultation import PreconsultationRequest, PreconsultationResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["预问诊审核"])

# 预问诊服务实例（延迟初始化）
_preconsultation_service = None


def set_preconsultation_service(service) -> None:
    """设置预问诊服务实例"""
    global _preconsultation_service
    _preconsultation_service = service


def get_preconsultation_service():
    """获取预问诊服务实例"""
    if _preconsultation_service is None:
        raise HTTPException(status_code=503, detail="预问诊服务未初始化")
    return _preconsultation_service


@router.post(
    "/preconsultation/review",
    response_model=PreconsultationResponse,
    summary="预问诊安全审核",
    description=(
        "对合成教学病例进行多Agent安全审核流程。\n\n"
        "**安全声明：本接口仅供教学演示，不提供真实诊断或替代医生。**\n\n"
        "审核流程：输入校验 → 知识检索 → 风险评估 → 安全审核\n\n"
        "注意：HIGH/CRITICAL 风险由规则引擎确定，不允许模型下调。"
    ),
)
async def review_preconsultation(request: PreconsultationRequest) -> PreconsultationResponse:
    """执行预问诊安全审核"""
    service = get_preconsultation_service()

    # 转换为字典
    request_data = request.model_dump()

    # 如果症状是 Pydantic 对象列表，转换为字典列表
    if request_data.get("symptoms"):
        request_data["symptoms"] = [
            s.model_dump() if hasattr(s, "model_dump") else s
            for s in request.symptoms
        ]

    result = service.review(request_data)

    return PreconsultationResponse(**result)
