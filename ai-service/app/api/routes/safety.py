"""
安全检查 API 路由
提供 POST /api/v1/safety/check 接口

复用 SafetyReviewAgent 的正则模式进行文本安全检查。

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

logger = logging.getLogger(__name__)

router = APIRouter(tags=["安全检查"])


def _check_text_safety(
    text: str,
    risk_level: str | None = None,
    needs_human_review: bool | None = None,
) -> dict:
    """
    执行文本安全检查

    Args:
        text: 待审核文本
        risk_level: 当前风险等级
        needs_human_review: 当前是否标记人工审核

    Returns:
        安全检查结果
    """
    trace_id = str(uuid.uuid4())
    flags: list[str] = []
    sanitized = text
    human_review = needs_human_review or False

    # 检查确定性诊断表述（累计所有类型，不提前退出）
    diagnosis_detected = False
    for pattern in _DIAGNOSIS_PATTERNS:
        if pattern.search(text):
            flags.append("contains_definitive_diagnosis")
            sanitized = pattern.sub("[已拦截: 不允许确定性诊断表述]", sanitized)
            diagnosis_detected = True
            break

    # 检查药物处方或具体剂量
    prescription_detected = False
    for pattern in _PRESCRIPTION_PATTERNS:
        if pattern.search(text):
            flags.append("contains_prescription_or_dosage")
            sanitized = pattern.sub("[已拦截: 不允许药物处方或具体剂量]", sanitized)
            prescription_detected = True
            break

    # 检查取消人工审核的危险表述
    cancel_detected = False
    for pattern in _CANCEL_REVIEW_PATTERNS:
        if pattern.search(text):
            flags.append("cancel_human_review_detected")
            cancel_detected = True
            break

    # 检查 HIGH/CRITICAL 风险是否被降低
    if risk_level in ("HIGH", "CRITICAL"):
        if not needs_human_review:
            flags.append("high_risk_missing_human_review")
            human_review = True

    # 确定安全状态：只要存在不安全内容就 blocked
    has_unsafe = diagnosis_detected or prescription_detected or cancel_detected
    if has_unsafe:
        safety_status = "blocked"
        human_review = True
        # 替换为安全说明，不泄露原始不安全文本
        sanitized = _BLOCKED_DISCLAIMER
    elif human_review or risk_level in ("HIGH", "CRITICAL"):
        safety_status = "human_review"
    else:
        safety_status = "pass"

    # 确保 sanitized_text 不为空
    if not sanitized.strip():
        sanitized = "【安全拦截】内容已被清理。"

    disclaimer = "以上内容仅供教学演示，不构成诊断或治疗建议。"

    return {
        "trace_id": trace_id,
        "safety_status": safety_status,
        "safety_flags": flags,
        "sanitized_text": sanitized,
        "needs_human_review": human_review,
        "disclaimer": disclaimer,
    }


@router.post(
    "/safety/check",
    summary="安全检查",
    description=(
        "对待审核文本进行安全检查。\n\n"
        "**安全声明：本接口仅供教学演示，不提供真实诊断或替代医生。**\n\n"
        "检查内容：确定性诊断、药物处方、取消人工审核、风险降级。\n\n"
        "原始不安全文本不得通过 API 返回。"
    ),
)
async def check_safety(request: dict) -> dict:
    """执行安全检查"""
    # 兼容 text 和 candidate_text 两种字段名
    text = request.get("text") or request.get("candidate_text") or ""
    risk_level = request.get("risk_level")
    needs_human_review = request.get("needs_human_review")

    if not text.strip():
        return {
            "trace_id": str(uuid.uuid4()),
            "safety_status": "pass",
            "safety_flags": [],
            "sanitized_text": "",
            "needs_human_review": False,
            "disclaimer": "以上内容仅供教学演示，不构成诊断或治疗建议。",
        }

    return _check_text_safety(text, risk_level, needs_human_review)
