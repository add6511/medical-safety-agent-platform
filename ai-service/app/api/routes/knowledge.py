"""
知识库 API 路由
提供文档导入、列表、检索和删除接口

安全声明：知识库内容仅供教学参考，不构成诊断或治疗建议。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header

from app.core.config import settings
from app.schemas.knowledge import (
    DocumentImportRequest,
    DocumentImportResponse,
    DocumentListResponse,
    DocumentListItem,
    SearchRequest,
    SearchResponse,
    SearchItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["知识库"])

# 知识库服务实例（延迟初始化，在 lifespan 中设置）
_knowledge_service = None


def set_knowledge_service(service) -> None:
    """设置知识库服务实例"""
    global _knowledge_service
    _knowledge_service = service


def get_knowledge_service():
    """获取知识库服务实例"""
    if _knowledge_service is None:
        raise HTTPException(status_code=503, detail="知识库服务未初始化")
    return _knowledge_service


def _verify_internal_api_key(x_internal_api_key: Optional[str]) -> None:
    """校验内部 API 密钥（仅当配置了 INTERNAL_API_KEY 时才强制校验）"""
    required_key = settings.INTERNAL_API_KEY
    if not required_key:
        return
    if x_internal_api_key is None:
        raise HTTPException(status_code=403, detail="缺少内部 API 密钥")
    if x_internal_api_key != required_key:
        raise HTTPException(status_code=401, detail="内部 API 密钥无效")


@router.post(
    "/knowledge/documents",
    response_model=DocumentImportResponse,
    summary="导入教学文档",
    description=(
        "导入教学用指南文本到知识库。"
        "内容必须为合成教学材料，不接受真实患者数据。"
        "相同校验值的文档重复导入时保持幂等，不重复创建数据。"
    ),
)
def import_document(
    request: DocumentImportRequest,
    x_internal_api_key: Optional[str] = Header(None),
) -> DocumentImportResponse:
    """导入文档到知识库"""
    _verify_internal_api_key(x_internal_api_key)
    service = get_knowledge_service()

    result = service.import_document(
        title=request.title,
        publisher=request.publisher,
        source_url=request.source_url,
        document_version=request.document_version,
        published_at=request.published_at,
        content=request.content,
    )

    return DocumentImportResponse(
        document_id=result["document_id"],
        checksum=result["checksum"],
        chunk_count=result["chunk_count"],
        duplicate=result["duplicate"],
    )


@router.get(
    "/knowledge/documents",
    response_model=DocumentListResponse,
    summary="查询文档列表",
    description="返回已导入的文档列表，不包含文档正文。",
)
async def list_documents() -> DocumentListResponse:
    """返回已导入文档列表"""
    service = get_knowledge_service()

    docs = service.list_documents()

    return DocumentListResponse(
        total=len(docs),
        documents=[
            DocumentListItem(
                document_id=d["document_id"],
                title=d["title"],
                publisher=d["publisher"],
                source_url=d["source_url"],
                document_version=d["document_version"],
                published_at=d["published_at"],
                checksum=d["checksum"],
                chunk_count=d["chunk_count"],
                created_at=d["created_at"],
            )
            for d in docs
        ],
    )


@router.post(
    "/knowledge/search",
    response_model=SearchResponse,
    summary="知识检索",
    description=(
        "根据查询文本检索相关知识片段。"
        "检索结果只返回知识片段和来源，不生成诊断结论。"
    ),
)
async def search_knowledge(request: SearchRequest) -> SearchResponse:
    """知识检索接口"""
    service = get_knowledge_service()

    results = service.search(query=request.query.strip(), top_k=request.top_k)

    return SearchResponse(
        query=request.query,
        top_k=request.top_k,
        results=[
            SearchItem(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                title=r["title"],
                content=r["content"],
                score=r["score"],
                publisher=r["publisher"],
                source_url=r["source_url"],
                document_version=r["document_version"],
                chunk_index=r["chunk_index"],
            )
            for r in results
        ],
    )


@router.delete(
    "/knowledge/documents/{document_id}",
    summary="删除文档",
    description="删除指定文档及其关联的所有知识块。",
)
def delete_document(
    document_id: str,
    x_internal_api_key: Optional[str] = Header(None),
) -> dict:
    """删除文档及其关联知识块"""
    _verify_internal_api_key(x_internal_api_key)
    service = get_knowledge_service()

    deleted = service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"文档不存在: {document_id}")

    return {"message": "文档已删除", "document_id": document_id}
