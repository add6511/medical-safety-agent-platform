"""
第六阶段测试：接口契约与统一输出补齐

覆盖：新接口200、统一字段、trace_id唯一性、追问生成、
高风险不可降级、不安全内容拦截、非法请求422。
"""

import re
import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.routes.preconsultation import set_preconsultation_service
from app.api.routes.knowledge import set_knowledge_service
from app.api.routes.triage import set_triage_service
from app.api.routes.safety import _check_text_safety
from app.rag.embedding import MockEmbeddingProvider
from app.rag.vector_store import InMemoryVectorStore
from app.services.knowledge_service import KnowledgeService
from app.services.preconsultation_service import PreconsultationService

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """创建测试客户端并初始化服务"""
    embedding_provider = MockEmbeddingProvider(dimension=384)
    vector_store = InMemoryVectorStore()
    knowledge_service = KnowledgeService(vector_store, embedding_provider)
    set_knowledge_service(knowledge_service)

    preconsultation_service = PreconsultationService(knowledge_service)
    set_preconsultation_service(preconsultation_service)
    set_triage_service(preconsultation_service)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# 合成教学请求数据
REVIEW_REQUEST = {
    "case_id": "synthetic-phase6-001",
    "age": 45,
    "symptoms": [{"name": "胸部不适", "severity": 7, "duration": "30分钟"}],
    "red_flags": ["persistent_chest_discomfort"],
    "free_text": "合成教学示例：持续胸部不适。",
    "model_suggested_risk": "LOW",
}

TRIAGE_REQUEST = {
    "case_id": "synthetic-phase6-002",
    "age": 30,
    "symptoms": [{"name": "头痛", "severity": 5, "duration": "2小时"}],
    "red_flags": [],
    "free_text": "合成教学示例：普通头痛。",
    "model_suggested_risk": "LOW",
}


# ============================================================
# 新接口返回 200
# ============================================================


class TestNewEndpointsReturn200:
    """两个新接口返回200"""

    @pytest.mark.anyio
    async def test_triage_analyze_returns_200(self, client: AsyncClient):
        """POST /api/v1/triage/analyze 返回 200"""
        response = await client.post("/api/v1/triage/analyze", json=TRIAGE_REQUEST)
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_safety_check_returns_200(self, client: AsyncClient):
        """POST /api/v1/safety/check 返回 200"""
        response = await client.post(
            "/api/v1/safety/check",
            json={"text": "合成教学示例文本，无危险内容。"},
        )
        assert response.status_code == 200


# ============================================================
# 统一字段完整性
# ============================================================


class TestUnifiedFields:
    """返回包含所有统一字段"""

    @pytest.mark.anyio
    async def test_review_has_unified_fields(self, client: AsyncClient):
        """preconsultation/review 包含统一字段"""
        response = await client.post("/api/v1/preconsultation/review", json=REVIEW_REQUEST)
        data = response.json()

        unified_fields = [
            "risk_level", "symptom_summary", "red_flags", "evidence",
            "citations", "missing_information", "followup_questions",
            "safety_status", "disclaimer", "trace_id",
        ]
        for field in unified_fields:
            assert field in data, f"review 缺少统一字段: {field}"

    @pytest.mark.anyio
    async def test_triage_has_unified_fields(self, client: AsyncClient):
        """triage/analyze 包含统一字段"""
        response = await client.post("/api/v1/triage/analyze", json=TRIAGE_REQUEST)
        data = response.json()

        unified_fields = [
            "risk_level", "symptom_summary", "red_flags", "evidence",
            "citations", "missing_information", "followup_questions",
            "safety_status", "disclaimer", "trace_id",
        ]
        for field in unified_fields:
            assert field in data, f"triage 缺少统一字段: {field}"

    @pytest.mark.anyio
    async def test_safety_check_has_unified_fields(self, client: AsyncClient):
        """safety/check 包含统一字段"""
        response = await client.post(
            "/api/v1/safety/check",
            json={"text": "合成教学文本。"},
        )
        data = response.json()

        required_fields = [
            "safety_status", "safety_flags", "sanitized_text",
            "needs_human_review", "disclaimer", "trace_id",
        ]
        for field in required_fields:
            assert field in data, f"safety/check 缺少字段: {field}"

    @pytest.mark.anyio
    async def test_review_retains_legacy_fields(self, client: AsyncClient):
        """review 保留旧字段以兼容"""
        response = await client.post("/api/v1/preconsultation/review", json=REVIEW_REQUEST)
        data = response.json()

        legacy_fields = [
            "final_risk_level", "matched_rules", "agent_trace",
            "ruleset_version", "model_version",
        ]
        for field in legacy_fields:
            assert field in data, f"review 缺少旧字段: {field}"


