"""
合成医疗安全规则引擎
对输入进行确定性规则匹配，输出风险等级和命中规则

安全声明：所有规则均为合成教学示例，不构成真实临床指南。
HIGH/CRITICAL 风险必须强制人工审核，不允许语言模型下调。
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from app.rules.models import (
    MatchConditions,
    MatchedRule,
    RiskLevel,
    RuleEngineResult,
    SafetyRule,
    Ruleset,
)

logger = logging.getLogger(__name__)

# 默认规则文件路径
_DEFAULT_RULES_PATH = Path(__file__).parent / "data" / "synthetic_rules_v1.json"


class SafetyRuleEngine:
    """
    合成安全规则引擎
    执行确定性规则匹配，返回风险等级和命中规则
    """

    def __init__(self, ruleset: Optional[Ruleset] = None, rules_path: Optional[str] = None):
        """
        初始化规则引擎

        Args:
            ruleset: 直接传入的规则集（优先使用）
            rules_path: 规则文件路径（ruleset 为 None 时使用）
        """
        if ruleset is not None:
            self._ruleset = ruleset
        else:
            path = Path(rules_path) if rules_path else _DEFAULT_RULES_PATH
            self._ruleset = self._load_ruleset(path)

        # 按优先级降序排列，高优先级规则先匹配
        self._rules = sorted(
            self._ruleset.rules, key=lambda r: r.priority, reverse=True
        )

    @staticmethod
    def _load_ruleset(path: Path) -> Ruleset:
        """从 JSON 文件加载规则集"""
        if not path.exists():
            raise FileNotFoundError(f"规则文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return Ruleset(**data)

    @property
    def ruleset_version(self) -> str:
        """返回规则集版本"""
        return self._ruleset.ruleset_version

    def evaluate(
        self,
        red_flags: List[str],
        free_text: str,
    ) -> RuleEngineResult:
        """
        执行规则评估

        Args:
            red_flags: 红旗标识列表
            free_text: 自由文本（用于关键词匹配）

        Returns:
            规则引擎执行结果
        """
        matched: List[MatchedRule] = []

        for rule in self._rules:
            if self._match_rule(rule, red_flags, free_text):
                matched.append(
                    MatchedRule(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        risk_level=rule.risk_level,
                        display_message=rule.display_message,
                        priority=rule.priority,
                    )
                )

        # 取最高等级
        if matched:
            highest = max(matched, key=lambda m: m.risk_level.severity)
            risk_level = highest.risk_level
        else:
            risk_level = RiskLevel.LOW

        # HIGH 或 CRITICAL 必须人工审核
        needs_human_review = risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

        logger.info(
            "规则评估完成。命中规则数=%d, 最高风险=%s, 需人工审核=%s",
            len(matched),
            risk_level.value,
            needs_human_review,
        )

        return RuleEngineResult(
            risk_level=risk_level,
            needs_human_review=needs_human_review,
            matched_rules=matched,
            ruleset_version=self._ruleset.ruleset_version,
        )

    @staticmethod
    def _match_rule(
        rule: SafetyRule,
        red_flags: List[str],
        free_text: str,
    ) -> bool:
        """
        检查单条规则是否匹配

        匹配逻辑：红旗标识任一命中 OR 关键词任一命中
        """
        conditions = rule.match_conditions

        # 检查红旗标识
        if conditions.red_flags:
            for flag in conditions.red_flags:
                if flag in red_flags:
                    return True

        # 检查关键词
        if conditions.keywords and free_text:
            text_lower = free_text.lower()
            for keyword in conditions.keywords:
                if keyword.lower() in text_lower:
                    return True

        return False
