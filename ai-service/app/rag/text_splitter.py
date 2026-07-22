"""
文档切分模块
使用 langchain-text-splitters 的 RecursiveCharacterTextSplitter
针对中文医学文本配置合理的分隔符
"""

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """知识块数据结构"""

    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    title: str
    publisher: str
    source_url: str
    document_version: str
    published_at: Optional[datetime]
    checksum: str


@dataclass
class DocumentInfo:
    """文档元信息"""

    document_id: str
    title: str
    publisher: str
    source_url: str
    document_version: str
    published_at: Optional[datetime]
    checksum: str
    chunk_count: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def compute_checksum(content: str) -> str:
    """计算文档内容的 SHA-256 校验值"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    """去除多余空白，保留段落结构"""
    # 将连续的空白字符（包括换行）规范化为单个换行
    text = re.sub(r"[ \t]+", " ", text)
    # 去除每行首尾空白
    lines = [line.strip() for line in text.split("\n")]
    # 去除连续空行
    result = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                result.append("")
                prev_empty = True
        else:
            result.append(line)
            prev_empty = False
    return "\n".join(result).strip()


def split_document(
    document_id: str,
    title: str,
    publisher: str,
    source_url: str,
    document_version: str,
    published_at: Optional[datetime],
    content: str,
    checksum: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[TextChunk]:
    """
    将文档内容切分为知识块

    Args:
        document_id: 文档唯一标识
        title: 文档标题
        publisher: 发布机构
        source_url: 来源链接
        document_version: 文档版本
        published_at: 发布时间
        content: 文档正文
        checksum: 文档校验值
        chunk_size: 切分块大小，默认从配置读取
        chunk_overlap: 块重叠大小，默认从配置读取

    Returns:
        切分后的知识块列表
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    # 规范化文本
    normalized = normalize_text(content)

    # 文本过短时直接返回单个块，不生成空块
    if len(normalized) <= chunk_size:
        if not normalized:
            logger.warning("文档内容为空，跳过切分。document_id=%s", document_id)
            return []
        return [
            TextChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=0,
                content=normalized,
                title=title,
                publisher=publisher,
                source_url=source_url,
                document_version=document_version,
                published_at=published_at,
                checksum=checksum,
            )
        ]

    # 使用中文友好的分隔符进行递归切分
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        keep_separator=True,
        length_function=len,
    )

    texts = splitter.split_text(normalized)

    # 过滤空块
    texts = [t for t in texts if t.strip()]

    chunks = []
    for i, text in enumerate(texts):
        chunks.append(
            TextChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=i,
                content=text.strip(),
                title=title,
                publisher=publisher,
                source_url=source_url,
                document_version=document_version,
                published_at=published_at,
                checksum=checksum,
            )
        )

    # 不在日志中输出完整文档内容
    logger.info(
        "文档切分完成。document_id=%s, 块数=%d, checksum=%s",
        document_id,
        len(chunks),
        checksum[:16] + "...",
    )

    return chunks
