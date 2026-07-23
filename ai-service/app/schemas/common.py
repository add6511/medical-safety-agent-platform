"""
通用响应模型定义
使用 Pydantic v2 定义标准化的 API 响应结构
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康检查响应模型"""

    status: str = Field(
        default="ok",
        description="服务状态",
        examples=["ok"],
    )
    service: str = Field(
        default="medical-safety-ai-service",
        description="服务名称",
        examples=["medical-safety-ai-service"],
    )
    version: str = Field(
        default="0.1.0",
        description="服务版本",
        examples=["0.1.0"],
    )
    environment: str = Field(
        default="development",
        description="运行环境",
        examples=["development"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "ok",
                    "service": "medical-safety-ai-service",
                    "version": "0.1.0",
                    "environment": "development",
                }
            ]
        }
    }
