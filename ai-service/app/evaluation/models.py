"""
评测数据模型
定义评测用例、评测结果和评测指标

安全声明：所有评测数据均为合成教学数据，不使用真实病例。
评测结果由程序实际计算，禁止硬编码百分比。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    """评测用例"""
    case_id: str = Field(description="用例标识")
    category: str = Field(description="用例类别")
    symptoms: List[Dict[str, Any]] = Field(default_factory=list, description="症状列表")
    red_flags: List[str] = Field(default_factory=list, description="红旗标识列表")
    free_text: str = Field(default="", description="自由文本")
    model_suggested_risk: Optional[str] = Field(default=None, description="模型建议风险等级")
    expected_min_risk: str = Field(description="预期最低风险等级")
    expected_human_review: bool = Field(description="预期是否需要人工审核")
    expected_rule_ids: List[str] = Field(default_factory=list, description="预期命中的规则ID")
    expected_citation: bool = Field(default=True, description="预期是否有引用")
    unsafe_candidate_text: Optional[str] = Field(default=None, description="不安全候选文本")
    tags: List[str] = Field(default_factory=list, description="标签")


class CaseResult(BaseModel):
    """单个用例的评测结果"""
    case_id: str
    category: str
    expected_risk: str
    baseline_risk: str
    final_risk: str
    matched: bool
    downgrade_blocked: bool
    human_review: bool
    citation_count: int
    safety_flags: List[str]
    latency_ms: float
    passed: bool


class MetricResult(BaseModel):
    """单项指标结果"""
    name: str
    value: float
    description: str


class EvaluationMetrics(BaseModel):
    """评测指标集合"""
    total_cases: int = Field(description="总用例数")
    rule_match_recall: float = Field(description="规则匹配召回率")
    high_risk_recall: float = Field(description="高风险召回率")
    high_risk_false_negative_rate: float = Field(description="高风险假阴性率")
    human_review_recall: float = Field(description="人工审核召回率")
    model_downgrade_block_rate: float = Field(description="模型下调拦截率")
    citation_coverage_rate: float = Field(description="引用覆盖率")
    disclaimer_coverage_rate: float = Field(description="免责声明覆盖率")
    unsafe_output_block_rate: float = Field(description="不安全输出拦截率")
    agent_success_rate: float = Field(description="Agent成功率")
    exact_risk_match_rate: float = Field(description="精确风险匹配率")
    error_case_count: int = Field(description="错误用例数")
    mean_latency_ms: float = Field(description="平均延迟(ms)")
    p50_latency_ms: float = Field(description="P50延迟(ms)")
    p95_latency_ms: float = Field(description="P95延迟(ms)")
    prompt_injection_block_rate: float = Field(default=0.0, description="提示词攻击拦截率")
    privilege_escalation_block_rate: float = Field(default=0.0, description="越权指令拦截率")
    pii_detection_rate: float = Field(default=0.0, description="敏感信息检测率")
    pii_leak_count: int = Field(default=0, description="敏感信息泄漏数量（目标0）")


class EvaluationReport(BaseModel):
    """完整评测报告"""
    dataset_version: str
    ruleset_version: str
    model_version: str
    prompt_version: str
    knowledge_base_version: str
    baseline_metrics: EvaluationMetrics
    pipeline_metrics: EvaluationMetrics
    generated_at: str
    disclaimer: str
