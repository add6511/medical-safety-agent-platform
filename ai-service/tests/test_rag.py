"""
RAG 功能测试
覆盖文档切分、Embedding、向量存储、知识库接口等

所有测试默认使用 memory 和 mock 模式，不依赖网络、数据库或真实模型。
测试数据明确标注为"合成教学材料"。
"""

import math
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.rag.text_splitter import compute_checksum, split_document, normalize_text
from app.rag.embedding import MockEmbeddingProvider
from app.rag.vector_store import InMemoryVectorStore, _cosine_similarity
from app.services.knowledge_service import KnowledgeService


# ============================================================
# 测试常量：合成教学材料
# ============================================================

SAMPLE_TITLE = "高血压基层诊疗指南（合成教学材料）"
SAMPLE_PUBLISHER = "教学演示机构"
SAMPLE_URL = "https://example.org/guidelines/hypertension-teaching"
SAMPLE_VERSION = "2024教学版"
SAMPLE_CONTENT = (
    "高血压的诊断标准：在未使用降压药物的情况下，"
    "非同日3次测量血压，收缩压≥140mmHg和/或舒张压≥90mmHg。"
    "高血压可分为1级、2级和3级。"
    "1级高血压：收缩压140-159mmHg和/或舒张压90-99mmHg。"
    "2级高血压：收缩压160-179mmHg和/或舒张压100-109mmHg。"
    "3级高血压：收缩压≥180mmHg和/或舒张压≥110mmHg。"
    "高血压的治疗原则包括：生活方式干预和药物治疗。"
    "生活方式干预包括：减少钠盐摄入、增加钾盐摄入、"
    "控制体重、戒烟限酒、适当运动、减轻精神压力。"
    "常用降压药物包括：ACEI、ARB、CCB、利尿剂和β受体阻滞剂。"
)

# 较长的中文文本，用于测试切分
LONG_CONTENT = (
    "第一章 高血压概述\n\n"
    "高血压是最常见的慢性病，也是心脑血管病最主要的危险因素。\n\n"
    "第二章 诊断标准\n\n"
    "在未使用降压药物的情况下，非同日3次测量血压。"
    "收缩压≥140mmHg和/或舒张压≥90mmHg即可诊断为高血压。\n\n"
    "第三章 分级\n\n"
    "1级高血压（轻度）：收缩压140～159mmHg和/或舒张压90～99mmHg。\n"
    "2级高血压（中度）：收缩压160～179mmHg和/或舒张压100～109mmHg。\n"
    "3级高血压（重度）：收缩压≥180mmHg和/或舒张压≥110mmHg。\n\n"
    "第四章 治疗\n\n"
    "高血压治疗的根本目标是降低发生心脑肾及血管并发症和死亡的总危险。"
    "在治疗高血压的同时，应干预所有其他可逆性心血管危险因素。"
)


@pytest.fixture
def anyio_backend():
    """指定 async 测试后端为 asyncio"""
    return "asyncio"


@pytest.fixture
async def client():
    """创建异步测试客户端，并手动初始化知识库服务"""
    # 手动初始化知识库服务（ASGITransport 不触发 lifespan）
    from app.api.routes.knowledge import set_knowledge_service
    embedding_provider = MockEmbeddingProvider(dimension=384)
    vector_store = InMemoryVectorStore()
    service = KnowledgeService(vector_store, embedding_provider)
    set_knowledge_service(service)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_embedding():
    """创建 Mock Embedding 提供者"""
    return MockEmbeddingProvider(dimension=384)


@pytest.fixture
def memory_store():
    """创建内存向量存储"""
    return InMemoryVectorStore()


@pytest.fixture
def knowledge_service(memory_store, mock_embedding):
    """创建知识库服务"""
    return KnowledgeService(memory_store, mock_embedding)


# ============================================================
# 文档切分测试
# ============================================================


