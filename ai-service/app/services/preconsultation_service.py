"""
预问诊审核服务
协调 SupervisorAgent 和各子 Agent，返回统一审核结果

安全声明：本服务仅供教学演示，不提供真实诊断或替代医生。
"""

import logging
import uuid
from typing import Any, Dict, List

from app.agents.base import AgentContext
from app.agents.intake_agent import IntakeAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.safety_agent import SafetyReviewAgent
from app.agents.supervisor import SupervisorAgent
from app.core.config import settings
from app.rules.engine import SafetyRuleEngine
from app.security.input_guard import check_input_safety
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


def _collect_user_text(request_data: Dict[str, Any]) -> str:
    """收集所有用户可控文本字段用于安全检测"""
    parts = []
    for key in ("case_id", "free_text"):
        val = request_data.get(key, "")
        if isinstance(val, str) and val.strip():
            parts.append(val)
    for s in request_data.get("symptoms", []):
        if isinstance(s, dict):
            parts.append(str(s.get("name", "")))
            parts.append(str(s.get("duration", "")))
        elif hasattr(s, "name"):
            parts.append(str(s.name))
            parts.append(str(s.duration))
    for flag in request_data.get("red_flags", []):
        if isinstance(flag, str):
            parts.append(flag)
    return " ".join(parts)


class PreconsultationService:
    """预问诊审核服务"""

    def __init__(self, knowledge_service: KnowledgeService):
        self._knowledge_service = knowledge_service
        self._rule_engine = SafetyRuleEngine()
        self._supervisor = SupervisorAgent([
            IntakeAgent(),
            RetrievalAgent(knowledge_service),
            RiskAssessmentAgent(self._rule_engine),
            SafetyReviewAgent(),
        ])

    def review(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行预问诊审核

        Args:
            request_data: 请求数据字典

        Returns:
            审核结果字典
        """
        trace_id = str(uuid.uuid4())

        # 对所有用户输入字段进行统一安全检测
        all_user_text = _collect_user_text(request_data)
        input_guard = check_input_safety(all_user_text)

        # 对 free_text 单独进行脱敏（如果非空）
        free_text = request_data.get("free_text", "")
        if free_text and free_text.strip():
            free_text_guard = check_input_safety(free_text)
            sanitized_free_text = free_text_guard.sanitized_text
        else:
            sanitized_free_text = ""

        # 构建 Agent 上下文
        context = AgentContext(
            case_id=request_data.get("case_id", "unknown"),
            trace_id=trace_id,
            age=request_data.get("age"),
            symptoms=[s if isinstance(s, dict) else s.model_dump() for s in request_data.get("symptoms", [])],
            red_flags=request_data.get("red_flags", []),
            free_text=sanitized_free_text,
            model_suggested_risk=request_data.get("model_suggested_risk"),
        )

        # 执行审核流程
        result_context, audit_trail = self._supervisor.process(context)

        # 合并输入安全检测的标志
        all_safety_flags = list(result_context.safety_flags)
        for flag in input_guard.flags:
            if flag not in all_safety_flags:
                all_safety_flags.append(flag)

        # 更新安全状态
        result_context.safety_flags = all_safety_flags

        # 如果输入检测被阻止
        if input_guard.is_blocked:
            result_context.needs_human_review = True

        # 构建响应
        disclaimer = "以上内容仅供教学演示，不构成诊断或治疗建议。如需就医请咨询专业医疗机构。"

        # 审计记录中不包含原始敏感信息
        for record in audit_trail:
            record.input_summary = f"trace_id={trace_id}, {record.input_summary}"

        response = {
            "case_id": result_context.case_id,
            "trace_id": trace_id,
            "final_risk_level": result_context.final_risk_level or "LOW",
            "risk_level": result_context.final_risk_level or "LOW",
            "rule_risk_level": result_context.rule_risk_level or "LOW",
            "model_suggested_risk": result_context.model_suggested_risk,
            "model_downgrade_blocked": result_context.model_downgrade_blocked,
            "needs_human_review": result_context.needs_human_review,
            "matched_rules": result_context.matched_rules,
            "retrieved_evidence": result_context.retrieved_evidence,
            "evidence": result_context.retrieved_evidence,
            "citations": [
                {
                    "title": ev.get("title", ""),
                    "publisher": ev.get("publisher", ""),
                    "source_url": ev.get("source_url", ""),
                    "document_version": ev.get("document_version", ""),
                    "chunk_index": ev.get("chunk_index", 0),
                }
                for ev in result_context.retrieved_evidence
            ],
            "safety_flags": all_safety_flags,
            "safety_status": _determine_safety_status(result_context, input_guard.is_blocked),
            "safe_summary": result_context.safe_summary,
            "sanitized_input": sanitized_free_text,
            "symptom_summary": result_context.symptom_summary,
            "red_flags": result_context.red_flags,
            "missing_information": result_context.missing_fields,
            "followup_questions": result_context.followup_questions,
            "disclaimer": disclaimer,
            "agent_trace": [record.model_dump() for record in audit_trail],
            "ruleset_version": result_context.ruleset_version or self._rule_engine.ruleset_version,
            "model_version": settings.MODEL_VERSION,
            "prompt_version": settings.PROMPT_VERSION,
            "knowledge_base_version": settings.SAFETY_RULESET_VERSION,
        }

        return response


def _determine_safety_status(context: AgentContext, input_blocked: bool = False) -> str:
    """根据安全标记确定安全状态"""
    if input_blocked:
        return "blocked"
    blocked_flags = {
        "contains_definitive_diagnosis",
        "contains_prescription_or_dosage",
        "cancel_human_review_detected",
        "prompt_injection_detected",
        "system_prompt_extraction_detected",
        "privilege_escalation_detected",
        "human_review_bypass_detected",
    }
    if blocked_flags & set(context.safety_flags):
        return "blocked"
    if context.needs_human_review:
        return "human_review"
    return "pass"
