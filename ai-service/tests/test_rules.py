"""
合成安全规则引擎测试

覆盖：单红旗命中、多红旗取最高、HIGH/CRITICAL 强制人工审核、
无红旗低风险、规则匹配逻辑。
"""

import pytest

from app.rules.engine import SafetyRuleEngine
from app.rules.models import RiskLevel, Ruleset, SafetyRule, MatchConditions


@pytest.fixture
def engine():
    """创建使用默认合成规则的引擎"""
    return SafetyRuleEngine()


class TestSingleRedFlag:
    """单个红旗命中测试"""

    def test_consciousness_change_critical(self, engine: SafetyRuleEngine):
        """意识状态变化应命中 CRITICAL"""
        result = engine.evaluate(red_flags=["consciousness_change"], free_text="")
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.needs_human_review is True
        assert len(result.matched_rules) >= 1
        assert any(r.rule_id == "consciousness_change" for r in result.matched_rules)

    def test_severe_breathing_critical(self, engine: SafetyRuleEngine):
        """严重呼吸困难应命中 CRITICAL"""
        result = engine.evaluate(red_flags=["severe_breathing_difficulty"], free_text="")
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.needs_human_review is True

    def test_persistent_chest_high(self, engine: SafetyRuleEngine):
        """持续胸部不适应命中 HIGH"""
        result = engine.evaluate(red_flags=["persistent_chest_discomfort"], free_text="")
        assert result.risk_level == RiskLevel.HIGH
        assert result.needs_human_review is True

    def test_pregnancy_emergency_high(self, engine: SafetyRuleEngine):
        """孕产紧急信号应命中 HIGH"""
        result = engine.evaluate(red_flags=["pregnancy_emergency_signal"], free_text="")
        assert result.risk_level == RiskLevel.HIGH
        assert result.needs_human_review is True

    def test_keyword_match(self, engine: SafetyRuleEngine):
        """关键词匹配应触发规则"""
        result = engine.evaluate(red_flags=[], free_text="患者出现意识模糊")
        assert result.risk_level == RiskLevel.CRITICAL
        assert len(result.matched_rules) >= 1


class TestMultipleRedFlags:
    """多红旗取最高风险测试"""

    def test_high_and_critical_takes_critical(self, engine: SafetyRuleEngine):
        """同时命中 HIGH 和 CRITICAL 时取 CRITICAL"""
        result = engine.evaluate(
            red_flags=["persistent_chest_discomfort", "consciousness_change"],
            free_text="",
        )
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.needs_human_review is True

    def test_multiple_critical(self, engine: SafetyRuleEngine):
        """多个 CRITICAL 命中"""
        result = engine.evaluate(
            red_flags=["consciousness_change", "severe_breathing_difficulty", "uncontrolled_bleeding"],
            free_text="",
        )
        assert result.risk_level == RiskLevel.CRITICAL
        assert len(result.matched_rules) >= 3


class TestHighCriticalForcesHumanReview:
    """HIGH/CRITICAL 强制人工审核测试"""

    def test_high_requires_human_review(self, engine: SafetyRuleEngine):
        """HIGH 风险必须需要人工审核"""
        result = engine.evaluate(red_flags=["persistent_chest_discomfort"], free_text="")
        assert result.risk_level == RiskLevel.HIGH
        assert result.needs_human_review is True

    def test_critical_requires_human_review(self, engine: SafetyRuleEngine):
        """CRITICAL 风险必须需要人工审核"""
        result = engine.evaluate(red_flags=["consciousness_change"], free_text="")
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.needs_human_review is True


class TestNoRedFlagsLowRisk:
    """无红旗的低风险用例"""

    def test_empty_input_low_risk(self, engine: SafetyRuleEngine):
        """空输入应返回 LOW"""
        result = engine.evaluate(red_flags=[], free_text="")
        assert result.risk_level == RiskLevel.LOW
        assert result.needs_human_review is False
        assert len(result.matched_rules) == 0

    def test_normal_text_low_risk(self, engine: SafetyRuleEngine):
        """正常文本无红旗应返回 LOW"""
        result = engine.evaluate(red_flags=[], free_text="今天感觉有点头疼")
        assert result.risk_level == RiskLevel.LOW
        assert result.needs_human_review is False


class TestRuleEngineMetadata:
    """规则引擎元数据测试"""

    def test_ruleset_version(self, engine: SafetyRuleEngine):
        """规则集版本正确"""
        assert engine.ruleset_version == "synthetic-1.0.0"

    def test_matched_rule_has_display_message(self, engine: SafetyRuleEngine):
        """命中规则包含展示信息"""
        result = engine.evaluate(red_flags=["consciousness_change"], free_text="")
        assert len(result.matched_rules) >= 1
        assert "合成教学示例" in result.matched_rules[0].display_message
