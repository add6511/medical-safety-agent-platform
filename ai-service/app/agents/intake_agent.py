"""
IntakeAgent - 输入校验与规范化 Agent
校验和规范化输入，识别症状、红旗选项和缺失字段，不做诊断
"""

from typing import Any, Dict, List

from app.agents.base import AgentContext, BaseAgent

# 合法的红旗标识列表（与规则引擎保持一致）
VALID_RED_FLAGS = {
    "consciousness_change",
    "severe_breathing_difficulty",
    "persistent_chest_discomfort",
    "uncontrolled_bleeding",
    "self_harm_risk",
    "pregnancy_emergency_signal",
}


class IntakeAgent(BaseAgent):
    """输入校验与规范化 Agent"""

    def __init__(self):
        super().__init__("IntakeAgent")

    def _execute(self, context: AgentContext) -> AgentContext:
        """校验和规范化输入"""
        # 规范化症状
        normalized: List[Dict[str, Any]] = []
        for symptom in context.symptoms:
            name = str(symptom.get("name", "")).strip()
            severity = symptom.get("severity", 0)
            duration = str(symptom.get("duration", "")).strip()

            if not name:
                continue

            # 规范化严重程度到 0-10 范围
            try:
                severity = max(0, min(10, int(severity)))
            except (ValueError, TypeError):
                severity = 0

            normalized.append({
                "name": name,
                "severity": severity,
                "duration": duration,
            })

        context.normalized_symptoms = normalized

        # 识别缺失字段
        missing: List[str] = []
        if not context.age or context.age <= 0:
            missing.append("age")
        if not normalized:
            missing.append("symptoms")
        if not context.free_text.strip():
            missing.append("free_text")

        context.missing_fields = missing

        # 过滤无效红旗标识（保留合法的）
        context.red_flags = [f for f in context.red_flags if f in VALID_RED_FLAGS]

        return context
