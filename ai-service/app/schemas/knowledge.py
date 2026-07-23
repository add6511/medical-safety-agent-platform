"""
知识库相关数据模型
定义文档导入、检索、删除等接口的请求和响应结构
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class DocumentImportRequest(BaseModel):
    """文档导入请求模型"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="文档标题",
        examples=["高血压基层诊疗指南"],
    )
    publisher: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="发布机构",
        examples=["中华医学会"],
    )
    source_url: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="来源链接",
        examples=["https://example.org/guidelines/hypertension"],
    )
    document_version: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="文档版本",
        examples=["2024版"],
    )
    published_at: Optional[datetime] = Field(
        default=None,
        description="发布时间",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=500000,
        description="文档正文内容（合成教学材料，不构成诊断或治疗建议）",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, v: str) -> str:
        """确保内容不是纯空白"""
        if not v.strip():
            raise ValueError("文档内容不能为空或纯空白")
        return v

    @field_validator("source_url")
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        """基本的 URL 格式校验"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("source_url 必须以 http:// 或 https:// 开头")
        return v


class DocumentImportResponse(BaseModel):
    """文档导入响应模型"""

    document_id: str = Field(description="文档唯一标识")
    checksum: str = Field(description="文档 SHA-256 校验值")
    chunk_count: int = Field(description="切分后的知识块数量")
    duplicate: bool = Field(description="是否为重复导入")


class DocumentListItem(BaseModel):
    """文档列表项（不包含正文）"""

    document_id: str = Field(description="文档唯一标识")
    title: str = Field(description="文档标题")
    publisher: str = Field(description="发布机构")
    source_url: str = Field(description="来源链接")
    document_version: str = Field(description="文档版本")
    published_at: Optional[datetime] = Field(description="发布时间")
    checksum: str = Field(description="文档校验值")
    chunk_count: int = Field(description="知识块数量")
    created_at: datetime = Field(description="导入时间")


class DocumentListResponse(BaseModel):
    """文档列表响应模型"""

    total: int = Field(description="文档总数")
    documents: List[DocumentListItem] = Field(description="文档列表")


class SearchRequest(BaseModel):
    """知识检索请求模型"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="检索查询文本",
        examples=["高血压的诊断标准是什么"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="返回结果数量，范围 1-10",
    )

    @field_validator("query")
    @classmethod
    def validate_query_not_blank(cls, v: str) -> str:
        """确保查询不是纯空白"""
        if not v.strip():
            raise ValueError("查询内容不能为空或纯空白")
        return v


class SearchItem(BaseModel):
    """单条检索结果"""

    chunk_id: str = Field(description="知识块唯一标识")
    document_id: str = Field(description="所属文档标识")
    title: str = Field(description="文档标题")
    content: str = Field(description="知识块内容")
    score: float = Field(description="相似度得分（0-1）")
    publisher: str = Field(description="发布机构")
    source_url: str = Field(description="来源链接")
    document_version: str = Field(description="文档版本")
    chunk_index: int = Field(description="块在文档中的序号")


class SearchResponse(BaseModel):
    """知识检索响应模型"""

    query: str = Field(description="原始查询")
    top_k: int = Field(description="请求返回数量")
    results: List[SearchItem] = Field(description="检索结果列表")
    disclaimer: str = Field(
        default="检索结果仅供教学参考，不构成诊断或治疗建议。",
        description="安全声明",
    )