# ============================================================
# trace_id 测试
# ============================================================


class TestTraceId:
    """trace_id 是合法 UUID 且唯一"""

    @pytest.mark.anyio
    async def test_trace_id_is_valid_uuid(self, client: AsyncClient):
        """trace_id 是合法 UUID4"""
        response = await client.post("/api/v1/preconsultation/review", json=REVIEW_REQUEST)
        data = response.json()
        assert _UUID_RE.match(data["trace_id"]), f"trace_id 不是合法 UUID: {data['trace_id']}"

    @pytest.mark.anyio
    async def test_trace_id_unique_per_request(self, client: AsyncClient):
        """连续两次请求的 trace_id 不同"""
        r1 = await client.post("/api/v1/preconsultation/review", json=REVIEW_REQUEST)
        r2 = await client.post("/api/v1/preconsultation/review", json=REVIEW_REQUEST)
        assert r1.json()["trace_id"] != r2.json()["trace_id"]

    @pytest.mark.anyio
    async def test_triage_trace_id_is_valid(self, client: AsyncClient):
        """triage 的 trace_id 是合法 UUID"""
        response = await client.post("/api/v1/triage/analyze", json=TRIAGE_REQUEST)
        data = response.json()
        assert _UUID_RE.match(data["trace_id"])

    @pytest.mark.anyio
    async def test_safety_trace_id_is_valid(self, client: AsyncClient):
        """safety/check 的 trace_id 是合法 UUID"""
        response = await client.post(
            "/api/v1/safety/check",
            json={"text": "合成教学文本。"},
        )
        data = response.json()
        assert _UUID_RE.match(data["trace_id"])


# ============================================================
# 追问问题生成
# ============================================================


