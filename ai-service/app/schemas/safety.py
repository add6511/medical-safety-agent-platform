"""
安全检查请求和响应模型

安全声明：所有内容仅供教学演示，不构成诊断或治疗建议。
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.rules.models import RiskLevel


class SafetyCheckRequest(BaseModel):
    """安全检查请求"""
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="待审核文本",
    )
    risk_level: Optional[str] = Field(
        default=None,
        description="当前风险等级（用于检查风险是否被降低）",
    )
    needs_human_review: Optional[bool] = Field(
        default=None,
        description="当前是否标记需要人工审核",
    )

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in {level.value for level in RiskLevel}:
            raise ValueError(f"非法风险等级: {v}，合法值: LOW/MEDIUM/HIGH/CRITICAL")
        return v.upper() if v else v


class SafetyCheckResponse(BaseModel):
    """安全检查响应"""
    trace_id: str = Field(description="请求追踪ID（UUID4）")
    safety_status: str = Field(description="安全状态：pass / blocked / human_review")
    safety_flags: List[str] = Field(description="安全标记列表")
    sanitized_text: str = Field(description="清理后的文本")
    needs_human_review: bool = Field(description="是否需要人工审核")
    disclaimer: str = Field(description="免责声明")
