"""
知识库服务
协调文档切分、Embedding 和向量存储，提供知识库的完整业务逻辑
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from app.rag.embedding import EmbeddingProvider
from app.rag.text_splitter import DocumentInfo, TextChunk, compute_checksum, split_document
from app.rag.vector_store import SearchResult, VectorStore

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库服务，负责文档导入、检索和管理"""

    def __init__(self, vector_store: VectorStore, embedding_provider: EmbeddingProvider):
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider

    def import_document(
        self,
        title: str,
        publisher: str,
        source_url: str,
        document_version: str,
        published_at: Optional[datetime],
        content: str,
    ) -> dict:
        """
        导入文档：计算校验值、切分、向量化、存储

        Returns:
            包含 document_id, checksum, chunk_count, duplicate 的字典
        """
        # 计算文档校验值
        checksum = compute_checksum(content)

        # 检查重复导入（幂等性）
        existing_doc_id = self._vector_store.check_duplicate(checksum)
        if existing_doc_id is not None:
            logger.info("文档已存在，跳过导入。checksum=%s, 已有document_id=%s", checksum[:16] + "...", existing_doc_id)
            # 获取已有文档的块数
            docs = self._vector_store.list_documents()
            existing_doc = next((d for d in docs if d.document_id == existing_doc_id), None)
            chunk_count = existing_doc.chunk_count if existing_doc else 0
            return {
                "document_id": existing_doc_id,
                "checksum": checksum,
                "chunk_count": chunk_count,
                "duplicate": True,
            }

        # 生成文档 ID
        document_id = str(uuid.uuid4())

        # 切分文档
        chunks = split_document(
            document_id=document_id,
            title=title,
            publisher=publisher,
            source_url=source_url,
            document_version=document_version,
            published_at=published_at,
            content=content,
            checksum=checksum,
        )

        if not chunks:
            logger.warning("文档切分后无有效内容。document_id=%s", document_id)
            return {
                "document_id": document_id,
                "checksum": checksum,
                "chunk_count": 0,
                "duplicate": False,
            }

        # 生成向量
        texts = [chunk.content for chunk in chunks]
        vectors = self._embedding_provider.embed_texts(texts)

        # 创建文档元信息
        doc_info = DocumentInfo(
            document_id=document_id,
            title=title,
            publisher=publisher,
            source_url=source_url,
            document_version=document_version,
            published_at=published_at,
            checksum=checksum,
            chunk_count=len(chunks),
        )

        # 存储到向量库
        self._vector_store.add_document(doc_info, chunks, vectors)

        logger.info("文档导入成功。document_id=%s, 块数=%d", document_id, len(chunks))

        return {
            "document_id": document_id,
            "checksum": checksum,
            "chunk_count": len(chunks),
            "duplicate": False,
        }

    def list_documents(self) -> List[dict]:
        """返回已导入文档列表（不包含正文）"""
        docs = self._vector_store.list_documents()
        return [
            {
                "document_id": d.document_id,
                "title": d.title,
                "publisher": d.publisher,
                "source_url": d.source_url,
                "document_version": d.document_version,
                "published_at": d.published_at,
                "checksum": d.checksum,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at,
            }
            for d in docs
        ]

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """
        知识检索：将查询文本向量化后在向量库中检索

        Returns:
            检索结果列表，每项包含完整的引用字段
        """
        # 将查询文本向量化
        query_vectors = self._embedding_provider.embed_texts([query])
        query_vector = query_vectors[0]

        # 在向量库中检索
        results = self._vector_store.search(query_vector, top_k=top_k)

        return [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "title": r.title,
                "content": r.content,
                "score": r.score,
                "publisher": r.publisher,
                "source_url": r.source_url,
                "document_version": r.document_version,
                "chunk_index": r.chunk_index,
            }
            for r in results
        ]

    def delete_document(self, document_id: str) -> bool:
        """删除指定文档及其关联知识块"""
        return self._vector_store.delete_document(document_id)