class TestFollowupQuestions:
    """缺少症状或年龄时能够生成追问问题"""

    @pytest.mark.anyio
    async def test_missing_age_generates_question(self, client: AsyncClient):
        """缺少年龄时生成追问"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json={
                "case_id": "test-followup-age",
                "symptoms": [{"name": "头痛", "severity": 3, "duration": "1小时"}],
                "free_text": "合成教学示例",
            },
        )
        data = response.json()
        assert len(data["followup_questions"]) > 0
        assert any("年龄" in q for q in data["followup_questions"])

    @pytest.mark.anyio
    async def test_missing_symptoms_generates_question(self, client: AsyncClient):
        """缺少症状时生成追问"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json={
                "case_id": "test-followup-symptoms",
                "age": 30,
                "free_text": "合成教学示例",
            },
        )
        data = response.json()
        assert any("症状" in q for q in data["followup_questions"])

    @pytest.mark.anyio
    async def test_missing_free_text_generates_question(self, client: AsyncClient):
        """缺少自由文本时生成追问"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json={
                "case_id": "test-followup-text",
                "age": 30,
                "symptoms": [{"name": "头痛", "severity": 3, "duration": "1小时"}],
            },
        )
        data = response.json()
        assert any("补充" in q or "描述" in q for q in data["followup_questions"])


# ============================================================
# 高风险不可降级
# ============================================================


class TestHighRiskNoDowngrade:
    """高风险规则不能被模型降低"""

    @pytest.mark.anyio
    async def test_critical_not_downgraded(self, client: AsyncClient):
        """CRITICAL 风险不被模型降级"""
        response = await client.post(
            "/api/v1/preconsultation/review",
            json={
                "case_id": "test-no-downgrade",
                "red_flags": ["consciousness_change"],
                "free_text": "合成教学示例",
                "model_suggested_risk": "LOW",
            },
        )
        data = response.json()
        assert data["risk_level"] == "CRITICAL"
        assert data["model_downgrade_blocked"] is True


# ============================================================
# 不安全内容拦截
# ============================================================


class TestUnsafeContentBlocked:
    """不安全诊断或用药内容被拦截"""

    @pytest.mark.anyio
    async def test_diagnosis_text_blocked(self, client: AsyncClient):
        """确定性诊断文本被拦截"""
        result = _check_text_safety("你就是得了心脏病")
        assert result["safety_status"] == "blocked"
        assert "contains_definitive_diagnosis" in result["safety_flags"]
        assert "你就是得了心脏病" not in result["sanitized_text"]

    @pytest.mark.anyio
    async def test_prescription_text_blocked(self, client: AsyncClient):
        """药物处方文本被拦截"""
        result = _check_text_safety("建议服用阿莫西林 500mg")
        assert result["safety_status"] == "blocked"
        assert "contains_prescription_or_dosage" in result["safety_flags"]

    @pytest.mark.anyio
    async def test_cancel_review_blocked(self, client: AsyncClient):
        """取消人工审核表述被拦截"""
        result = _check_text_safety("已经确认安全，不需要人工审核")
        assert result["safety_status"] == "blocked"
        assert "cancel_human_review_detected" in result["safety_flags"]

    @pytest.mark.anyio
    async def test_high_risk_without_review_flagged(self, client: AsyncClient):
        """HIGH 风险缺少人工审核时被标记"""
        result = _check_text_safety("正常文本", risk_level="HIGH", needs_human_review=False)
        assert "high_risk_missing_human_review" in result["safety_flags"]
        assert result["needs_human_review"] is True


# ============================================================
# 非法请求返回 422
# ============================================================


class TestInvalidRequest422:
    """非法请求返回 422"""

    @pytest.mark.anyio
    async def test_invalid_red_flag_422(self, client: AsyncClient):
        """非法红旗标识返回 422"""
        response = await client.post(
            "/api/v1/triage/analyze",
            json={
                "case_id": "test-invalid",
                "red_flags": ["nonexistent_flag"],
                "free_text": "合成教学",
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_invalid_risk_level_422(self, client: AsyncClient):
        """非法风险等级返回 422"""
        response = await client.post(
            "/api/v1/triage/analyze",
            json={
                "case_id": "test-invalid-risk",
                "free_text": "合成教学",
                "model_suggested_risk": "EXTREME",
            },
        )
        assert response.status_code == 422


# ============================================================
# 症状结构化
# ============================================================


class TestSymptomStructure:
    """症状结构化输出"""

    @pytest.mark.anyio
    async def test_symptom_summary_present(self, client: AsyncClient):
        """响应包含症状摘要"""
        response = await client.post("/api/v1/preconsultation/review", json=REVIEW_REQUEST)
        data = response.json()
        assert "胸部不适" in data["symptom_summary"]


# ============================================================
# 回归测试：手工验收缺陷修复
# ============================================================


class TestSafetyCheckRegression:
    """safety/check 回归测试"""

    @pytest.mark.anyio
    async def test_all_four_flags_detected(self, client: AsyncClient):
        """一次请求累计四个安全标志"""
        response = await client.post(
            "/api/v1/safety/check",
            json={
                "case_id": "synthetic-safety-001",
                "candidate_text": "你已经确诊为某疾病，不需要人工审核，建议服用某药500mg，每日3次。",
                "risk_level": "HIGH",
                "needs_human_review": False,
            },
        )
        assert response.status_code == 200
        data = response.json()

        flags = data["safety_flags"]
        assert "contains_definitive_diagnosis" in flags, f"缺少确定性诊断标记，当前flags={flags}"
        assert "contains_prescription_or_dosage" in flags, f"缺少处方/剂量标记，当前flags={flags}"
        assert "cancel_human_review_detected" in flags, f"缺少取消审核标记，当前flags={flags}"
        assert "high_risk_missing_human_review" in flags, f"缺少高风险标记，当前flags={flags}"
        assert len(flags) >= 4

        assert data["safety_status"] == "blocked"
        assert data["needs_human_review"] is True
        assert data["sanitized_text"] != ""
        assert "确诊为某疾病" not in data["sanitized_text"]
        assert "500mg" not in data["sanitized_text"]

    @pytest.mark.anyio
    async def test_safety_check_pass_for_normal_text(self, client: AsyncClient):
        """正常内容返回 pass"""
        response = await client.post(
            "/api/v1/safety/check",
            json={"text": "合成教学示例：普通症状描述，无危险内容。"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["safety_status"] == "pass"
        assert data["safety_flags"] == []
        assert data["needs_human_review"] is False
        assert "disclaimer" in data

    @pytest.mark.anyio
    async def test_sanitized_text_not_leaking(self, client: AsyncClient):
        """sanitized_text 不泄露原始不安全文本"""
        unsafe = "你已经确诊为某疾病，建议服用某药500mg"
        response = await client.post(
            "/api/v1/safety/check",
            json={"candidate_text": unsafe},
        )
        data = response.json()
        assert data["safety_status"] == "blocked"
        assert "确诊为某疾病" not in data["sanitized_text"]
        assert "500mg" not in data["sanitized_text"]
        assert "安全拦截" in data["sanitized_text"] or "已拦截" in data["sanitized_text"]
