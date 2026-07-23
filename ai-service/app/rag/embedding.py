"""
Embedding 接口定义和实现
提供统一的向量化接口，支持 mock 和 openai_compatible 两种模式
"""

import hashlib
import logging
import math
import struct
from abc import ABC, abstractmethod
from typing import List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Embedding 提供者抽象基类"""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为向量列表

        Args:
            texts: 待向量化的文本列表

        Returns:
            向量列表，每个向量为浮点数列表
        """
        ...

    @abstractmethod
    def get_dimension(self) -> int:
        """返回向量维度"""
        ...


class MockEmbeddingProvider(EmbeddingProvider):
    """
    模拟 Embedding 提供者
    用于本地测试，生成确定性归一化向量，不调用外部模型
    相同文本始终生成相同向量
    """

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    def _text_to_vector(self, text: str) -> List[float]:
        """
        将文本转换为确定性向量
        使用 SHA-256 哈希生成伪随机但确定性的浮点数
        """
        # 使用多个哈希种子生成足够维度的向量
        vector = []
        seed = text.encode("utf-8")

        while len(vector) < self._dimension:
            hash_bytes = hashlib.sha256(seed).digest()
            # 将每 4 字节转换为一个浮点数
            for i in range(0, len(hash_bytes) - 3, 4):
                if len(vector) >= self._dimension:
                    break
                # 使用 struct 解包为无符号整数，再归一化到 [-1, 1]
                val = struct.unpack(">I", hash_bytes[i : i + 4])[0]
                normalized = (val / 0xFFFFFFFF) * 2.0 - 1.0
                vector.append(normalized)
            # 更新种子以生成更多维度
            seed = hashlib.sha256(seed).digest()

        # L2 归一化
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """生成确定性模拟向量"""
        return [self._text_to_vector(text) for text in texts]

    def get_dimension(self) -> int:
        return self._dimension


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI 兼容 Embedding 提供者
    使用 HTTPX 调用 /embeddings 接口
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dimension: int = 384,
        timeout: float = 30.0,
    ):
        if not base_url:
            raise ValueError("EMBEDDING_BASE_URL 不能为空")
        if not api_key:
            raise ValueError("EMBEDDING_API_KEY 不能为空")
        if not model:
            raise ValueError("EMBEDDING_MODEL 不能为空")

        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._dimension = dimension
        self._timeout = timeout

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """调用 OpenAI 兼容接口获取向量"""
        url = f"{self._base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "input": texts,
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # 不在异常中暴露 API Key
            logger.error("Embedding 接口返回错误状态码: %d", e.response.status_code)
            raise RuntimeError(f"Embedding 接口请求失败，状态码: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("Embedding 接口请求异常: %s", type(e).__name__)
            raise RuntimeError(f"Embedding 接口请求异常: {type(e).__name__}") from e

        data = response.json()
        embeddings = data.get("data", [])

        # 校验返回向量数量
        if len(embeddings) != len(texts):
            raise RuntimeError(
                f"返回向量数量({len(embeddings)})与输入文本数量({len(texts)})不匹配"
            )

        # 按 index 排序并提取向量
        embeddings.sort(key=lambda x: x.get("index", 0))
        vectors = []
        for item in embeddings:
            vector = item.get("embedding", [])
            # 校验向量维度
            if len(vector) != self._dimension:
                raise RuntimeError(
                    f"返回向量维度({len(vector)})与预期维度({self._dimension})不匹配"
                )
            vectors.append(vector)

        return vectors

    def get_dimension(self) -> int:
        return self._dimension


def create_embedding_provider() -> EmbeddingProvider:
    """根据配置创建对应的 Embedding 提供者"""
    mode = settings.EMBEDDING_MODE
    dimension = settings.EMBEDDING_DIMENSION

    if mode == "mock":
        logger.info("使用 Mock Embedding 提供者，维度=%d", dimension)
        return MockEmbeddingProvider(dimension=dimension)
    elif mode == "openai_compatible":
        logger.info("使用 OpenAI 兼容 Embedding 提供者，维度=%d", dimension)
        return OpenAICompatibleEmbeddingProvider(
            base_url=settings.EMBEDDING_BASE_URL,
            api_key=settings.EMBEDDING_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimension=dimension,
        )
    else:
        raise ValueError(f"不支持的 EMBEDDING_MODE: {mode}")
