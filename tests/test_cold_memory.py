"""Tests for cold memory (LanceDB)."""

import pytest
import pytest_asyncio
from orchestrator.memory.cold import ColdMemoryManager
import numpy as np
import structlog

# Test logger
logger = structlog.get_logger(__name__)


@pytest_asyncio.fixture
async def cold_memory(tmp_path):
    """Create a cold memory manager with temporary path."""
    import tempfile
    import os
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "test_cold_memory.lance")
    
    manager = ColdMemoryManager()
    
    # Patch the settings to use temp path
    from unittest.mock import patch
    with patch('orchestrator.config.get_settings') as mock_settings:
        mock_settings.return_value.lancedb_path = temp_path
        
        await manager.initialize()
        yield manager
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_archive_and_search(cold_memory: ColdMemoryManager):
    """Test archiving and searching in cold memory."""
    
    # Create test entries
    entries = [
        {
            "agent_id": "test_agent",
            "content": f"Test content {i}",
            "timestamp": i,
            "data_type": "thought",
            "metadata": {"test": True},
            "embedding": list(np.random.rand(768).astype(float))
        }
        for i in range(10)
    ]
    
    # Archive
    archived_count = await cold_memory.archive(entries)
    assert archived_count == 10
    
    # Search
    query_vector = list(np.random.rand(768).astype(float))
    results = await cold_memory.search(query_vector, num_results=5)
    assert len(results) <= 5


@pytest.mark.asyncio
async def test_get_by_agent(cold_memory: ColdMemoryManager):
    """Test getting archived entries for a specific agent."""
    
    # Archive entries
    entries = [
        {
            "agent_id": "test_agent",
            "content": f"Content {i}",
            "timestamp": i,
            "data_type": "thought",
            "metadata": {},
            "embedding": list(np.random.rand(768).astype(float))
        }
        for i in range(20)
    ]
    
    await cold_memory.archive(entries)
    
    # Get by agent
    agent_entries = await cold_memory.get_by_agent("test_agent", limit=100)
    assert len(agent_entries) >= 20
    
    # Verify all entries are from the correct agent
    for entry in agent_entries:
        assert entry["agent_id"] == "test_agent"


@pytest.mark.asyncio
async def test_get_stats(cold_memory: ColdMemoryManager):
    """Test getting cold memory statistics."""
    
    stats = await cold_memory.get_stats()
    assert isinstance(stats, dict)
    assert "total_rows" in stats or "indices" in stats


@pytest.mark.asyncio
async def test_optimize_indices(cold_memory: ColdMemoryManager):
    """Test index optimization."""
    
    # This should not raise an error
    await cold_memory.optimize_indices()
    
    stats = await cold_memory.get_stats()
    assert len(stats.get("indices", [])) >= 1
