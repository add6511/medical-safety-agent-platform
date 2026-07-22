"""
预问诊审核 API 测试

覆盖：API 正常返回 200、非法输入返回 422、
完整响应字段验证、引用字段完整性。
"""

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
async def client():
    """创建测试客户端并初始化服务"""
    # 初始化知识库服务
    embedding_provider = MockEmbeddingProvider(dimension=384)
    vector_store = InMemoryVectorStore()
    knowledge_service = KnowledgeService(vector_store, embedding_provider)
    set_knowledge_service(knowledge_service)

    # 初始化预问诊服务
    preconsultation_service = PreconsultationService(knowledge_service)
    set_preconsultation_service(preconsultation_service)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# 合成教学病例
SYNTHETIC_LOW_RISK = {
    "case_id": "synthetic-case-low",
    "age": 30,
    "symptoms": [{"name": "轻微头痛", "severity": 3, "duration": "1小时"}],
    "red_flags": [],
    "free_text": "合成教学病例，轻微不适。",
    "model_suggested_risk": "LOW",
}

SYNTHETIC_HIGH_RISK = {
    "case_id": "synthetic-case-high",
    "age": 55,
    "symptoms": [{"name": "胸部不适", "severity": 8, "duration": "30分钟"}],
    "red_flags": ["persistent_chest_discomfort"],
    "free_text": "合成教学病例，持续胸部不适。",
    "model_suggested_risk": "LOW",
}

SYNTHETIC_CRITICAL_RISK = {
    "case_id": "synthetic-case-critical",
    "age": 70,
    "symptoms": [{"name": "意识模糊", "severity": 9, "duration": "10分钟"}],
    "red_flags": ["consciousness_change"],
    "free_text": "合成教学病例，意识状态变化。",
    "model_suggested_risk": "LOW",
}


class TestPreconsultationAPI:
    """预问诊 API 接口测试"""

    @pytest.mark.anyio
    async def test_api_returns_200_low_risk(self, client: AsyncClient):
        """低风险用例 API 返回 200"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json=SYNTHETIC_LOW_RISK,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_api_returns_200_high_risk(self, client: AsyncClient):
        """高风险用例 API 返回 200"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json=SYNTHETIC_HIGH_RISK,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_api_returns_200_critical_risk(self, client: AsyncClient):
        """极高风险用例 API 返回 200"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json=SYNTHETIC_CRITICAL_RISK,
        )
        assert response.status_code == 200


class TestResponseFields:
    """响应字段完整性测试"""

    @pytest.mark.anyio
    async def test_response_has_all_required_fields(self, client: AsyncClient):
        """响应包含所有必要字段"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json=SYNTHETIC_LOW_RISK,
        )
        data = response.json()

        required_fields = [
            "case_id", "final_risk_level", "rule_risk_level",
            "model_suggested_risk", "model_downgrade_blocked",
            "needs_human_review", "matched_rules", "retrieved_evidence",
            "safety_flags", "safe_summary", "disclaimer", "agent_trace",
            "ruleset_version", "model_version", "prompt_version",
            "knowledge_base_version",
        ]
        for field in required_fields:
            assert field in data, f"响应缺少字段: {field}"

    @pytest.mark.anyio
    async def test_disclaimer_present(self, client: AsyncClient):
        """免责声明存在"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json=SYNTHETIC_LOW_RISK,
        )
        data = response.json()
        assert "教学" in data["disclaimer"]

    @pytest.mark.anyio
    async def test_agent_trace_no_chain_of_thought(self, client: AsyncClient):
        """agent_trace 不包含思维链字段"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json=SYNTHETIC_LOW_RISK,
        )
        data = response.json()

        for record in data["agent_trace"]:
            assert "chain_of_thought" not in record
            assert "reasoning" not in record


class TestModelDowngradeBlocking:
    """模型降级阻止 API 测试"""

    @pytest.mark.anyio
    async def test_high_risk_not_downgraded(self, client: AsyncClient):
        """规则 HIGH + 模型 LOW 时，最终风险保持 HIGH"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json=SYNTHETIC_HIGH_RISK,
        )
        data = response.json()

        assert data["rule_risk_level"] == "HIGH"
        assert data["final_risk_level"] == "HIGH"
        assert data["model_downgrade_blocked"] is True
        assert data["needs_human_review"] is True

    @pytest.mark.anyio
    async def test_critical_risk_not_downgraded(self, client: AsyncClient):
        """规则 CRITICAL + 模型 LOW 时，最终风险保持 CRITICAL"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json=SYNTHETIC_CRITICAL_RISK,
        )
        data = response.json()

        assert data["rule_risk_level"] == "CRITICAL"
        assert data["final_risk_level"] == "CRITICAL"
        assert data["model_downgrade_blocked"] is True


class TestValidation:
    """输入校验测试"""

    @pytest.mark.anyio
    async def test_invalid_red_flag_returns_422(self, client: AsyncClient):
        """非法红旗标识返回 422"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json={
                "case_id": "test-invalid",
                "red_flags": ["non_existent_flag"],
                "free_text": "测试",
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_invalid_risk_level_returns_422(self, client: AsyncClient):
        """非法风险等级返回 422"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json={
                "case_id": "test-invalid-risk",
                "free_text": "测试",
                "model_suggested_risk": "EXTREME",
            },
        )
        assert response.status_code == 422


class TestCitationFields:
    """引用字段完整性测试"""

    @pytest.mark.anyio
    async def test_matched_rules_have_display_message(self, client: AsyncClient):
        """命中规则包含展示信息"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json=SYNTHETIC_HIGH_RISK,
        )
        data = response.json()

        for rule in data["matched_rules"]:
            assert "rule_id" in rule
            assert "display_message" in rule
            assert "risk_level" in rule
