"""
RiskAssessmentAgent - 风险评估 Agent
必须先执行确定性规则引擎，模型建议不能覆盖 HIGH/CRITICAL 规则风险

安全声明：HIGH/CRITICAL 一旦由规则引擎命中，不允许语言模型将风险降低。
"""

import logging
from typing import Optional

from app.agents.base import AgentContext, BaseAgent
from app.rules.engine import SafetyRuleEngine
from app.rules.models import RiskLevel

logger = logging.getLogger(__name__)

# 风险等级名称到枚举的映射
_RISK_LEVEL_MAP = {
    "LOW": RiskLevel.LOW,
    "MEDIUM": RiskLevel.MEDIUM,
    "HIGH": RiskLevel.HIGH,
    "CRITICAL": RiskLevel.CRITICAL,
}


class RiskAssessmentAgent(BaseAgent):
    """风险评估 Agent"""

    def __init__(self, rule_engine: SafetyRuleEngine):
        super().__init__("RiskAssessmentAgent")
        self._rule_engine = rule_engine

    def _execute(self, context: AgentContext) -> AgentContext:
        """执行风险评估：规则引擎 + 模型建议（不可下调）"""
        # 第一步：执行确定性规则引擎
        rule_result = self._rule_engine.evaluate(
            red_flags=context.red_flags,
            free_text=context.free_text,
        )

        context.rule_risk_level = rule_result.risk_level.value
        context.matched_rules = [r.model_dump() for r in rule_result.matched_rules]
        context.ruleset_version = rule_result.ruleset_version
        context.needs_human_review = rule_result.needs_human_review

        # 第二步：解析模型建议的风险等级
        model_risk = self._parse_risk_level(context.model_suggested_risk)

        # 第三步：风险不可下调机制
        # 如果规则引擎给出 HIGH 或 CRITICAL，模型建议不能将其降低
        if rule_result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            # 模型试图下调风险时，阻止并记录
            if model_risk is not None and model_risk < rule_result.risk_level:
                context.model_downgrade_blocked = True
                logger.warning(
                    "模型风险下调被阻止。case_id=%s, 规则风险=%s, 模型建议=%s",
                    context.case_id,
                    rule_result.risk_level.value,
                    model_risk.value,
                )
            # 最终风险保持规则引擎的结果
            context.final_risk_level = rule_result.risk_level.value
        else:
            # 规则引擎为 LOW/MEDIUM 时，取规则和模型中的较高等级
            if model_risk is not None and model_risk > rule_result.risk_level:
                context.final_risk_level = model_risk.value
            else:
                context.final_risk_level = rule_result.risk_level.value

        logger.info(
            "风险评估完成。case_id=%s, rule_risk=%s, model_risk=%s, final_risk=%s, downgrade_blocked=%s",
            context.case_id,
            context.rule_risk_level,
            context.model_suggested_risk,
            context.final_risk_level,
            context.model_downgrade_blocked,
        )

        return context

    def _build_output_summary(self, context: AgentContext) -> str:
        """构建有意义的输出摘要"""
        parts = [f"规则风险{context.rule_risk_level or 'LOW'}"]
        if context.model_suggested_risk:
            parts.append(f"模型建议{context.model_suggested_risk}")
        if context.model_downgrade_blocked:
            parts.append("下调已阻止")
        parts.append(f"最终风险{context.final_risk_level or 'LOW'}")
        return "，".join(parts)

    @staticmethod
    def _parse_risk_level(value: Optional[str]) -> Optional[RiskLevel]:
        """解析风险等级字符串为枚举"""
        if value is None:
            return None
        return _RISK_LEVEL_MAP.get(value.upper())
