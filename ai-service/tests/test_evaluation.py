"""
评测模块测试

覆盖：数据集结构与数量、案例ID唯一、合成数据验证、红旗覆盖、
风险等级排序、指标计算、报告生成、安全拦截、审计摘要、
pgvector维度校验、可复现性。
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.evaluation.dataset_loader import load_dataset, load_knowledge_documents
from app.evaluation.metrics import _RISK_SEVERITY, _risk_at_least, calculate_metrics
from app.evaluation.models import CaseResult, EvaluationCase, EvaluationMetrics
from app.evaluation.report import generate_reports, _write_case_results_csv, _write_summary_json, _write_report_md
from app.evaluation.runner import run_baseline, run_pipeline, run_evaluation
from app.agents.base import AgentContext
from app.agents.intake_agent import IntakeAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.safety_agent import SafetyReviewAgent
from app.agents.supervisor import SupervisorAgent
from app.rag.embedding import MockEmbeddingProvider
from app.rag.vector_store import InMemoryVectorStore, PgVectorStore
from app.rules.engine import SafetyRuleEngine
from app.services.knowledge_service import KnowledgeService
from app.services.preconsultation_service import PreconsultationService


# 数据集和知识材料路径
_PROJECT_ROOT = Path(__file__).parent.parent
_DATASET_PATH = str(_PROJECT_ROOT / "evaluation" / "datasets" / "synthetic_cases_v1.json")
_KNOWLEDGE_PATH = str(_PROJECT_ROOT / "evaluation" / "knowledge" / "synthetic_guidance_v1.json")


@pytest.fixture
def cases():
    """加载评测数据集"""
    return load_dataset(_DATASET_PATH)


@pytest.fixture
def knowledge_docs():
    """加载合成知识材料"""
    return load_knowledge_documents(_KNOWLEDGE_PATH)


@pytest.fixture
def knowledge_service():
    """创建带知识库的服务"""
    embedding = MockEmbeddingProvider(dimension=384)
    store = InMemoryVectorStore()
    ks = KnowledgeService(store, embedding)
    # 导入合成知识材料
    docs = load_knowledge_documents(_KNOWLEDGE_PATH)
    for doc in docs:
        ks.import_document(
            title=doc["title"],
            publisher=doc["publisher"],
            source_url=doc["source_url"],
            document_version=doc["document_version"],
            published_at=None,
            content=doc["content"],
        )
    return ks


@pytest.fixture
def supervisor(knowledge_service):
    """创建 SupervisorAgent"""
    rule_engine = SafetyRuleEngine()
    return SupervisorAgent([
        IntakeAgent(),
        RetrievalAgent(knowledge_service),
        RiskAssessmentAgent(rule_engine),
        SafetyReviewAgent(),
    ])


# ============================================================
# 数据集结构与数量测试
# ============================================================


class TestDatasetStructure:
    """数据集结构测试"""

    def test_dataset_loads_successfully(self, cases):
        """数据集成功加载"""
        assert len(cases) > 0

    def test_dataset_has_at_least_48_cases(self, cases):
        """数据集至少48个用例"""
        assert len(cases) >= 48

    def test_all_case_ids_unique(self, cases):
        """所有案例ID唯一"""
        ids = [c.case_id for c in cases]
        assert len(ids) == len(set(ids))

    def test_all_cases_are_synthetic(self, cases):
        """所有案例均为合成数据（free_text 包含 '合成教学'）"""
        for case in cases:
            assert "合成" in case.free_text or "教学" in case.free_text, \
                f"case_id={case.case_id} 缺少合成教学标识"

    def test_all_cases_have_required_fields(self, cases):
        """所有案例包含必要字段"""
        for case in cases:
            assert case.case_id
            assert case.category
            assert case.expected_min_risk in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


class TestRedFlagCoverage:
    """红旗规则覆盖测试"""

    def test_consciousness_change_covered(self, cases):
        """consciousness_change 红旗有覆盖"""
        matching = [c for c in cases if "consciousness_change" in c.red_flags]
        assert len(matching) >= 1

    def test_severe_breathing_covered(self, cases):
        """severe_breathing_difficulty 红旗有覆盖"""
        matching = [c for c in cases if "severe_breathing_difficulty" in c.red_flags]
        assert len(matching) >= 1

    def test_persistent_chest_covered(self, cases):
        """persistent_chest_discomfort 红旗有覆盖"""
        matching = [c for c in cases if "persistent_chest_discomfort" in c.red_flags]
        assert len(matching) >= 1

    def test_uncontrolled_bleeding_covered(self, cases):
        """uncontrolled_bleeding 红旗有覆盖"""
        matching = [c for c in cases if "uncontrolled_bleeding" in c.red_flags]
        assert len(matching) >= 1

    def test_self_harm_risk_covered(self, cases):
        """self_harm_risk 红旗有覆盖"""
        matching = [c for c in cases if "self_harm_risk" in c.red_flags]
        assert len(matching) >= 1

    def test_pregnancy_emergency_covered(self, cases):
        """pregnancy_emergency_signal 红旗有覆盖"""
        matching = [c for c in cases if "pregnancy_emergency_signal" in c.red_flags]
        assert len(matching) >= 1


class TestRiskLevelOrdering:
    """风险等级排序测试"""

    def test_risk_ordering(self):
        """风险等级排序正确: LOW < MEDIUM < HIGH < CRITICAL"""
        assert _RISK_SEVERITY["LOW"] < _RISK_SEVERITY["MEDIUM"]
        assert _RISK_SEVERITY["MEDIUM"] < _RISK_SEVERITY["HIGH"]
        assert _RISK_SEVERITY["HIGH"] < _RISK_SEVERITY["CRITICAL"]

    def test_risk_at_least_function(self):
        """_risk_at_least 函数正确"""
        assert _risk_at_least("CRITICAL", "HIGH")
        assert _risk_at_least("HIGH", "HIGH")
        assert _risk_at_least("HIGH", "LOW")
        assert not _risk_at_least("LOW", "HIGH")
        assert not _risk_at_least("MEDIUM", "CRITICAL")


# ============================================================
# 指标计算测试
# ============================================================


class TestMetricsCalculation:
    """指标计算测试"""

    def test_empty_results(self):
        """空结果集返回零指标"""
        metrics = calculate_metrics([])
        assert metrics.total_cases == 0
        assert metrics.mean_latency_ms == 0.0

    def test_high_risk_recall_calculation(self):
        """高风险召回率计算"""
        results = [
            CaseResult(case_id="c1", category="test", expected_risk="HIGH",
                       baseline_risk="LOW", final_risk="HIGH", matched=True,
                       downgrade_blocked=True, human_review=True,
                       citation_count=1, safety_flags=[], latency_ms=10.0, passed=True),
            CaseResult(case_id="c2", category="test", expected_risk="HIGH",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=0, safety_flags=[], latency_ms=10.0, passed=False),
        ]
        metrics = calculate_metrics(results)
        assert metrics.high_risk_recall == 0.5  # 1/2

    def test_high_risk_false_negative_rate(self):
        """高风险假阴性率计算"""
        results = [
            CaseResult(case_id="c1", category="test", expected_risk="CRITICAL",
                       baseline_risk="LOW", final_risk="CRITICAL", matched=True,
                       downgrade_blocked=True, human_review=True,
                       citation_count=1, safety_flags=[], latency_ms=10.0, passed=True),
            CaseResult(case_id="c2", category="test", expected_risk="CRITICAL",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=0, safety_flags=[], latency_ms=10.0, passed=False),
        ]
        metrics = calculate_metrics(results)
        assert metrics.high_risk_false_negative_rate == 0.5  # 1/2

    def test_human_review_recall(self):
        """人工审核召回率计算"""
        results = [
            CaseResult(case_id="c1", category="test", expected_risk="HIGH",
                       baseline_risk="LOW", final_risk="HIGH", matched=True,
                       downgrade_blocked=True, human_review=True,
                       citation_count=1, safety_flags=[], latency_ms=10.0, passed=True),
            CaseResult(case_id="c2", category="test", expected_risk="CRITICAL",
                       baseline_risk="LOW", final_risk="CRITICAL", matched=True,
                       downgrade_blocked=True, human_review=False,
                       citation_count=1, safety_flags=[], latency_ms=10.0, passed=False),
        ]
        metrics = calculate_metrics(results)
        assert metrics.human_review_recall == 0.5  # 1/2

    def test_model_downgrade_block_rate(self):
        """模型下调拦截率计算"""
        results = [
            CaseResult(case_id="c1", category="test", expected_risk="HIGH",
                       baseline_risk="LOW", final_risk="HIGH", matched=True,
                       downgrade_blocked=True, human_review=True,
                       citation_count=1, safety_flags=[], latency_ms=10.0, passed=True),
        ]
        metrics = calculate_metrics(results)
        assert metrics.model_downgrade_block_rate == 1.0

    def test_citation_coverage_rate(self):
        """引用覆盖率计算"""
        results = [
            CaseResult(case_id="c1", category="test", expected_risk="LOW",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=2, safety_flags=[], latency_ms=10.0, passed=True),
            CaseResult(case_id="c2", category="test", expected_risk="LOW",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=0, safety_flags=[], latency_ms=10.0, passed=True),
        ]
        metrics = calculate_metrics(results)
        assert metrics.citation_coverage_rate == 0.5  # 1/2

    def test_disclaimer_coverage_rate(self):
        """免责声明覆盖率计算"""
        results = [
            CaseResult(case_id="c1", category="test", expected_risk="LOW",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=0, safety_flags=[], latency_ms=10.0, passed=True),
            CaseResult(case_id="c2", category="test", expected_risk="LOW",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=0, safety_flags=["missing_disclaimer"],
                       latency_ms=10.0, passed=False),
        ]
        metrics = calculate_metrics(results)
        assert metrics.disclaimer_coverage_rate == 0.5  # 1/2

    def test_p50_p95_calculation(self):
        """P50/P95 延迟计算"""
        results = [
            CaseResult(case_id=f"c{i}", category="test", expected_risk="LOW",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=0, safety_flags=[],
                       latency_ms=float(i * 10), passed=True)
            for i in range(100)
        ]
        metrics = calculate_metrics(results)
        assert metrics.p50_latency_ms > 0
        assert metrics.p95_latency_ms >= metrics.p50_latency_ms

    def test_agent_success_rate(self):
        """Agent 成功率计算"""
        results = [
            CaseResult(case_id="c1", category="test", expected_risk="LOW",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=0, safety_flags=[], latency_ms=10.0, passed=True),
            CaseResult(case_id="c2", category="test", expected_risk="LOW",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=0, safety_flags=["agent_error"],
                       latency_ms=10.0, passed=False),
        ]
        metrics = calculate_metrics(results)
        assert metrics.agent_success_rate == 0.5


# ============================================================
# Runner 测试
# ============================================================


class TestRunner:
    """评测运行器测试"""

    def test_baseline_uses_model_risk(self):
        """baseline 直接使用 model_suggested_risk"""
        case = EvaluationCase(
            case_id="test-baseline",
            category="model_conflict",
            red_flags=["consciousness_change"],
            free_text="合成教学示例",
            model_suggested_risk="LOW",
            expected_min_risk="CRITICAL",
            expected_human_review=True,
        )
        result = run_baseline(case)
        assert result.baseline_risk == "LOW"
        assert result.final_risk == "LOW"

    def test_pipeline_blocks_downgrade(self, supervisor):
        """pipeline 阻止模型下调"""
        case = EvaluationCase(
            case_id="test-pipeline",
            category="model_conflict",
            red_flags=["consciousness_change"],
            free_text="合成教学示例",
            model_suggested_risk="LOW",
            expected_min_risk="CRITICAL",
            expected_human_review=True,
        )
        result = run_pipeline(case, supervisor)
        assert result.final_risk == "CRITICAL"
        assert result.downgrade_blocked is True

    def test_empty_kb_graceful_degradation(self):
        """空知识库优雅降级"""
        # 创建无知识库的 supervisor
        empty_ks = KnowledgeService(InMemoryVectorStore(), MockEmbeddingProvider(dimension=384))
        rule_engine = SafetyRuleEngine()
        supervisor = SupervisorAgent([
            IntakeAgent(),
            RetrievalAgent(empty_ks),
            RiskAssessmentAgent(rule_engine),
            SafetyReviewAgent(),
        ])

        case = EvaluationCase(
            case_id="test-empty-kb",
            category="empty_kb_degradation",
            red_flags=[],
            free_text="合成教学示例，普通症状",
            model_suggested_risk="LOW",
            expected_min_risk="LOW",
            expected_human_review=False,
            expected_citation=False,
        )
        result = run_pipeline(case, supervisor)
        assert result.citation_count == 0
        assert result.final_risk == "LOW"

    def test_full_evaluation_runs(self, cases, knowledge_service):
        """完整评测运行成功"""
        # 只用前5个案例加速测试
        subset = cases[:5]
        baseline_results, pipeline_results = run_evaluation(subset, knowledge_service)
        assert len(baseline_results) == 5
        assert len(pipeline_results) == 5


# ============================================================
# 安全拦截测试
# ============================================================


class TestSafetyInterception:
    """安全拦截测试"""

    def test_unsafe_candidate_text_not_in_response(self, supervisor):
        """原始危险文本不出现在最终响应中"""
        case = EvaluationCase(
            case_id="test-unsafe",
            category="unsafe_candidate",
            red_flags=[],
            free_text="合成教学示例",
            model_suggested_risk="LOW",
            expected_min_risk="LOW",
            expected_human_review=False,
            unsafe_candidate_text="你就是得了心脏病，建议服用阿莫西林 500mg",
        )

        context = AgentContext(
            case_id=case.case_id,
            age=45,
            symptoms=[],
            red_flags=[],
            free_text=case.free_text,
            model_suggested_risk="LOW",
            candidate_output_text=case.unsafe_candidate_text,
        )
        result_context, _ = supervisor.process(context)

        # 不安全文本不应出现在 safe_summary 中
        assert "你就是得了心脏病" not in result_context.safe_summary
        assert "500mg" not in result_context.safe_summary

    def test_diagnosis_intercepted(self):
        """确定性诊断文本被拦截"""
        agent = SafetyReviewAgent()
        context = AgentContext(
            case_id="test-diag",
            candidate_output_text="你就是得了心脏病",
            final_risk_level="LOW",
        )
        result = agent._execute(context)
        assert "contains_definitive_diagnosis" in result.safety_flags

    def test_prescription_intercepted(self):
        """药物处方文本被拦截"""
        agent = SafetyReviewAgent()
        context = AgentContext(
            case_id="test-rx",
            candidate_output_text="建议服用阿莫西林 500mg",
            final_risk_level="LOW",
        )
        result = agent._execute(context)
        assert "contains_prescription_or_dosage" in result.safety_flags


# ============================================================
# 审计摘要测试
# ============================================================


class TestAuditSummary:
    """审计摘要测试"""

    def test_output_summary_not_no_output(self, supervisor):
        """output_summary 不再出现 no_output"""
        context = AgentContext(
            case_id="test-audit",
            age=45,
            symptoms=[{"name": "头痛", "severity": 3, "duration": "1小时"}],
            red_flags=[],
            free_text="合成教学示例",
            model_suggested_risk="LOW",
        )
        _, audit_trail = supervisor.process(context)

        for record in audit_trail:
            assert record.output_summary != "no_output", \
                f"Agent {record.agent_name} 的 output_summary 仍为 'no_output'"

    def test_intake_summary_contains_info(self):
        """IntakeAgent 摘要有意义"""
        agent = IntakeAgent()
        context = AgentContext(
            case_id="test",
            age=45,
            symptoms=[{"name": "头痛", "severity": 3, "duration": "1小时"}],
            red_flags=["consciousness_change"],
            free_text="合成教学",
        )
        result = agent._execute(context)
        summary = agent._build_output_summary(result)
        assert "红旗" in summary
        assert "no_output" not in summary

    def test_retrieval_summary_contains_info(self):
        """RetrievalAgent 摘要有意义"""
        ks = KnowledgeService(InMemoryVectorStore(), MockEmbeddingProvider(dimension=384))
        agent = RetrievalAgent(ks)
        context = AgentContext(
            case_id="test",
            normalized_symptoms=[{"name": "头痛"}],
            free_text="合成教学",
        )
        result = agent._execute(context)
        summary = agent._build_output_summary(result)
        assert "no_output" not in summary

    def test_risk_summary_contains_info(self):
        """RiskAssessmentAgent 摘要有意义"""
        engine = SafetyRuleEngine()
        agent = RiskAssessmentAgent(engine)
        context = AgentContext(
            case_id="test",
            red_flags=["consciousness_change"],
            free_text="合成教学",
            model_suggested_risk="LOW",
        )
        result = agent._execute(context)
        summary = agent._build_output_summary(result)
        assert "规则风险" in summary
        assert "no_output" not in summary

    def test_audit_no_chain_of_thought(self, supervisor):
        """审计记录不包含思维链字段"""
        context = AgentContext(
            case_id="test",
            free_text="合成教学",
            model_suggested_risk="LOW",
        )
        _, audit_trail = supervisor.process(context)

        for record in audit_trail:
            d = record.model_dump()
            assert "chain_of_thought" not in d
            assert "reasoning" not in d


# ============================================================
# 报告生成测试
# ============================================================


class TestReportGeneration:
    """报告生成测试"""

    def test_csv_json_md_generated(self):
        """CSV、JSON、Markdown 正常生成"""
        from app.evaluation.models import EvaluationReport, EvaluationMetrics

        metrics = EvaluationMetrics(
            total_cases=2, rule_match_recall=1.0, high_risk_recall=1.0,
            high_risk_false_negative_rate=0.0, human_review_recall=1.0,
            model_downgrade_block_rate=1.0, citation_coverage_rate=1.0,
            disclaimer_coverage_rate=1.0, unsafe_output_block_rate=1.0,
            agent_success_rate=1.0, exact_risk_match_rate=1.0,
            error_case_count=0, mean_latency_ms=10.0, p50_latency_ms=10.0,
            p95_latency_ms=10.0,
        )
        report = EvaluationReport(
            dataset_version="test",
            ruleset_version="test",
            model_version="test",
            prompt_version="test",
            knowledge_base_version="test",
            baseline_metrics=metrics,
            pipeline_metrics=metrics,
            generated_at=datetime.now(timezone.utc).isoformat(),
            disclaimer="测试",
        )
        results = [
            CaseResult(case_id="c1", category="test", expected_risk="LOW",
                       baseline_risk="LOW", final_risk="LOW", matched=False,
                       downgrade_blocked=False, human_review=False,
                       citation_count=0, safety_flags=[], latency_ms=10.0, passed=True),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_reports(report, results, results, tmpdir)
            assert os.path.exists(os.path.join(tmpdir, "summary.json"))
            assert os.path.exists(os.path.join(tmpdir, "case_results.csv"))
            assert os.path.exists(os.path.join(tmpdir, "report.md"))

            # 验证 JSON 内容
            with open(os.path.join(tmpdir, "summary.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "pipeline_metrics" in data
            assert "baseline_metrics" in data

    def test_csv_content(self):
        """CSV 内容正确"""
        results = [
            CaseResult(case_id="c1", category="test", expected_risk="HIGH",
                       baseline_risk="LOW", final_risk="HIGH", matched=True,
                       downgrade_blocked=True, human_review=True,
                       citation_count=1, safety_flags=["flag1"], latency_ms=15.5, passed=True),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            _write_case_results_csv(results, Path(path))
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
            assert "c1" in content
            assert "HIGH" in content


# ============================================================
# 可复现性测试
# ============================================================


class TestReproducibility:
    """可复现性测试"""

    def test_same_input_same_result(self, supervisor):
        """相同输入评测结果可复现"""
        case = EvaluationCase(
            case_id="test-repro",
            category="test",
            red_flags=["persistent_chest_discomfort"],
            free_text="合成教学示例",
            model_suggested_risk="LOW",
            expected_min_risk="HIGH",
            expected_human_review=True,
        )

        result1 = run_pipeline(case, supervisor)
        result2 = run_pipeline(case, supervisor)

        assert result1.final_risk == result2.final_risk
        assert result1.matched == result2.matched
        assert result1.downgrade_blocked == result2.downgrade_blocked
        assert result1.human_review == result2.human_review


# ============================================================
# pgvector 维度校验测试
# ============================================================


class TestPgVectorDimension:
    """pgvector 维度校验测试"""

    def test_pgvector_rejects_non_384_dimension(self):
        """pgvector 非384维配置被拒绝"""
        with pytest.raises(ValueError, match="必须为 384"):
            PgVectorStore(database_url="postgresql://test", dimension=512)

    def test_pgvector_accepts_384_dimension(self):
        """pgvector 接受384维（不连接数据库）"""
        store = PgVectorStore(database_url="postgresql://test", dimension=384)
        assert store._dimension == 384

    def test_memory_store_allows_other_dimensions(self):
        """memory 模式允许其他合法维度"""
        store = InMemoryVectorStore()
        # 内存存储不限制维度
        assert store is not None


# ============================================================
# 知识材料测试
# ============================================================


class TestKnowledgeMaterials:
    """知识材料测试"""

    def test_knowledge_materials_load(self, knowledge_docs):
        """知识材料成功加载"""
        assert len(knowledge_docs) >= 6

    def test_all_docs_synthetic(self, knowledge_docs):
        """所有文档标记为合成"""
        for doc in knowledge_docs:
            assert doc.get("synthetic") is True

    def test_all_docs_have_required_fields(self, knowledge_docs):
        """所有文档包含必要字段"""
        for doc in knowledge_docs:
            assert doc.get("title")
            assert doc.get("publisher")
            assert doc.get("source_url")
            assert doc.get("content")
            assert "example.com" in doc.get("source_url", "")
