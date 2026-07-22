"""
Agent 基类和审计记录模型
所有 Agent 继承此基类，统一记录执行审计信息

安全声明：审计记录不包含思维链（chain_of_thought）或内部推理过程。
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentAuditRecord(BaseModel):
    """Agent 审计记录"""
    agent_name: str = Field(description="Agent 名称")
    status: str = Field(description="执行状态：success / error")
    input_summary: str = Field(description="输入摘要（不含敏感信息）")
    output_summary: str = Field(description="输出摘要")
    started_at: datetime = Field(description="开始时间")
    duration_ms: float = Field(description="执行耗时（毫秒）")
    rule_ids: List[str] = Field(default_factory=list, description="关联的规则标识")
    error: Optional[str] = Field(default=None, description="错误信息（如有）")


class AgentContext(BaseModel):
    """Agent 间传递的上下文"""
    case_id: str = Field(description="病例标识")
    age: Optional[int] = Field(default=None, description="年龄")
    symptoms: List[Dict[str, Any]] = Field(default_factory=list, description="症状列表")
    red_flags: List[str] = Field(default_factory=list, description="红旗标识列表")
    free_text: str = Field(default="", description="自由文本")
    model_suggested_risk: Optional[str] = Field(default=None, description="模型建议风险等级")

    # Agent 输出字段（逐步填充）
    normalized_symptoms: List[Dict[str, Any]] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    retrieved_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    rule_risk_level: Optional[str] = Field(default=None)
    final_risk_level: Optional[str] = Field(default=None)
    needs_human_review: bool = Field(default=False)
    matched_rules: List[Dict[str, Any]] = Field(default_factory=list)
    model_downgrade_blocked: bool = Field(default=False)
    safety_flags: List[str] = Field(default_factory=list)
    safe_summary: str = Field(default="")
    ruleset_version: str = Field(default="")
    # 不可信候选输出文本（仅内部审核使用，不得通过API返回）
    candidate_output_text: str = Field(default="")


class BaseAgent(ABC):
    """Agent 抽象基类"""

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def _execute(self, context: AgentContext) -> AgentContext:
        """
        子类实现的具体执行逻辑

        Args:
            context: Agent 上下文

        Returns:
            更新后的上下文
        """
        ...

    def run(self, context: AgentContext) -> tuple[AgentContext, AgentAuditRecord]:
        """
        执行 Agent 并记录审计信息

        Returns:
            (更新后的上下文, 审计记录)
        """
        started_at = datetime.now(timezone.utc)
        input_summary = self._build_input_summary(context)

        try:
            result_context = self._execute(context)
            duration_ms = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000

            output_summary = self._build_output_summary(result_context)
            rule_ids = [r.get("rule_id", "") for r in result_context.matched_rules if isinstance(r, dict)]

            audit = AgentAuditRecord(
                agent_name=self._name,
                status="success",
                input_summary=input_summary,
                output_summary=output_summary,
                started_at=started_at,
                duration_ms=round(duration_ms, 2),
                rule_ids=rule_ids,
            )

            logger.info("Agent 执行成功。name=%s, duration_ms=%.2f", self._name, audit.duration_ms)
            return result_context, audit

        except Exception as e:
            duration_ms = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000
            error_msg = f"{type(e).__name__}: {str(e)[:200]}"

            audit = AgentAuditRecord(
                agent_name=self._name,
                status="error",
                input_summary=input_summary,
                output_summary=f"执行失败: {error_msg}",
                started_at=started_at,
                duration_ms=round(duration_ms, 2),
                error=error_msg,
            )

            logger.error("Agent 执行失败。name=%s, error=%s", self._name, error_msg)
            # 返回原始上下文，不中断流程
            return context, audit

    def _build_input_summary(self, context: AgentContext) -> str:
        """构建输入摘要（不含敏感信息）"""
        parts = [f"case_id={context.case_id}"]
        if context.symptoms:
            parts.append(f"symptoms_count={len(context.symptoms)}")
        if context.red_flags:
            parts.append(f"red_flags_count={len(context.red_flags)}")
        return ", ".join(parts)

    def _build_output_summary(self, context: AgentContext) -> str:
        """构建输出摘要"""
        parts = []
        if context.rule_risk_level:
            parts.append(f"rule_risk={context.rule_risk_level}")
        if context.final_risk_level:
            parts.append(f"final_risk={context.final_risk_level}")
        if context.matched_rules:
            parts.append(f"matched_rules_count={len(context.matched_rules)}")
        if context.retrieved_evidence:
            parts.append(f"evidence_count={len(context.retrieved_evidence)}")
        return ", ".join(parts) if parts else "no_output"
