"""Tests for hot memory (RedisVL)."""

import pytest
import pytest_asyncio
from orchestrator.memory.hot import HotMemoryManager
import numpy as np
import structlog

# Test logger
logger = structlog.get_logger(__name__)


@pytest_asyncio.fixture
async def hot_memory():
    """Create a hot memory manager for testing."""
    manager = HotMemoryManager()
    # Note: In real tests, we'd mock Redis or use test Redis instance
    # await manager.initialize()
    yield manager
    # Cleanup happens in manager (handled by Redis TTL)


@pytest.mark.asyncio
async def test_write_and_read(hot_memory: HotMemoryManager):
    """Test writing and reading from hot memory."""
    pytest.skip("Requires test Redis instance")
    
    agent_id = "test_agent"
    content = "Test thought"
    embedding = list(np.random.rand(768).astype(float))
    
    # Write
    key = await hot_memory.write(agent_id, content, embedding)
    assert key.startswith(f"{agent_id}:thought:")
    
    # Read
    entries = await hot_memory.read(agent_id, limit=5)
    assert len(entries) >= 1
    assert entries[0]["content"] == content


@pytest.mark.asyncio
async def test_semantic_search(hot_memory: HotMemoryManager):
    """Test semantic vector search."""
    pytest.skip("Requires test Redis instance")
    
    agent_id = "test_agent"
    query_vector = list(np.random.rand(768).astype(float))
    
    # Write some test data
    for i in range(10):
        embedding = list(np.random.rand(768).astype(float))
        await hot_memory.write(agent_id, f"Test content {i}", embedding)
    
    # Search
    results = await hot_memory.semantic_search(query_vector, num_results=5)
    assert len(results) <= 5


@pytest.mark.asyncio
async def test_agent_filter(hot_memory: HotMemoryManager):
    """Test filtering by agent ID."""
    pytest.skip("Requires test Redis instance")
    
    agent1 = "agent_1"
    agent2 = "agent_2"
    
    # Write to both agents
    for i in range(5):
        embedding = list(np.random.rand(768).astype(float))
        await hot_memory.write(agent1, f"Agent1 content {i}", embedding)
        await hot_memory.write(agent2, f"Agent2 content {i}", embedding)
    
    # Search with filter
    query_vector = list(np.random.rand(768).astype(float))
    results = await hot_memory.semantic_search(query_vector, agent_filter=agent1)
    
    # All results should be from agent1
    for result in results:
        assert result["agent_id"] == agent1


@pytest.mark.asyncio
async def test_get_stats(hot_memory: HotMemoryManager):
    """Test getting hot memory statistics."""
    pytest.skip("Requires test Redis instance")
    
    stats = await hot_memory.get_stats()
    assert isinstance(stats, dict)
    assert "total_keys" in stats or "index_info" in stats


@pytest.mark.asyncio
async def test_get_by_prefix(hot_memory: HotMemoryManager):
    """Test getting entries by prefix."""
    pytest.skip("Requires test Redis instance")
    
    prefix1 = "web"
    prefix2 = "code"
    
    # Write to different agents with prefixes
    for i in range(5):
        embedding = list(np.random.rand(768).astype(float))
        await hot_memory.write(f"res_01_web", f"Web content {i}", embedding)
        await hot_memory.write(f"res_02_code", f"Code content {i}", embedding)
    
    # Get by prefix
    web_entries = await hot_memory.get_by_prefix("web", limit=100)
    assert len(web_entries) >= 5
    
    code_entries = await hot_memory.get_by_prefix("code", limit=100)
    assert len(code_entries) >= 5
    
    # Verify entries are from correct agents
    for entry in web_entries:
        assert entry["agent_id"] == "res_01_web"
    
    for entry in code_entries:
        assert entry["agent_id"] == "res_02_code"
