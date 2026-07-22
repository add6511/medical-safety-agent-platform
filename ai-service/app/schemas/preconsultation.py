"""
预问诊审核请求和响应模型

安全声明：所有内容仅供教学演示，不构成诊断或治疗建议。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.rules.models import RiskLevel


# 合法的红旗标识列表
VALID_RED_FLAGS = {
    "consciousness_change",
    "severe_breathing_difficulty",
    "persistent_chest_discomfort",
    "uncontrolled_bleeding",
    "self_harm_risk",
    "pregnancy_emergency_signal",
}


class SymptomInput(BaseModel):
    """症状输入"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="症状名称",
        examples=["胸部不适"],
    )
    severity: int = Field(
        default=5,
        ge=0,
        le=10,
        description="严重程度（0-10）",
        examples=[7],
    )
    duration: str = Field(
        default="",
        max_length=100,
        description="持续时间",
        examples=["30分钟"],
    )


class PreconsultationRequest(BaseModel):
    """预问诊审核请求"""
    case_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="病例标识（合成教学用）",
        examples=["synthetic-case-001"],
    )
    age: Optional[int] = Field(
        default=None,
        ge=0,
        le=150,
        description="年龄",
        examples=[45],
    )
    symptoms: List[SymptomInput] = Field(
        default_factory=list,
        description="症状列表",
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="红旗标识列表",
        examples=[["persistent_chest_discomfort"]],
    )
    free_text: str = Field(
        default="",
        max_length=5000,
        description="自由文本描述（合成教学病例）",
    )
    model_suggested_risk: Optional[str] = Field(
        default=None,
        description="模型建议的风险等级（LOW/MEDIUM/HIGH/CRITICAL）",
    )

    @field_validator("red_flags")
    @classmethod
    def validate_red_flags(cls, v: List[str]) -> List[str]:
        """校验红旗标识的合法性"""
        for flag in v:
            if flag not in VALID_RED_FLAGS:
                raise ValueError(f"非法红旗标识: {flag}，合法值: {sorted(VALID_RED_FLAGS)}")
        return v

    @field_validator("model_suggested_risk")
    @classmethod
    def validate_model_risk(cls, v: Optional[str]) -> Optional[str]:
        """校验模型建议风险等级的合法性"""
        if v is not None and v.upper() not in {level.value for level in RiskLevel}:
            raise ValueError(f"非法风险等级: {v}，合法值: LOW/MEDIUM/HIGH/CRITICAL")
        return v.upper() if v else v


class PreconsultationResponse(BaseModel):
    """预问诊审核响应"""
    case_id: str = Field(description="病例标识")
    trace_id: str = Field(description="请求追踪ID（UUID4）")
    final_risk_level: str = Field(description="最终风险等级")
    risk_level: str = Field(description="风险等级（与 final_risk_level 一致）")
    rule_risk_level: str = Field(description="规则引擎风险等级")
    model_suggested_risk: Optional[str] = Field(description="模型建议风险等级")
    model_downgrade_blocked: bool = Field(description="模型降级是否被阻止")
    needs_human_review: bool = Field(description="是否需要人工审核")
    matched_rules: List[Dict[str, Any]] = Field(description="命中的规则列表")
    retrieved_evidence: List[Dict[str, Any]] = Field(description="检索到的知识引用")
    evidence: List[Dict[str, Any]] = Field(description="证据列表（与 retrieved_evidence 一致）")
    citations: List[Dict[str, Any]] = Field(description="引用来源列表")
    safety_flags: List[str] = Field(description="安全审核标记")
    safety_status: str = Field(description="安全状态：pass / blocked / human_review")
    safe_summary: str = Field(description="安全审核后的摘要文本")
    symptom_summary: str = Field(description="症状摘要")
    red_flags: List[str] = Field(description="红旗标识列表")
    missing_information: List[str] = Field(description="缺失信息字段")
    followup_questions: List[str] = Field(description="追问问题列表")
    disclaimer: str = Field(description="免责声明")
    agent_trace: List[Dict[str, Any]] = Field(description="Agent 审计记录（不含思维链）")
    ruleset_version: str = Field(description="规则集版本")
    model_version: str = Field(description="模型版本")
    prompt_version: str = Field(description="Prompt 版本")
    knowledge_base_version: str = Field(description="知识库版本")
