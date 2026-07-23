"""
健康检查接口测试
使用 HTTPX 和 pytest 验证 /health 接口的正确性
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    """指定 async 测试后端为 asyncio"""
    return "asyncio"


@pytest.fixture
async def client():
    """创建异步测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_returns_200(client: AsyncClient):
    """验证 GET /health 返回 200 状态码"""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_health_status_is_ok(client: AsyncClient):
    """验证 /health 响应中 status 字段等于 ok"""
    response = await client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.anyio
async def test_health_has_required_fields(client: AsyncClient):
    """验证 /health 响应包含 service、version、environment 字段"""
    response = await client.get("/health")
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "environment" in data


@pytest.mark.anyio
async def test_health_service_name(client: AsyncClient):
    """验证 service 字段值正确"""
    response = await client.get("/health")
    data = response.json()
    assert data["service"] == "medical-safety-ai-service"


@pytest.mark.anyio
async def test_openapi_schema_generated(client: AsyncClient):
    """验证 OpenAPI 文档能够正常生成"""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "基层医疗安全型预问诊AI服务"
    assert schema["info"]["version"] == "0.1.0"