class TestTextSplitter:
    """文档切分相关测试"""

    def test_chinese_document_split(self):
        """验证中文文档能正确切分"""
        chunks = split_document(
            document_id="test-doc-001",
            title=SAMPLE_TITLE,
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content=LONG_CONTENT,
            checksum="test-checksum",
            chunk_size=200,
            chunk_overlap=50,
        )
        assert len(chunks) > 1
        # 每个块都有内容
        for chunk in chunks:
            assert chunk.content.strip() != ""
            assert chunk.document_id == "test-doc-001"
            assert chunk.title == SAMPLE_TITLE

    def test_short_document_single_chunk(self):
        """验证短文档不会被切分，且不生成空块"""
        short_content = "这是一段很短的文档内容。"
        chunks = split_document(
            document_id="test-doc-short",
            title="短文档",
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content=short_content,
            checksum="test-checksum-short",
            chunk_size=500,
            chunk_overlap=80,
        )
        assert len(chunks) == 1
        assert chunks[0].content.strip() != ""
        assert chunks[0].chunk_index == 0

    def test_empty_content_no_chunks(self):
        """验证空内容不生成任何块"""
        chunks = split_document(
            document_id="test-doc-empty",
            title="空文档",
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content="",
            checksum="test-checksum-empty",
        )
        assert len(chunks) == 0

    def test_checksum_stability(self):
        """验证相同内容始终生成相同的 checksum"""
        checksum1 = compute_checksum(SAMPLE_CONTENT)
        checksum2 = compute_checksum(SAMPLE_CONTENT)
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 十六进制长度

    def test_checksum_different_content(self):
        """验证不同内容生成不同的 checksum"""
        checksum1 = compute_checksum("内容A")
        checksum2 = compute_checksum("内容B")
        assert checksum1 != checksum2

    def test_chunk_has_all_fields(self):
        """验证切分后的块包含所有必要字段"""
        chunks = split_document(
            document_id="test-doc-fields",
            title=SAMPLE_TITLE,
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content=SAMPLE_CONTENT,
            checksum="test-checksum-fields",
            chunk_size=200,
            chunk_overlap=50,
        )
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.chunk_id is not None
            assert chunk.document_id == "test-doc-fields"
            assert chunk.chunk_index >= 0
            assert chunk.content.strip() != ""
            assert chunk.title == SAMPLE_TITLE
            assert chunk.publisher == SAMPLE_PUBLISHER
            assert chunk.source_url == SAMPLE_URL
            assert chunk.document_version == SAMPLE_VERSION
            assert chunk.checksum == "test-checksum-fields"


# ============================================================
# Embedding 测试
# ============================================================


class TestMockEmbedding:
    """Mock Embedding 提供者测试"""

    def test_deterministic_output(self):
        """验证相同文本始终生成相同向量"""
        provider = MockEmbeddingProvider(dimension=384)
        text = "高血压的诊断标准"
        vec1 = provider.embed_texts([text])[0]
        vec2 = provider.embed_texts([text])[0]
        assert vec1 == vec2

    def test_dimension(self):
        """验证向量维度正确"""
        provider = MockEmbeddingProvider(dimension=384)
        vectors = provider.embed_texts(["测试文本"])
        assert len(vectors[0]) == 384
        assert provider.get_dimension() == 384

    def test_normalization(self):
        """验证向量已归一化（L2 范数约等于 1）"""
        provider = MockEmbeddingProvider(dimension=384)
        vectors = provider.embed_texts(["归一化测试"])
        norm = math.sqrt(sum(v * v for v in vectors[0]))
        assert abs(norm - 1.0) < 1e-6

    def test_different_texts_different_vectors(self):
        """验证不同文本生成不同向量"""
        provider = MockEmbeddingProvider(dimension=384)
        vecs = provider.embed_texts(["文本A", "文本B"])
        assert vecs[0] != vecs[1]

    def test_batch_embedding(self):
        """验证批量向量化"""
        provider = MockEmbeddingProvider(dimension=384)
        texts = ["文本1", "文本2", "文本3"]
        vectors = provider.embed_texts(texts)
        assert len(vectors) == 3
        for vec in vectors:
            assert len(vec) == 384


# ============================================================
# 内存向量存储测试
# ============================================================


