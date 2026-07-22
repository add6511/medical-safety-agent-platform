"""
预问诊审核服务
协调 SupervisorAgent 和各子 Agent，返回统一审核结果

安全声明：本服务仅供教学演示，不提供真实诊断或替代医生。
"""

import logging
from typing import Any, Dict, List

from app.agents.base import AgentContext
from app.agents.intake_agent import IntakeAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.safety_agent import SafetyReviewAgent
from app.agents.supervisor import SupervisorAgent
from app.core.config import settings
from app.rules.engine import SafetyRuleEngine
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


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
        # 构建 Agent 上下文
        context = AgentContext(
            case_id=request_data.get("case_id", "unknown"),
            age=request_data.get("age"),
            symptoms=[s if isinstance(s, dict) else s.model_dump() for s in request_data.get("symptoms", [])],
            red_flags=request_data.get("red_flags", []),
            free_text=request_data.get("free_text", ""),
            model_suggested_risk=request_data.get("model_suggested_risk"),
        )

        # 执行审核流程
        result_context, audit_trail = self._supervisor.process(context)

        # 构建响应
        disclaimer = "以上内容仅供教学演示，不构成诊断或治疗建议。如需就医请咨询专业医疗机构。"

        response = {
            "case_id": result_context.case_id,
            "final_risk_level": result_context.final_risk_level or "LOW",
            "rule_risk_level": result_context.rule_risk_level or "LOW",
            "model_suggested_risk": result_context.model_suggested_risk,
            "model_downgrade_blocked": result_context.model_downgrade_blocked,
            "needs_human_review": result_context.needs_human_review,
            "matched_rules": result_context.matched_rules,
            "retrieved_evidence": result_context.retrieved_evidence,
            "safety_flags": result_context.safety_flags,
            "safe_summary": result_context.safe_summary,
            "disclaimer": disclaimer,
            "agent_trace": [record.model_dump() for record in audit_trail],
            "ruleset_version": result_context.ruleset_version or self._rule_engine.ruleset_version,
            "model_version": settings.MODEL_VERSION,
            "prompt_version": settings.PROMPT_VERSION,
            "knowledge_base_version": settings.SAFETY_RULESET_VERSION,
        }

        return response
