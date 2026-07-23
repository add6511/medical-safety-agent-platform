"""
分诊分析请求和响应模型

安全声明：所有内容仅供教学演示，不构成诊断或治疗建议。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.rules.models import RiskLevel
from app.schemas.preconsultation import SymptomInput, VALID_RED_FLAGS


class TriageRequest(BaseModel):
    """分诊分析请求"""
    case_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="病例标识（合成教学用）",
        examples=["synthetic-triage-001"],
    )
    age: Optional[int] = Field(
        default=None,
        ge=0,
        le=150,
        description="年龄",
    )
    symptoms: List[SymptomInput] = Field(
        default_factory=list,
        description="症状列表",
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="红旗标识列表",
    )
    free_text: str = Field(
        default="",
        max_length=5000,
        description="自由文本描述（合成教学病例）",
    )
    model_suggested_risk: Optional[str] = Field(
        default=None,
        description="模型建议的风险等级",
    )

    @field_validator("red_flags")
    @classmethod
    def validate_red_flags(cls, v: List[str]) -> List[str]:
        for flag in v:
            if flag not in VALID_RED_FLAGS:
                raise ValueError(f"非法红旗标识: {flag}，合法值: {sorted(VALID_RED_FLAGS)}")
        return v

    @field_validator("model_suggested_risk")
    @classmethod
    def validate_model_risk(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in {level.value for level in RiskLevel}:
            raise ValueError(f"非法风险等级: {v}，合法值: LOW/MEDIUM/HIGH/CRITICAL")
        return v.upper() if v else v


class TriageResponse(BaseModel):
    """分诊分析响应"""
    case_id: str = Field(description="病例标识")
    trace_id: str = Field(description="请求追踪ID（UUID4）")
    risk_level: str = Field(description="风险等级")
    symptom_summary: str = Field(description="症状摘要")
    red_flags: List[str] = Field(description="红旗标识列表")
    evidence: List[Dict[str, Any]] = Field(description="证据列表")
    citations: List[Dict[str, Any]] = Field(description="引用来源列表")
    missing_information: List[str] = Field(description="缺失信息字段")
    followup_questions: List[str] = Field(description="追问问题列表")
    safety_status: str = Field(description="安全状态：pass / blocked / human_review")
    safety_flags: List[str] = Field(description="安全审核标记列表")
    sanitized_input: str = Field(description="脱敏后的输入文本")
    needs_human_review: bool = Field(description="是否需要人工审核")
    disclaimer: str = Field(description="免责声明")