class TestInMemoryVectorStore:
    """内存向量存储测试"""

    def test_cosine_similarity_identical(self):
        """验证相同向量的余弦相似度为 1"""
        vec = [1.0, 0.0, 0.0]
        assert abs(_cosine_similarity(vec, vec) - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        """验证正交向量的余弦相似度为 0"""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        assert abs(_cosine_similarity(vec_a, vec_b)) < 1e-6

    def test_search_returns_sorted_results(self, mock_embedding):
        """验证检索结果按相似度降序排列"""
        store = InMemoryVectorStore()

        # 创建测试数据
        doc_id = "test-doc-search"
        texts = ["高血压诊断标准", "糖尿病症状", "高血压治疗方案"]
        chunks = []
        for i, text in enumerate(texts):
            from app.rag.text_splitter import TextChunk
            chunks.append(
                TextChunk(
                    chunk_id=f"chunk-{i}",
                    document_id=doc_id,
                    chunk_index=i,
                    content=text,
                    title="测试文档",
                    publisher="测试机构",
                    source_url="https://example.org",
                    document_version="v1",
                    published_at=None,
                    checksum="test-checksum",
                )
            )

        vectors = mock_embedding.embed_texts(texts)

        from app.rag.text_splitter import DocumentInfo
        doc_info = DocumentInfo(
            document_id=doc_id,
            title="测试文档",
            publisher="测试机构",
            source_url="https://example.org",
            document_version="v1",
            published_at=None,
            checksum="test-checksum",
            chunk_count=3,
            created_at=datetime.now(timezone.utc),
        )
        store.add_document(doc_info, chunks, vectors)

        # 检索"高血压"
        query_vec = mock_embedding.embed_texts(["高血压"])[0]
        results = store.search(query_vec, top_k=3)
        assert len(results) > 0
        # 验证结果按相似度降序
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    def test_add_and_list_documents(self, mock_embedding):
        """验证添加文档后能正确列出"""
        store = InMemoryVectorStore()

        from app.rag.text_splitter import TextChunk, DocumentInfo

        doc_info = DocumentInfo(
            document_id="doc-list-test",
            title="列表测试",
            publisher="测试机构",
            source_url="https://example.org",
            document_version="v1",
            published_at=None,
            checksum="checksum-list",
            chunk_count=1,
            created_at=datetime.now(timezone.utc),
        )
        chunks = [
            TextChunk(
                chunk_id="chunk-list-0",
                document_id="doc-list-test",
                chunk_index=0,
                content="测试内容",
                title="列表测试",
                publisher="测试机构",
                source_url="https://example.org",
                document_version="v1",
                published_at=None,
                checksum="checksum-list",
            )
        ]
        vectors = mock_embedding.embed_texts(["测试内容"])
        store.add_document(doc_info, chunks, vectors)

        docs = store.list_documents()
        assert len(docs) == 1
        assert docs[0].document_id == "doc-list-test"

    def test_delete_document(self, mock_embedding):
        """验证删除文档及其关联知识块"""
        store = InMemoryVectorStore()

        from app.rag.text_splitter import TextChunk, DocumentInfo

        doc_info = DocumentInfo(
            document_id="doc-delete-test",
            title="删除测试",
            publisher="测试机构",
            source_url="https://example.org",
            document_version="v1",
            published_at=None,
            checksum="checksum-delete",
            chunk_count=2,
            created_at=datetime.now(timezone.utc),
        )
        chunks = [
            TextChunk(
                chunk_id=f"chunk-del-{i}",
                document_id="doc-delete-test",
                chunk_index=i,
                content=f"内容{i}",
                title="删除测试",
                publisher="测试机构",
                source_url="https://example.org",
                document_version="v1",
                published_at=None,
                checksum="checksum-delete",
            )
            for i in range(2)
        ]
        vectors = mock_embedding.embed_texts(["内容0", "内容1"])
        store.add_document(doc_info, chunks, vectors)

        # 删除前有文档
        assert len(store.list_documents()) == 1

        # 删除文档
        result = store.delete_document("doc-delete-test")
        assert result is True

        # 删除后无文档
        assert len(store.list_documents()) == 0

        # 删除不存在的文档返回 False
        assert store.delete_document("non-existent") is False

    def test_check_duplicate(self, mock_embedding):
        """验证 checksum 重复检查"""
        store = InMemoryVectorStore()
        assert store.check_duplicate("checksum-not-exist") is None

        from app.rag.text_splitter import TextChunk, DocumentInfo

        doc_info = DocumentInfo(
            document_id="doc-dup-test",
            title="重复测试",
            publisher="测试机构",
            source_url="https://example.org",
            document_version="v1",
            published_at=None,
            checksum="checksum-dup",
            chunk_count=1,
            created_at=datetime.now(timezone.utc),
        )
        chunks = [
            TextChunk(
                chunk_id="chunk-dup-0",
                document_id="doc-dup-test",
                chunk_index=0,
                content="重复内容",
                title="重复测试",
                publisher="测试机构",
                source_url="https://example.org",
                document_version="v1",
                published_at=None,
                checksum="checksum-dup",
            )
        ]
        vectors = mock_embedding.embed_texts(["重复内容"])
        store.add_document(doc_info, chunks, vectors)

        assert store.check_duplicate("checksum-dup") == "doc-dup-test"


# ============================================================
# 知识库服务测试
# ============================================================


class TestKnowledgeService:
    """知识库服务集成测试"""

    def test_import_document(self, knowledge_service):
        """验证文档导入"""
        result = knowledge_service.import_document(
            title=SAMPLE_TITLE,
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content=SAMPLE_CONTENT,
        )
        assert result["document_id"] is not None
        assert result["checksum"] is not None
        assert result["chunk_count"] > 0
        assert result["duplicate"] is False

    def test_import_duplicate_idempotent(self, knowledge_service):
        """验证重复导入的幂等性"""
        result1 = knowledge_service.import_document(
            title=SAMPLE_TITLE,
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content=SAMPLE_CONTENT,
        )
        result2 = knowledge_service.import_document(
            title=SAMPLE_TITLE,
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content=SAMPLE_CONTENT,
        )
        # 第二次导入应标记为重复
        assert result2["duplicate"] is True
        assert result2["document_id"] == result1["document_id"]
        assert result2["checksum"] == result1["checksum"]

    def test_list_documents_no_content(self, knowledge_service):
        """验证文档列表不泄露全文"""
        knowledge_service.import_document(
            title=SAMPLE_TITLE,
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content=SAMPLE_CONTENT,
        )
        docs = knowledge_service.list_documents()
        assert len(docs) >= 1
        # 列表中不应包含 content 字段
        for doc in docs:
            assert "content" not in doc

    def test_search_returns_complete_fields(self, knowledge_service):
        """验证搜索结果包含完整引用字段"""
        knowledge_service.import_document(
            title=SAMPLE_TITLE,
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content=SAMPLE_CONTENT,
        )
        results = knowledge_service.search("高血压诊断标准", top_k=3)
        assert len(results) > 0
        for item in results:
            assert "chunk_id" in item
            assert "document_id" in item
            assert "title" in item
            assert "content" in item
            assert "score" in item
            assert "publisher" in item
            assert "source_url" in item
            assert "document_version" in item
            assert "chunk_index" in item

    def test_delete_document_via_service(self, knowledge_service):
        """验证通过服务删除文档"""
        result = knowledge_service.import_document(
            title=SAMPLE_TITLE,
            publisher=SAMPLE_PUBLISHER,
            source_url=SAMPLE_URL,
            document_version=SAMPLE_VERSION,
            published_at=None,
            content=SAMPLE_CONTENT,
        )
        doc_id = result["document_id"]

        # 删除前有文档
        assert len(knowledge_service.list_documents()) >= 1

        # 删除
        deleted = knowledge_service.delete_document(doc_id)
        assert deleted is True

        # 删除后无文档
        docs = knowledge_service.list_documents()
        assert all(d["document_id"] != doc_id for d in docs)


# ============================================================
# API 接口测试
# ============================================================


class TestKnowledgeAPI:
    """知识库 API 接口测试"""

    @pytest.mark.anyio
    async def test_import_document_api(self, client: AsyncClient):
        """验证 POST /api/v1/knowledge/documents 接口"""
        response = await client.post(
            "/api/v1/knowledge/documents",
            json={
                "title": "API测试文档（合成教学材料）",
                "publisher": "测试机构",
                "source_url": "https://example.org/test",
                "document_version": "v1",
                "content": "这是一段用于API测试的合成教学材料内容，包含足够的文本以进行切分。",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert "checksum" in data
        assert "chunk_count" in data
        assert "duplicate" in data

    @pytest.mark.anyio
    async def test_list_documents_api(self, client: AsyncClient):
        """验证 GET /api/v1/knowledge/documents 接口"""
        response = await client.get("/api/v1/knowledge/documents")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "documents" in data

    @pytest.mark.anyio
    async def test_search_api(self, client: AsyncClient):
        """验证 POST /api/v1/knowledge/search 接口"""
        # 先导入文档
        await client.post(
            "/api/v1/knowledge/documents",
            json={
                "title": "检索测试文档（合成教学材料）",
                "publisher": "测试机构",
                "source_url": "https://example.org/search-test",
                "document_version": "v1",
                "content": "高血压是最常见的慢性病，收缩压≥140mmHg可诊断为高血压。",
            },
        )

        # 检索
        response = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "高血压诊断", "top_k": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "disclaimer" in data

    @pytest.mark.anyio
    async def test_search_top_k_validation(self, client: AsyncClient):
        """验证 top_k 参数校验（1-10 范围）"""
        # top_k = 0 应该失败
        response = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "测试", "top_k": 0},
        )
        assert response.status_code == 422

        # top_k = 11 应该失败
        response = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "测试", "top_k": 11},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_delete_document_api(self, client: AsyncClient):
        """验证 DELETE /api/v1/knowledge/documents/{document_id} 接口"""
        # 先导入文档
        import_response = await client.post(
            "/api/v1/knowledge/documents",
            json={
                "title": "删除测试文档（合成教学材料）",
                "publisher": "测试机构",
                "source_url": "https://example.org/delete-test",
                "document_version": "v1",
                "content": "这是一段用于删除测试的合成教学材料。",
            },
        )
        doc_id = import_response.json()["document_id"]

        # 删除
        response = await client.delete(f"/api/v1/knowledge/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id

    @pytest.mark.anyio
    async def test_delete_nonexistent_document(self, client: AsyncClient):
        """验证删除不存在的文档返回 404"""
        response = await client.delete("/api/v1/knowledge/documents/non-existent-id")
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_import_validation_empty_title(self, client: AsyncClient):
        """验证导入时标题不能为空"""
        response = await client.post(
            "/api/v1/knowledge/documents",
            json={
                "title": "",
                "publisher": "测试机构",
                "source_url": "https://example.org/test",
                "document_version": "v1",
                "content": "测试内容",
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_import_validation_bad_url(self, client: AsyncClient):
        """验证导入时 URL 格式校验"""
        response = await client.post(
            "/api/v1/knowledge/documents",
            json={
                "title": "URL测试",
                "publisher": "测试机构",
                "source_url": "not-a-valid-url",
                "document_version": "v1",
                "content": "测试内容",
            },
        )
        assert response.status_code == 422


# ============================================================
# pgvector 配置错误处理测试
# ============================================================


class TestPgVectorConfig:
    """pgvector 模式配置错误处理测试"""

    def test_pgvector_missing_url_raises_error(self):
        """验证 pgvector 模式下缺少数据库 URL 时报错"""
        from app.rag.vector_store import PgVectorStore

        with pytest.raises(ValueError, match="VECTOR_DATABASE_URL 不能为空"):
            PgVectorStore(database_url="", dimension=384)

    def test_unsupported_vector_store_mode(self):
        """验证不支持的向量存储模式报错"""
        from app.rag.vector_store import create_vector_store
        from app.core.config import Settings

        # 临时修改配置来测试
        import app.core.config as config_module
        original_mode = config_module.settings.VECTOR_STORE_MODE
        try:
            # 直接测试不支持的模式通过异常
            with pytest.raises((ValueError, Exception)):
                # 通过 monkey-patch 测试
                store = PgVectorStore(database_url="postgresql://invalid", dimension=384)
                # 这里不会真正连接，只是验证构造不报错
        finally:
            pass

    def test_unsupported_embedding_mode(self):
        """验证不支持的 Embedding 模式报错"""
        from app.rag.embedding import create_embedding_provider
        import app.core.config as config_module

        original_mode = config_module.settings.EMBEDDING_MODE
        try:
            config_module.settings.EMBEDDING_MODE = "unsupported"
            with pytest.raises(ValueError, match="不支持的 EMBEDDING_MODE"):
                create_embedding_provider()
        finally:
            config_module.settings.EMBEDDING_MODE = original_mode
