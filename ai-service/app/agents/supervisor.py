"""
SupervisorAgent - 审核流程协调器
按 Intake → Retrieval → RiskAssessment → SafetyReview 顺序协调各 Agent
返回统一审核结果和完整审计记录
"""

import logging
from typing import List

from app.agents.base import AgentAuditRecord, AgentContext, BaseAgent

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    审核流程协调器
    按固定顺序执行各 Agent，收集审计记录
    """

    def __init__(self, agents: List[BaseAgent]):
        """
        初始化协调器

        Args:
            agents: 按执行顺序排列的 Agent 列表
                    [IntakeAgent, RetrievalAgent, RiskAssessmentAgent, SafetyReviewAgent]
        """
        self._agents = agents

    def process(self, context: AgentContext) -> tuple[AgentContext, List[AgentAuditRecord]]:
        """
        执行完整审核流程

        Args:
            context: 初始上下文

        Returns:
            (最终上下文, 审计记录列表)
        """
        audit_trail: List[AgentAuditRecord] = []

        for agent in self._agents:
            logger.info("开始执行 Agent: %s, case_id=%s", agent.name, context.case_id)
            context, audit = agent.run(context)
            audit_trail.append(audit)

            # 如果 Agent 执行出错，记录但继续执行后续 Agent
            if audit.status == "error":
                logger.warning(
                    "Agent 执行出错，继续后续流程。agent=%s, error=%s",
                    agent.name,
                    audit.error,
                )

        logger.info(
            "审核流程完成。case_id=%s, agents_executed=%d, final_risk=%s",
            context.case_id,
            len(audit_trail),
            context.final_risk_level,
        )

        return context, audit_trail
