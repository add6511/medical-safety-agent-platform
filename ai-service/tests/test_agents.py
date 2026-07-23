"""
多 Agent 审核流程测试

覆盖：Agent 执行顺序、模型降级阻止、空知识库降级、
安全拦截、Agent 失败降级、审计记录不含思维链。
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.agents.base import AgentAuditRecord, AgentContext
from app.agents.intake_agent import IntakeAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.safety_agent import SafetyReviewAgent
from app.agents.supervisor import SupervisorAgent
from app.rag.embedding import MockEmbeddingProvider
from app.rag.vector_store import InMemoryVectorStore
from app.rules.engine import SafetyRuleEngine
from app.services.knowledge_service import KnowledgeService


@pytest.fixture
def knowledge_service():
    """创建知识库服务"""
    return KnowledgeService(InMemoryVectorStore(), MockEmbeddingProvider(dimension=384))


@pytest.fixture
def rule_engine():
    """创建规则引擎"""
    return SafetyRuleEngine()


@pytest.fixture
def supervisor(knowledge_service, rule_engine):
    """创建 SupervisorAgent"""
    return SupervisorAgent([
        IntakeAgent(),
        RetrievalAgent(knowledge_service),
        RiskAssessmentAgent(rule_engine),
        SafetyReviewAgent(),
    ])


def _make_context(**kwargs) -> AgentContext:
    """创建测试用上下文"""
    defaults = {
        "case_id": "test-case-001",
        "age": 45,
        "symptoms": [{"name": "胸部不适", "severity": 7, "duration": "30分钟"}],
        "red_flags": ["persistent_chest_discomfort"],
        "free_text": "合成教学病例",
        "model_suggested_risk": None,
    }
    defaults.update(kwargs)
    return AgentContext(**defaults)


class TestAgentExecutionOrder:
    """Agent 执行顺序测试"""

    def test_agents_execute_in_order(self, supervisor: SupervisorAgent):
        """验证 Agent 按 Intake → Retrieval → Risk → Safety 顺序执行"""
        context = _make_context()
        result_context, audit_trail = supervisor.process(context)

        assert len(audit_trail) == 4
        assert audit_trail[0].agent_name == "IntakeAgent"
        assert audit_trail[1].agent_name == "RetrievalAgent"
        assert audit_trail[2].agent_name == "RiskAssessmentAgent"
        assert audit_trail[3].agent_name == "SafetyReviewAgent"

    def test_all_agents_succeed(self, supervisor: SupervisorAgent):
        """所有 Agent 成功执行"""
        context = _make_context()
        _, audit_trail = supervisor.process(context)

        for record in audit_trail:
            assert record.status == "success"
            assert record.duration_ms >= 0


class TestModelDowngradeBlocked:
    """模型降级阻止测试"""

    def test_model_low_cannot_downgrade_rule_high(self, supervisor: SupervisorAgent):
        """模型建议 LOW 不能降低规则 HIGH"""
        context = _make_context(
            red_flags=["persistent_chest_discomfort"],
            model_suggested_risk="LOW",
        )
        result, _ = supervisor.process(context)

        assert result.rule_risk_level == "HIGH"
        assert result.final_risk_level == "HIGH"
        assert result.model_downgrade_blocked is True

    def test_model_low_cannot_downgrade_rule_critical(self, supervisor: SupervisorAgent):
        """模型建议 LOW 不能降低规则 CRITICAL"""
        context = _make_context(
            red_flags=["consciousness_change"],
            model_suggested_risk="LOW",
        )
        result, _ = supervisor.process(context)

        assert result.rule_risk_level == "CRITICAL"
        assert result.final_risk_level == "CRITICAL"
        assert result.model_downgrade_blocked is True

    def test_model_medium_cannot_downgrade_critical(self, supervisor: SupervisorAgent):
        """模型建议 MEDIUM 不能降低规则 CRITICAL"""
        context = _make_context(
            red_flags=["severe_breathing_difficulty"],
            model_suggested_risk="MEDIUM",
        )
        result, _ = supervisor.process(context)

        assert result.rule_risk_level == "CRITICAL"
        assert result.final_risk_level == "CRITICAL"
        assert result.model_downgrade_blocked is True


class TestEmptyKnowledgeBase:
    """空知识库优雅降级测试"""

    def test_empty_knowledge_base_no_crash(self, supervisor: SupervisorAgent):
        """知识库为空时不应崩溃"""
        context = _make_context()
        result, audit_trail = supervisor.process(context)

        # 应正常完成
        assert result.final_risk_level is not None
        assert len(audit_trail) == 4

        # RetrievalAgent 应成功（优雅降级）
        retrieval_audit = audit_trail[1]
        assert retrieval_audit.agent_name == "RetrievalAgent"
        assert retrieval_audit.status == "success"

        # 检索结果为空
        assert len(result.retrieved_evidence) == 0


class TestSafetyAgent:
    """安全审核 Agent 测试"""

    def test_definitive_diagnosis_intercepted(self, rule_engine: SafetyRuleEngine):
        """确定性诊断文本应被拦截"""
        context = _make_context(red_flags=[], free_text="普通症状")
        context.final_risk_level = "LOW"
        context.matched_rules = [{"rule_id": "test", "display_message": "你就是得了心脏病", "risk_level": "LOW", "name": "test", "priority": 1}]
        context.retrieved_evidence = []

        agent = SafetyReviewAgent()
        result = agent._execute(context)

        assert "contains_definitive_diagnosis" in result.safety_flags

    def test_prescription_dosage_intercepted(self):
        """药物剂量文本应被拦截"""
        context = _make_context()
        context.final_risk_level = "LOW"
        context.matched_rules = [{"rule_id": "test", "display_message": "建议服用阿莫西林 500mg", "risk_level": "LOW", "name": "test", "priority": 1}]
        context.retrieved_evidence = []

        agent = SafetyReviewAgent()
        result = agent._execute(context)

        assert "contains_prescription_or_dosage" in result.safety_flags

    def test_high_risk_missing_human_review_corrected(self):
        """高风险缺少人工审核时应被安全审核纠正"""
        context = _make_context()
        context.final_risk_level = "HIGH"
        context.needs_human_review = False  # 故意设为 False
        context.matched_rules = []
        context.retrieved_evidence = []

        agent = SafetyReviewAgent()
        result = agent._execute(context)

        assert "high_risk_missing_human_review" in result.safety_flags
        assert result.needs_human_review is True

    def test_disclaimer_always_present(self):
        """免责声明始终存在"""
        context = _make_context()
        context.final_risk_level = "LOW"
        context.matched_rules = []
        context.retrieved_evidence = []

        agent = SafetyReviewAgent()
        result = agent._execute(context)

        assert "不构成诊断" in result.safe_summary or "教学" in result.safe_summary


class TestAgentFailureFallback:
    """Agent 失败安全降级测试"""

    def test_agent_error_returns_safe_fallback(self):
        """Agent 执行出错时返回安全降级结果"""

        class FailingAgent(IntakeAgent):
            def _execute(self, context):
                raise RuntimeError("模拟失败")

        agent = FailingAgent()
        context = _make_context()
        result_context, audit = agent.run(context)

        # 应返回原始上下文
        assert result_context.case_id == context.case_id
        # 审计记录标记为错误
        assert audit.status == "error"
        assert "RuntimeError" in audit.error


class TestAgentTraceNoChainOfThought:
    """agent_trace 不包含思维链测试"""

    def test_audit_no_chain_of_thought(self, supervisor: SupervisorAgent):
        """审计记录不包含 chain_of_thought 字段"""
        context = _make_context()
        _, audit_trail = supervisor.process(context)

        for record in audit_trail:
            record_dict = record.model_dump()
            assert "chain_of_thought" not in record_dict
            assert "reasoning" not in record_dict
            assert "internal_thought" not in record_dict

    def test_audit_record_fields(self, supervisor: SupervisorAgent):
        """审计记录包含必要字段"""
        context = _make_context()
        _, audit_trail = supervisor.process(context)

        required_fields = [
            "agent_name", "status", "input_summary",
            "output_summary", "started_at", "duration_ms",
        ]
        for record in audit_trail:
            record_dict = record.model_dump()
            for field in required_fields:
                assert field in record_dict, f"缺少字段: {field}"


class TestIntakeAgent:
    """IntakeAgent 单元测试"""

    def test_normalize_symptoms(self):
        """症状规范化"""
        agent = IntakeAgent()
        context = _make_context(
            symptoms=[
                {"name": " 头痛 ", "severity": 15, "duration": " 2小时 "},
                {"name": "", "severity": 5, "duration": ""},
            ]
        )
        result = agent._execute(context)

        assert len(result.normalized_symptoms) == 1
        assert result.normalized_symptoms[0]["name"] == "头痛"
        assert result.normalized_symptoms[0]["severity"] == 10  # 上限为10

    def test_identify_missing_fields(self):
        """识别缺失字段"""
        agent = IntakeAgent()
        context = _make_context(age=None, symptoms=[], free_text="")
        result = agent._execute(context)

        assert "age" in result.missing_fields
        assert "symptoms" in result.missing_fields
        assert "free_text" in result.missing_fields

    def test_filter_invalid_red_flags(self):
        """过滤无效红旗标识"""
        agent = IntakeAgent()
        context = _make_context(red_flags=["invalid_flag", "consciousness_change"])
        result = agent._execute(context)

        assert "invalid_flag" not in result.red_flags
        assert "consciousness_change" in result.red_flags
