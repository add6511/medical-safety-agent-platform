"""
向量存储接口定义和实现
支持内存存储（默认）和 pgvector 存储两种模式
"""

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from app.core.config import settings
from app.rag.text_splitter import DocumentInfo, TextChunk

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """向量检索结果"""

    chunk_id: str
    document_id: str
    title: str
    content: str
    score: float
    publisher: str
    source_url: str
    document_version: str
    chunk_index: int


class VectorStore(ABC):
    """向量存储抽象基类"""

    @abstractmethod
    def add_document(
        self, doc_info: DocumentInfo, chunks: List[TextChunk], vectors: List[List[float]]
    ) -> None:
        """
        添加文档及其知识块

        Args:
            doc_info: 文档元信息
            chunks: 知识块列表
            vectors: 对应的向量列表
        """
        ...

    @abstractmethod
    def check_duplicate(self, checksum: str) -> Optional[str]:
        """
        根据 checksum 检查重复文档

        Args:
            checksum: 文档校验值

        Returns:
            如果重复，返回已有文档的 document_id；否则返回 None
        """
        ...

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """
        向量相似度检索

        Args:
            query_vector: 查询向量
            top_k: 返回结果数量

        Returns:
            按相似度排序的检索结果列表
        """
        ...

    @abstractmethod
    def list_documents(self) -> List[DocumentInfo]:
        """返回已导入文档列表（不包含正文）"""
        ...

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        删除指定文档及其关联知识块

        Args:
            document_id: 文档唯一标识

        Returns:
            是否成功删除（文档不存在返回 False）
        """
        ...


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class InMemoryVectorStore(VectorStore):
    """
    内存向量存储
    用于本地测试，所有数据存储在内存中，无需数据库
    """

    def __init__(self):
        # 文档元信息：document_id -> DocumentInfo
        self._documents: Dict[str, DocumentInfo] = {}
        # 知识块：chunk_id -> TextChunk
        self._chunks: Dict[str, TextChunk] = {}
        # 向量：chunk_id -> vector
        self._vectors: Dict[str, List[float]] = {}
        # checksum 索引：checksum -> document_id
        self._checksum_index: Dict[str, str] = {}

    def add_document(
        self, doc_info: DocumentInfo, chunks: List[TextChunk], vectors: List[List[float]]
    ) -> None:
        """添加文档及其知识块到内存"""
        if len(chunks) != len(vectors):
            raise ValueError("知识块数量与向量数量不匹配")

        self._documents[doc_info.document_id] = doc_info
        self._checksum_index[doc_info.checksum] = doc_info.document_id

        for chunk, vector in zip(chunks, vectors):
            self._chunks[chunk.chunk_id] = chunk
            self._vectors[chunk.chunk_id] = vector

        logger.info("文档已添加到内存存储。document_id=%s, 块数=%d", doc_info.document_id, len(chunks))

    def check_duplicate(self, checksum: str) -> Optional[str]:
        """检查 checksum 是否已存在"""
        return self._checksum_index.get(checksum)

    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """使用余弦相似度进行检索"""
        if not self._chunks:
            return []

        # 计算所有块与查询向量的相似度
        scored = []
        for chunk_id, chunk in self._chunks.items():
            vector = self._vectors.get(chunk_id)
            if vector is None:
                continue
            score = _cosine_similarity(query_vector, vector)
            scored.append((chunk, score))

        # 按相似度降序排序
        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for chunk, score in scored[:top_k]:
            results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    content=chunk.content,
                    score=round(score, 6),
                    publisher=chunk.publisher,
                    source_url=chunk.source_url,
                    document_version=chunk.document_version,
                    chunk_index=chunk.chunk_index,
                )
            )

        return results

    def list_documents(self) -> List[DocumentInfo]:
        """返回所有文档元信息"""
        return list(self._documents.values())

    def delete_document(self, document_id: str) -> bool:
        """删除文档及其关联知识块"""
        doc_info = self._documents.get(document_id)
        if doc_info is None:
            return False

        # 删除关联的知识块和向量
        chunk_ids_to_remove = [
            cid for cid, chunk in self._chunks.items()
            if chunk.document_id == document_id
        ]
        for cid in chunk_ids_to_remove:
            self._chunks.pop(cid, None)
            self._vectors.pop(cid, None)

        # 删除 checksum 索引
        self._checksum_index.pop(doc_info.checksum, None)

        # 删除文档元信息
        del self._documents[document_id]

        logger.info("文档已从内存存储删除。document_id=%s, 删除块数=%d", document_id, len(chunk_ids_to_remove))
        return True


class PgVectorStore(VectorStore):
    """
    PostgreSQL + pgvector 向量存储
    使用 psycopg v3 操作数据库
    """

    def __init__(self, database_url: str, dimension: int = 384):
        if not database_url:
            raise ValueError("VECTOR_DATABASE_URL 不能为空")
        self._database_url = database_url
        self._dimension = dimension
        # 不在初始化时连接数据库，延迟到实际使用时

    def _get_connection(self):
        """获取数据库连接（延迟初始化）"""
        try:
            import psycopg
        except ImportError:
            raise RuntimeError(
                "psycopg 未安装，请运行: pip install psycopg[binary]"
            )

        try:
            conn = psycopg.connect(self._database_url)
            return conn
        except Exception as e:
            logger.error("数据库连接失败")
            raise RuntimeError(
                f"无法连接到向量数据库，请检查 VECTOR_DATABASE_URL 配置。错误类型: {type(e).__name__}"
            ) from e

    def add_document(
        self, doc_info: DocumentInfo, chunks: List[TextChunk], vectors: List[List[float]]
    ) -> None:
        """添加文档及知识块到 PostgreSQL"""
        if len(chunks) != len(vectors):
            raise ValueError("知识块数量与向量数量不匹配")

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # 插入文档元信息
                cur.execute(
                    """
                    INSERT INTO knowledge_documents
                        (document_id, title, publisher, source_url, document_version,
                         published_at, checksum, chunk_count, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        doc_info.document_id,
                        doc_info.title,
                        doc_info.publisher,
                        doc_info.source_url,
                        doc_info.document_version,
                        doc_info.published_at,
                        doc_info.checksum,
                        doc_info.chunk_count,
                        doc_info.created_at,
                    ),
                )

                # 插入知识块
                for chunk, vector in zip(chunks, vectors):
                    # 将向量列表转换为 pgvector 格式的字符串
                    vector_str = "[" + ",".join(str(v) for v in vector) + "]"
                    cur.execute(
                        """
                        INSERT INTO knowledge_chunks
                            (chunk_id, document_id, chunk_index, content, title,
                             publisher, source_url, document_version, published_at,
                             checksum, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                        """,
                        (
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.chunk_index,
                            chunk.content,
                            chunk.title,
                            chunk.publisher,
                            chunk.source_url,
                            chunk.document_version,
                            chunk.published_at,
                            chunk.checksum,
                            vector_str,
                        ),
                    )

            conn.commit()
            logger.info("文档已添加到 pgvector 存储。document_id=%s, 块数=%d", doc_info.document_id, len(chunks))
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def check_duplicate(self, checksum: str) -> Optional[str]:
        """检查 checksum 是否已存在"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT document_id FROM knowledge_documents WHERE checksum = %s LIMIT 1",
                    (checksum,),
                )
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()

    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """使用 pgvector 余弦相似度检索"""
        conn = self._get_connection()
        try:
            vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT chunk_id, document_id, title, content,
                           1 - (embedding <=> %s::vector) AS score,
                           publisher, source_url, document_version, chunk_index
                    FROM knowledge_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (vector_str, vector_str, top_k),
                )
                rows = cur.fetchall()

            results = []
            for row in rows:
                results.append(
                    SearchResult(
                        chunk_id=row[0],
                        document_id=row[1],
                        title=row[2],
                        content=row[3],
                        score=round(float(row[4]), 6),
                        publisher=row[5],
                        source_url=row[6],
                        document_version=row[7],
                        chunk_index=row[8],
                    )
                )
            return results
        finally:
            conn.close()

    def list_documents(self) -> List[DocumentInfo]:
        """返回所有文档元信息"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT document_id, title, publisher, source_url, document_version,
                           published_at, checksum, chunk_count, created_at
                    FROM knowledge_documents
                    ORDER BY created_at DESC
                    """
                )
                rows = cur.fetchall()

            documents = []
            for row in rows:
                documents.append(
                    DocumentInfo(
                        document_id=row[0],
                        title=row[1],
                        publisher=row[2],
                        source_url=row[3],
                        document_version=row[4],
                        published_at=row[5],
                        checksum=row[6],
                        chunk_count=row[7],
                        created_at=row[8],
                    )
                )
            return documents
        finally:
            conn.close()

    def delete_document(self, document_id: str) -> bool:
        """删除文档及关联知识块"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # 先删除知识块（外键约束）
                cur.execute(
                    "DELETE FROM knowledge_chunks WHERE document_id = %s",
                    (document_id,),
                )
                # 再删除文档
                cur.execute(
                    "DELETE FROM knowledge_documents WHERE document_id = %s",
                    (document_id,),
                )
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def create_vector_store() -> VectorStore:
    """根据配置创建对应的向量存储"""
    mode = settings.VECTOR_STORE_MODE

    if mode == "memory":
        logger.info("使用内存向量存储")
        return InMemoryVectorStore()
    elif mode == "pgvector":
        logger.info("使用 pgvector 向量存储")
        return PgVectorStore(
            database_url=settings.VECTOR_DATABASE_URL,
            dimension=settings.EMBEDDING_DIMENSION,
        )
    else:
        raise ValueError(f"不支持的 VECTOR_STORE_MODE: {mode}")
