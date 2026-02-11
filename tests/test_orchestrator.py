"""Tests for orchestrator."""

import pytest
from fastapi.testclient import TestClient
from orchestrator.main import app
from orchestrator.config import get_settings
import structlog

# Test logger
logger = structlog.get_logger(__name__)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Hive Mind Orchestrator"
    assert data["version"] == "2.1.0"
    assert "endpoints" in data
    assert "endpoints" in data["endpoints"]


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "hot_memory" in data["services"]
    assert "cold_memory" in data["services"]


def test_list_agents(client: TestClient):
    """Test listing agents endpoint."""
    # Note: This will fail until agents are initialized
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    
    assert "agents" in data
    assert isinstance(data["agents"], list)


def test_get_stats(client: TestClient):
    """Test getting stats endpoint."""
    # Note: This will fail until memory managers are initialized
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    
    assert "hot_memory" in data or "cold_memory" in data or "metrics" in data


def test_get_memory_stats(client: TestClient):
    """Test getting memory stats endpoint."""
    # Note: This will fail until memory managers are initialized
    response = client.get("/memory")
    assert response.status_code == 200
    data = response.json()
    
    assert "hot" in data or "cold" in data


def test_dispatch_mission(client: TestClient):
    """Test mission dispatch endpoint."""
    # Note: This will fail until agents are initialized
    query_request = {
        "query": "What is the best way to use Redis?",
        "max_agents": 3
    }
    
    response = client.post("/query", json=query_request)
    assert response.status_code == 200
    data = response.json()
    
    assert data["query"] == "What is the best way to use Redis?"
    assert "results" in data
    assert isinstance(data["results"], list)
    assert "duration_ms" in data


@pytest.mark.asyncio
async def test_dispatch_mission_stream():
    """Test streaming mission dispatch."""
    # Note: This will fail until agents are initialized
    from fastapi.testclient import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        query_request = {
            "query": "Test streaming query",
            "max_agents": 2
        }
        
        response = await client.post("/query/stream", json=query_request)
        assert response.status_code == 200
        
        # Verify streaming response
        content = ""
        async for chunk in response.aiter_text():
            content += chunk
        
        # Should have start messages
        assert "initializing" in content.lower()
        assert "completed" in content.lower() or "failed" in content.lower()
        assert len(content) > 0


def test_settings():
    """Test settings loading."""
    settings = get_settings()
    
    assert settings.api_port == 8000
    assert settings.redis_ttl == 3600
    assert settings.lancedb_num_partitions == 256
