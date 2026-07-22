"""
规则引擎数据模型
定义风险等级、规则结构和规则匹配结果

安全声明：所有规则均为合成教学示例，不构成真实临床指南。
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """风险等级枚举，按严重程度递增"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def severity(self) -> int:
        """返回风险严重程度数值，用于比较"""
        return {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3,
        }[self]

    def __ge__(self, other: "RiskLevel") -> bool:
        return self.severity >= other.severity

    def __gt__(self, other: "RiskLevel") -> bool:
        return self.severity > other.severity

    def __le__(self, other: "RiskLevel") -> bool:
        return self.severity <= other.severity

    def __lt__(self, other: "RiskLevel") -> bool:
        return self.severity < other.severity


class MatchConditions(BaseModel):
    """规则匹配条件"""
    red_flags: List[str] = Field(
        default_factory=list,
        description="需要命中的红旗标识列表（任一命中即触发）",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="需要在文本中匹配的关键词列表（任一命中即触发）",
    )


class SafetyRule(BaseModel):
    """合成安全规则定义"""
    rule_id: str = Field(description="规则唯一标识")
    name: str = Field(description="规则名称")
    version: str = Field(description="规则版本")
    priority: int = Field(description="优先级，数值越大优先级越高")
    risk_level: RiskLevel = Field(description="该规则对应的风险等级")
    match_conditions: MatchConditions = Field(description="匹配条件")
    display_message: str = Field(description="命中时展示给用户的信息")
    synthetic_source: str = Field(description="合成来源说明")


class Ruleset(BaseModel):
    """规则集"""
    ruleset_version: str = Field(description="规则集版本")
    description: str = Field(default="", description="规则集描述")
    rules: List[SafetyRule] = Field(description="规则列表")


class MatchedRule(BaseModel):
    """已命中的规则"""
    rule_id: str = Field(description="规则标识")
    name: str = Field(description="规则名称")
    risk_level: RiskLevel = Field(description="风险等级")
    display_message: str = Field(description="展示信息")
    priority: int = Field(description="优先级")


class RuleEngineResult(BaseModel):
    """规则引擎执行结果"""
    risk_level: RiskLevel = Field(description="最终风险等级（取最高等级）")
    needs_human_review: bool = Field(description="是否需要人工审核")
    matched_rules: List[MatchedRule] = Field(description="命中的规则列表")
    ruleset_version: str = Field(description="规则集版本")
