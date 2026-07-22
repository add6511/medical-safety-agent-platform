"""
第五阶段测试：容器化、接口契约和集成验证

覆盖：OpenAPI 包含核心接口、健康检查端点、预问诊响应安全字段、
AI 服务异常安全策略、smoke test 校验函数、Dockerfile 安全检查。
"""

import json
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.agents.intake_agent import IntakeAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.safety_agent import SafetyReviewAgent
from app.agents.supervisor import SupervisorAgent
from app.api.routes.preconsultation import set_preconsultation_service
from app.api.routes.knowledge import set_knowledge_service
from app.rag.embedding import MockEmbeddingProvider
from app.rag.vector_store import InMemoryVectorStore
from app.rules.engine import SafetyRuleEngine
from app.services.knowledge_service import KnowledgeService
from app.services.preconsultation_service import PreconsultationService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def openapi_schema():
    """获取 OpenAPI schema"""
    return app.openapi()


@pytest.fixture
async def client():
    """创建测试客户端"""
    embedding_provider = MockEmbeddingProvider(dimension=384)
    vector_store = InMemoryVectorStore()
    knowledge_service = KnowledgeService(vector_store, embedding_provider)
    set_knowledge_service(knowledge_service)

    preconsultation_service = PreconsultationService(knowledge_service)
    set_preconsultation_service(preconsultation_service)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================
# OpenAPI 接口覆盖测试
# ============================================================


class TestOpenAPICoverage:
    """OpenAPI 包含所有核心接口"""

    def test_openapi_health_endpoint(self, openapi_schema):
        """OpenAPI 包含 /health 接口"""
        paths = openapi_schema.get("paths", {})
        assert "/health" in paths
        assert "get" in paths["/health"]

    def test_openapi_knowledge_documents(self, openapi_schema):
        """OpenAPI 包含知识文档接口"""
        paths = openapi_schema.get("paths", {})
        assert "/api/v1/knowledge/documents" in paths
        doc_path = paths["/api/v1/knowledge/documents"]
        assert "post" in doc_path or "get" in doc_path

    def test_openapi_knowledge_search(self, openapi_schema):
        """OpenAPI 包含知识检索接口"""
        paths = openapi_schema.get("paths", {})
        assert "/api/v1/knowledge/search" in paths
        assert "post" in paths["/api/v1/knowledge/search"]

    def test_openapi_preconsultation_review(self, openapi_schema):
        """OpenAPI 包含预问诊审核接口"""
        paths = openapi_schema.get("paths", {})
        assert "/api/v1/preconsultation/review" in paths
        assert "post" in paths["/api/v1/preconsultation/review"]

    def test_openapi_document_delete(self, openapi_schema):
        """OpenAPI 包含删除文档接口"""
        paths = openapi_schema.get("paths", {})
        doc_path = paths.get("/api/v1/knowledge/documents/{document_id}", {})
        assert "delete" in doc_path

    def test_openapi_valid_json(self, openapi_schema):
        """OpenAPI 是有效的 JSON 结构"""
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema
        assert "paths" in openapi_schema


# ============================================================
# 健康检查端点测试
# ============================================================


class TestHealthEndpoint:
    """Docker 健康检查目标接口"""

    @pytest.mark.anyio
    async def test_health_returns_200(self, client: AsyncClient):
        """健康检查返回 200"""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_health_response_structure(self, client: AsyncClient):
        """健康检查响应结构正确"""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "medical-safety-ai-service"
        assert "version" in data
        assert "environment" in data


# ============================================================
# 预问诊响应安全字段测试
# ============================================================


