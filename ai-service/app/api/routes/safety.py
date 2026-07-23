"""
安全检查 API 路由
提供 POST /api/v1/safety/check 接口

集成输入安全检测（提示词攻击、PII）和输出安全检测。

安全声明：本接口仅供教学演示，不提供真实诊断或替代医生。
原始不安全文本不得通过 API 返回。
"""

import logging
import uuid

from fastapi import APIRouter

from app.agents.safety_agent import (
    _BLOCKED_DISCLAIMER,
    _CANCEL_REVIEW_PATTERNS,
    _DIAGNOSIS_PATTERNS,
    _DISCLAIMER_KEYWORDS,
    _PRESCRIPTION_PATTERNS,
)
from app.schemas.safety import SafetyCheckRequest, SafetyCheckResponse
from app.security.input_guard import check_input_safety

logger = logging.getLogger(__name__)

router = APIRouter(tags=["安全检查"])


def _check_text_safety(
    text: str,
    risk_level: str | None = None,
    needs_human_review: bool | None = None,
) -> SafetyCheckResponse:
    """
    执行文本安全检查（集成输入安全检测）

    Args:
        text: 待审核文本
        risk_level: 当前风险等级
        needs_human_review: 当前是否标记人工审核

    Returns:
        安全检查结果
    """
    trace_id = str(uuid.uuid4())
    flags: list[str] = []
    human_review = needs_human_review or False

    # 1. 输入安全检测（提示词攻击 + PII）
    input_guard = check_input_safety(text)
    flags.extend(input_guard.flags)
    sanitized = input_guard.sanitized_text

    if input_guard.is_blocked:
        human_review = True

    # 2. 输出安全检测（诊断、处方、取消审核）
    diagnosis_detected = False
    for pattern in _DIAGNOSIS_PATTERNS:
        if pattern.search(text):
            flags.append("contains_definitive_diagnosis")
            sanitized = pattern.sub("[已拦截: 不允许确定性诊断表述]", sanitized)
            diagnosis_detected = True
            break

    prescription_detected = False
    for pattern in _PRESCRIPTION_PATTERNS:
        if pattern.search(text):
            flags.append("contains_prescription_or_dosage")
            sanitized = pattern.sub("[已拦截: 不允许药物处方或具体剂量]", sanitized)
            prescription_detected = True
            break

    cancel_detected = False
    for pattern in _CANCEL_REVIEW_PATTERNS:
        if pattern.search(text):
            flags.append("cancel_human_review_detected")
            cancel_detected = True
            break

    # 3. 风险降级检查
    if risk_level in ("HIGH", "CRITICAL"):
        if not needs_human_review:
            flags.append("high_risk_missing_human_review")
            human_review = True

    # 4. 确定安全状态
    has_unsafe_output = diagnosis_detected or prescription_detected or cancel_detected
    has_injection = input_guard.is_blocked

    if has_injection or has_unsafe_output:
        safety_status = "blocked"
        human_review = True
        # 替换为安全说明
        sanitized = _BLOCKED_DISCLAIMER
    elif human_review or risk_level in ("HIGH", "CRITICAL"):
        safety_status = "human_review"
    else:
        safety_status = "pass"

    if not sanitized.strip():
        sanitized = "【安全拦截】内容已被清理。"

    disclaimer = "以上内容仅供教学演示，不构成诊断或治疗建议。"

    return SafetyCheckResponse(
        trace_id=trace_id,
        safety_status=safety_status,
        safety_flags=flags,
        sanitized_text=sanitized,
        needs_human_review=human_review,
        disclaimer=disclaimer,
    )


@router.post(
    "/safety/check",
    response_model=SafetyCheckResponse,
    summary="安全检查",
    description=(
        "对待审核文本进行安全检查。\n\n"
        "**安全声明：本接口仅供教学演示，不提供真实诊断或替代医生。**\n\n"
        "检查内容：提示词攻击、越权指令、敏感信息、确定性诊断、药物处方、取消人工审核、风险降级。\n\n"
        "原始不安全文本不得通过 API 返回。"
    ),
)
def check_safety(request: SafetyCheckRequest) -> SafetyCheckResponse:
    """执行安全检查"""
    text = request.text or request.candidate_text
    risk_level = request.risk_level
    needs_human_review = request.needs_human_review

    return _check_text_safety(text, risk_level, needs_human_review)
