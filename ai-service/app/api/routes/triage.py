"""
分诊分析 API 路由
提供 POST /api/v1/triage/analyze 接口

复用 PreconsultationService 的多 Agent 流程。

安全声明：本接口仅供教学演示，不提供真实诊断或替代医生。
"""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.triage import TriageRequest, TriageResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["分诊分析"])

_triage_service = None


def set_triage_service(service) -> None:
    """设置分诊服务实例（复用 PreconsultationService）"""
    global _triage_service
    _triage_service = service


def get_triage_service():
    """获取分诊服务实例"""
    if _triage_service is None:
        raise HTTPException(status_code=503, detail="分诊服务未初始化")
    return _triage_service


@router.post(
    "/triage/analyze",
    response_model=TriageResponse,
    summary="分诊分析",
    description=(
        "对合成教学病例进行分诊分析，复用多Agent安全审核流程。\n\n"
        "**安全声明：本接口仅供教学演示，不提供真实诊断或替代医生。**"
    ),
)
async def analyze_triage(request: TriageRequest) -> TriageResponse:
    """执行分诊分析"""
    service = get_triage_service()

    # 复用 review 方法
    request_data = request.model_dump()
    if request_data.get("symptoms"):
        request_data["symptoms"] = [
            s.model_dump() if hasattr(s, "model_dump") else s
            for s in request.symptoms
        ]

    result = service.review(request_data)

    # 映射到统一输出结构
    return TriageResponse(
        case_id=result["case_id"],
        trace_id=result["trace_id"],
        risk_level=result["final_risk_level"],
        symptom_summary=result["symptom_summary"],
        red_flags=result["red_flags"],
        evidence=result["evidence"],
        citations=result["citations"],
        missing_information=result["missing_information"],
        followup_questions=result["followup_questions"],
        safety_status=result["safety_status"],
        disclaimer=result["disclaimer"],
    )
