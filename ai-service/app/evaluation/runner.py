"""
评测运行器
执行 baseline 和 pipeline 两组评测，收集结果

安全声明：
- unsafe_mock_baseline 是人为构造的消融对照，不代表任何真实大模型能力。
- 所有评测数据均为合成教学数据。
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agents.base import AgentContext
from app.agents.intake_agent import IntakeAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.safety_agent import SafetyReviewAgent
from app.agents.supervisor import SupervisorAgent
from app.evaluation.models import CaseResult, EvaluationCase
from app.rules.engine import SafetyRuleEngine
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)

# 风险等级严重程度
_RISK_SEVERITY = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def run_baseline(case: EvaluationCase) -> CaseResult:
    """
    运行 baseline 评测（直接采用 model_suggested_risk，不使用规则保护）

    安全声明：这是人为构造的消融对照，不代表任何真实大模型能力。
    """
    start = time.monotonic()

    baseline_risk = case.model_suggested_risk or "LOW"
    latency_ms = (time.monotonic() - start) * 1000

    # baseline 不使用规则引擎，所以 matched=False, downgrade_blocked=False
    return CaseResult(
        case_id=case.case_id,
        category=case.category,
        expected_risk=case.expected_min_risk,
        baseline_risk=baseline_risk,
        final_risk=baseline_risk,
        matched=False,
        downgrade_blocked=False,
        human_review=False,
        citation_count=0,
        safety_flags=[],
        latency_ms=round(latency_ms, 2),
        passed=False,  # baseline 通常不会通过安全检查
    )


def run_pipeline(
    case: EvaluationCase,
    supervisor: SupervisorAgent,
) -> CaseResult:
    """
    运行完整 pipeline 评测（RAG + 规则引擎 + 多 Agent 安全审核）
    """
    start = time.monotonic()

    # 构建上下文
    context = AgentContext(
        case_id=case.case_id,
        age=45,
        symptoms=case.symptoms,
        red_flags=case.red_flags,
        free_text=case.free_text,
        model_suggested_risk=case.model_suggested_risk,
        # 注入不安全候选文本用于测试拦截
        candidate_output_text=case.unsafe_candidate_text or "",
    )

    # 执行多 Agent 流程
    result_context, audit_trail = supervisor.process(context)

    latency_ms = (time.monotonic() - start) * 1000

    # 检查结果
    final_risk = result_context.final_risk_level or "LOW"
    baseline_risk = case.model_suggested_risk or "LOW"

    # 判断是否通过
    risk_ok = _RISK_SEVERITY.get(final_risk, 0) >= _RISK_SEVERITY.get(case.expected_min_risk, 0)
    review_ok = (not case.expected_human_review) or result_context.needs_human_review
    # 检查不安全文本是否被拦截
    safety_ok = True
    if case.unsafe_candidate_text:
        # 不安全候选文本不应出现在 safe_summary 中
        if case.unsafe_candidate_text in result_context.safe_summary:
            safety_ok = False

    passed = risk_ok and review_ok and safety_ok

    return CaseResult(
        case_id=case.case_id,
        category=case.category,
        expected_risk=case.expected_min_risk,
        baseline_risk=baseline_risk,
        final_risk=final_risk,
        matched=len(result_context.matched_rules) > 0,
        downgrade_blocked=result_context.model_downgrade_blocked,
        human_review=result_context.needs_human_review,
        citation_count=len(result_context.retrieved_evidence),
        safety_flags=result_context.safety_flags,
        latency_ms=round(latency_ms, 2),
        passed=passed,
    )


def run_evaluation(
    cases: List[EvaluationCase],
    knowledge_service: Optional[KnowledgeService] = None,
) -> tuple[List[CaseResult], List[CaseResult]]:
    """
    运行完整评测（baseline + pipeline）

    Args:
        cases: 评测用例列表
        knowledge_service: 知识库服务（可选）

    Returns:
        (baseline_results, pipeline_results)
    """
    # 创建规则引擎和 Agent
    rule_engine = SafetyRuleEngine()

    if knowledge_service is None:
        from app.rag.embedding import MockEmbeddingProvider
        from app.rag.vector_store import InMemoryVectorStore
        knowledge_service = KnowledgeService(InMemoryVectorStore(), MockEmbeddingProvider(dimension=384))

    supervisor = SupervisorAgent([
        IntakeAgent(),
        RetrievalAgent(knowledge_service),
        RiskAssessmentAgent(rule_engine),
        SafetyReviewAgent(),
    ])

    baseline_results: List[CaseResult] = []
    pipeline_results: List[CaseResult] = []

    for i, case in enumerate(cases):
        logger.info("评测进度: %d/%d, case_id=%s", i + 1, len(cases), case.case_id)

        # 运行 baseline
        baseline_result = run_baseline(case)
        baseline_results.append(baseline_result)

        # 运行 pipeline
        pipeline_result = run_pipeline(case, supervisor)
        pipeline_results.append(pipeline_result)

    logger.info("评测完成。总用例=%d", len(cases))
    return baseline_results, pipeline_results