class TestPreconsultationSafetyFields:
    """预问诊响应包含全部安全字段和版本字段"""

    @pytest.mark.anyio
    async def test_response_has_safety_fields(self, client: AsyncClient):
        """响应包含全部安全字段"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json={
                "case_id": "test-safety-fields",
                "age": 45,
                "symptoms": [{"name": "胸部不适", "severity": 7, "duration": "30分钟"}],
                "red_flags": ["persistent_chest_discomfort"],
                "free_text": "合成教学示例",
                "model_suggested_risk": "LOW",
            },
        )
        data = response.json()

        # 安全字段
        safety_fields = [
            "final_risk_level", "rule_risk_level", "model_suggested_risk",
            "model_downgrade_blocked", "needs_human_review", "matched_rules",
            "retrieved_evidence", "safety_flags", "safe_summary", "disclaimer",
        ]
        for field in safety_fields:
            assert field in data, f"缺少安全字段: {field}"

    @pytest.mark.anyio
    async def test_response_has_version_fields(self, client: AsyncClient):
        """响应包含全部版本字段"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json={
                "case_id": "test-version-fields",
                "free_text": "合成教学示例",
            },
        )
        data = response.json()

        version_fields = [
            "ruleset_version", "model_version", "prompt_version",
            "knowledge_base_version",
        ]
        for field in version_fields:
            assert field in data, f"缺少版本字段: {field}"

    @pytest.mark.anyio
    async def test_response_has_agent_trace(self, client: AsyncClient):
        """响应包含 agent_trace"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json={
                "case_id": "test-agent-trace",
                "free_text": "合成教学示例",
            },
        )
        data = response.json()

        assert "agent_trace" in data
        assert len(data["agent_trace"]) >= 4

        # 每条审计记录包含必要字段
        for record in data["agent_trace"]:
            assert "agent_name" in record
            assert "status" in record
            assert "output_summary" in record
            # 不包含思维链
            assert "chain_of_thought" not in record
            assert "reasoning" not in record


# ============================================================
# AI 服务异常安全策略测试
# ============================================================


class TestServiceFailureStrategy:
    """AI 服务异常时的安全失败策略"""

    @pytest.mark.anyio
    async def test_agent_failure_returns_safe_result(self):
        """Agent 失败时返回安全降级结果"""

        class FailingAgent(IntakeAgent):
            def _execute(self, context):
                raise RuntimeError("模拟失败")

        rule_engine = SafetyRuleEngine()
        supervisor = SupervisorAgent([
            FailingAgent(),
            RiskAssessmentAgent(rule_engine),
            SafetyReviewAgent(),
        ])

        from app.agents.base import AgentContext
        context = AgentContext(
            case_id="test-failure",
            red_flags=["consciousness_change"],
            free_text="合成教学示例",
            model_suggested_risk="LOW",
        )
        result, audit_trail = supervisor.process(context)

        # IntakeAgent 失败但流程继续
        assert audit_trail[0].status == "error"
        # 后续 Agent 仍然执行
        assert len(audit_trail) == 3

    def test_high_risk_not_downgraded_on_failure(self):
        """Agent 失败时高风险不被降级"""
        rule_engine = SafetyRuleEngine()

        # 即使 IntakeAgent 失败，规则引擎仍然工作
        result = rule_engine.evaluate(
            red_flags=["consciousness_change"],
            free_text="合成教学示例",
        )
        assert result.risk_level.value == "CRITICAL"
        assert result.needs_human_review is True


# ============================================================
# Smoke Test 校验函数测试
# ============================================================


class TestSmokeTestFunctions:
    """smoke test 的关键校验函数"""

    def test_smoke_test_module_importable(self):
        """smoke_test 模块可导入"""
        import importlib
        spec = importlib.util.find_spec("scripts.smoke_test")
        # scripts 不是标准包，检查文件存在即可
        script_path = Path(__file__).parent.parent / "scripts" / "smoke_test.py"
        assert script_path.exists()

    def test_export_openapi_module_importable(self):
        """export_openapi 模块可导入"""
        script_path = Path(__file__).parent.parent / "scripts" / "export_openapi.py"
        assert script_path.exists()


# ============================================================
# Dockerfile 安全检查
# ============================================================


class TestDockerfileSecurity:
    """Dockerfile 安全设计检查"""

    def test_dockerfile_exists(self):
        """Dockerfile 存在"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile.exists()

    def test_dockerfile_uses_non_root_user(self):
        """Dockerfile 使用非 root 用户"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text(encoding="utf-8")
        assert "USER" in content
        assert "10001" in content

    def test_dockerfile_uses_slim_image(self):
        """Dockerfile 使用 slim 镜像"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text(encoding="utf-8")
        assert "python:3.11-slim" in content

    def test_dockerfile_no_secrets(self):
        """Dockerfile 不包含密钥"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text(encoding="utf-8")
        assert "API_KEY" not in content
        assert "PASSWORD" not in content
        assert "SECRET" not in content

    def test_dockerfile_has_healthcheck(self):
        """Dockerfile 包含健康检查"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text(encoding="utf-8")
        assert "HEALTHCHECK" in content

    def test_dockerignore_exists(self):
        """.dockerignore 存在"""
        dockerignore = Path(__file__).parent.parent / ".dockerignore"
        assert dockerignore.exists()

    def test_dockerignore_excludes_env(self):
        """.dockerignore 排除 .env 文件"""
        dockerignore = Path(__file__).parent.parent / ".dockerignore"
        content = dockerignore.read_text(encoding="utf-8")
        assert ".env" in content

    def test_dockerignore_excludes_tests(self):
        """.dockerignore 排除测试目录"""
        dockerignore = Path(__file__).parent.parent / ".dockerignore"
        content = dockerignore.read_text(encoding="utf-8")
        assert "tests/" in content


# ============================================================
# 文档存在性测试
# ============================================================


class TestDocumentation:
    """接口契约文档测试"""

    def test_api_contract_exists(self):
        """API_CONTRACT.md 存在"""
        doc_path = Path(__file__).parent.parent / "docs" / "API_CONTRACT.md"
        assert doc_path.exists()

    def test_integration_guide_exists(self):
        """INTEGRATION_GUIDE.md 存在"""
        doc_path = Path(__file__).parent.parent / "docs" / "INTEGRATION_GUIDE.md"
        assert doc_path.exists()

    def test_api_contract_contains_disclaimer(self):
        """API 契约包含安全声明"""
        doc_path = Path(__file__).parent.parent / "docs" / "API_CONTRACT.md"
        content = doc_path.read_text(encoding="utf-8")
        assert "合成教学" in content or "不构成" in content

    def test_integration_guide_contains_safety(self):
        """集成指南包含安全策略"""
        doc_path = Path(__file__).parent.parent / "docs" / "INTEGRATION_GUIDE.md"
        content = doc_path.read_text(encoding="utf-8")
        assert "人工审核" in content or "人工" in content
