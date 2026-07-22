"""
SafetyReviewAgent - 安全审核 Agent
检查输出是否包含确定性诊断、药物处方、具体剂量等不安全内容
对不安全文本进行拦截或替换

安全声明：本 Agent 使用可解释的关键字和正则规则进行安全检查，
仅为课程安全演示，不得描述为真实医疗标准。
"""

import logging
import re
from typing import List

from app.agents.base import AgentContext, BaseAgent

logger = logging.getLogger(__name__)

# 确定性诊断表述模式
_DIAGNOSIS_PATTERNS = [
    re.compile(r"你(就是|得了|患有|确诊为)\s*\S+病", re.IGNORECASE),
    re.compile(r"(诊断|确诊)(为|是)\s*\S+", re.IGNORECASE),
    re.compile(r"你(一定|肯定|必然)(是|得了)\s*\S+", re.IGNORECASE),
]

# 药物处方和剂量模式
_PRESCRIPTION_PATTERNS = [
    re.compile(r"(开|服用|吃|口服|注射)\s*\S+\s*\d+\s*(mg|ml|g|片|粒|支)", re.IGNORECASE),
    re.compile(r"(处方|医嘱).*\S+\s*\d+\s*(mg|ml|g)", re.IGNORECASE),
    re.compile(r"(每天|每日|一日)\s*\d+\s*次.*\d+\s*(mg|ml|g|片)", re.IGNORECASE),
    re.compile(r"\d+\s*(mg|ml|g)\s*(的|每次|每日)", re.IGNORECASE),
]

# 免责声明关键词
_DISCLAIMER_KEYWORDS = ["仅供教学", "不构成诊断", "不构成治疗建议", "不代表医疗建议"]


class SafetyReviewAgent(BaseAgent):
    """安全审核 Agent"""

    def __init__(self):
        super().__init__("SafetyReviewAgent")

    def _execute(self, context: AgentContext) -> AgentContext:
        """执行安全审核"""
        flags: List[str] = []

        # 构建待审核文本（安全摘要）
        summary_parts = []
        if context.final_risk_level:
            summary_parts.append(f"风险等级: {context.final_risk_level}")
        if context.matched_rules:
            for rule in context.matched_rules:
                msg = rule.get("display_message", "")
                if msg:
                    summary_parts.append(msg)
        if context.retrieved_evidence:
            for ev in context.retrieved_evidence[:3]:
                title = ev.get("title", "")
                if title:
                    summary_parts.append(f"参考: {title}")

        candidate_text = "\n".join(summary_parts)

        # 检查确定性诊断表述
        for pattern in _DIAGNOSIS_PATTERNS:
            if pattern.search(candidate_text):
                flags.append("contains_definitive_diagnosis")
                # 替换不安全文本
                candidate_text = pattern.sub("[已拦截: 不允许确定性诊断表述]", candidate_text)
                break

        # 检查药物处方或具体剂量
        for pattern in _PRESCRIPTION_PATTERNS:
            if pattern.search(candidate_text):
                flags.append("contains_prescription_or_dosage")
                candidate_text = pattern.sub("[已拦截: 不允许药物处方或具体剂量]", candidate_text)
                break

        # 检查高风险是否要求人工审核
        if context.final_risk_level in ("HIGH", "CRITICAL") and not context.needs_human_review:
            flags.append("high_risk_missing_human_review")
            context.needs_human_review = True

        # 检查引用字段完整性
        if context.retrieved_evidence:
            required_fields = ["chunk_id", "title", "publisher", "source_url"]
            for ev in context.retrieved_evidence:
                for field_name in required_fields:
                    if not ev.get(field_name):
                        flags.append("missing_citation_field")
                        break

        # 检查免责声明
        has_disclaimer = any(kw in candidate_text for kw in _DISCLAIMER_KEYWORDS)
        if not has_disclaimer:
            # 添加免责声明
            candidate_text += "\n\n【声明】以上内容仅供教学演示，不构成诊断或治疗建议。"

        context.safety_flags = flags
        context.safe_summary = candidate_text

        logger.info(
            "安全审核完成。case_id=%s, flags=%s",
            context.case_id,
            flags,
        )

        return context
