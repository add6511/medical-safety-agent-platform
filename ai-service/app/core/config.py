"""
应用配置模块
使用 pydantic-settings 从环境变量读取配置
"""

from typing import List, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator


class Settings(BaseSettings):
    """应用配置项，从环境变量或 .env 文件加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 应用基本信息
    APP_NAME: str = "基层医疗安全型预问诊AI服务"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"

    # 日志级别
    LOG_LEVEL: str = "INFO"

    # AI 模式：mock 表示使用模拟数据，不调用真实模型
    AI_MODE: str = "mock"

    # 模型相关配置（禁止提供真实默认密钥）
    MODEL_BASE_URL: str = ""
    MODEL_API_KEY: str = ""
    MODEL_NAME: str = ""

    # 数据库连接
    DATABASE_URL: str = ""

    # CORS 允许的前端地址，多个地址用逗号分隔
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ===== RAG 相关配置 =====

    # 向量存储模式：memory（内存）或 pgvector（PostgreSQL）
    VECTOR_STORE_MODE: Literal["memory", "pgvector"] = "memory"

    # Embedding 模式：mock（本地模拟）或 openai_compatible（调用兼容接口）
    EMBEDDING_MODE: Literal["mock", "openai_compatible"] = "mock"

    # Embedding 向量维度
    EMBEDDING_DIMENSION: int = 384

    # 文档切分参数
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80

    # pgvector 数据库连接（与 DATABASE_URL 分开，避免冲突）
    VECTOR_DATABASE_URL: str = ""

    # Embedding 接口配置（openai_compatible 模式下使用）
    EMBEDDING_BASE_URL: str = ""
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = ""

    @field_validator("MODEL_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """确保 API Key 不包含明显的占位符风险"""
        return v

    @field_validator("EMBEDDING_API_KEY")
    @classmethod
    def validate_embedding_api_key(cls, v: str) -> str:
        """确保 Embedding API Key 不包含明显的占位符风险"""
        return v

    @model_validator(mode="after")
    def validate_rag_config(self) -> "Settings":
        """校验 RAG 相关配置的合法性"""
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError(
                f"CHUNK_OVERLAP({self.CHUNK_OVERLAP}) 必须小于 CHUNK_SIZE({self.CHUNK_SIZE})"
            )
        if self.EMBEDDING_DIMENSION <= 0:
            raise ValueError(
                f"EMBEDDING_DIMENSION({self.EMBEDDING_DIMENSION}) 必须大于 0"
            )
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        """将逗号分隔的 CORS_ORIGINS 转为列表"""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# 全局配置单例
settings = Settings()
