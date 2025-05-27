"""
Unit tests for memory stats functionality.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import MagicMock, patch

from memory_mcp.domains.persistence import PersistenceDomain
from memory_mcp.domains.manager import MemoryDomainManager


@pytest.fixture
def temp_memory_file():
    """Create a temporary memory file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def test_config(temp_memory_file):
    """Create test configuration."""
    return {
        "memory": {
            "file_path": temp_memory_file,
            "backend": "json"
        },
        "embedding": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": 384,
            "cache_dir": "/tmp/test_cache"
        }
    }


@pytest.mark.asyncio
async def test_persistence_stats_counting(test_config):
    """Test that persistence domain correctly counts memories by type."""
    persistence = PersistenceDomain(test_config)
    await persistence.initialize()
    
    # Store various types of memories
    memories = [
        {"id": "1", "type": "conversation", "content": {"msg": "Test 1"}, "embedding": [0.1] * 384},
        {"id": "2", "type": "conversation", "content": {"msg": "Test 2"}, "embedding": [0.2] * 384},
        {"id": "3", "type": "fact", "content": {"fact": "Test fact"}, "embedding": [0.3] * 384},
        {"id": "4", "type": "document", "content": {"doc": "Test doc"}, "embedding": [0.4] * 384},
        {"id": "5", "type": "entity", "content": {"entity": "Test entity"}, "embedding": [0.5] * 384},
        {"id": "6", "type": "reflection", "content": {"thought": "Test reflection"}, "embedding": [0.6] * 384},
        {"id": "7", "type": "code", "content": {"code": "print('test')"}, "embedding": [0.7] * 384},
    ]
    
    # Store in different tiers
    for i, memory in enumerate(memories):
        tier = "short_term" if i < 4 else "long_term"
        await persistence.store_memory(memory, tier)
    
    # Get stats
    stats = await persistence.get_memory_stats()
    
    # Verify counts
    assert stats["total_memories"] == 7
    assert stats["short_term_count"] == 4
    assert stats["long_term_count"] == 3
    assert stats["conversation"] == 2
    assert stats["fact"] == 1
    assert stats["document"] == 1
    assert stats["entity"] == 1
    assert stats["reflection"] == 1
    assert stats["code"] == 1


@pytest.mark.asyncio
async def test_stats_update_on_memory_deletion(test_config):
    """Test that stats are updated when memories are deleted."""
    persistence = PersistenceDomain(test_config)
    await persistence.initialize()
    
    # Store memories
    memories = [
        {"id": "del1", "type": "conversation", "content": {"msg": "Delete me"}, "embedding": [0.1] * 384},
        {"id": "del2", "type": "fact", "content": {"fact": "Delete me too"}, "embedding": [0.2] * 384},
        {"id": "keep1", "type": "conversation", "content": {"msg": "Keep me"}, "embedding": [0.3] * 384},
    ]
    
    for memory in memories:
        await persistence.store_memory(memory, "short_term")
    
    # Initial stats
    stats = await persistence.get_memory_stats()
    assert stats["total_memories"] == 3
    assert stats["conversation"] == 2
    assert stats["fact"] == 1
    
    # Delete memories
    await persistence.delete_memories(["del1", "del2"])
    
    # Updated stats
    stats = await persistence.get_memory_stats()
    assert stats["total_memories"] == 1
    assert stats["conversation"] == 1
    assert stats["fact"] == 0


@pytest.mark.asyncio
async def test_stats_with_empty_store(test_config):
    """Test stats with no memories stored."""
    persistence = PersistenceDomain(test_config)
    await persistence.initialize()
    
    stats = await persistence.get_memory_stats()
    
    # All counts should be 0
    assert stats["total_memories"] == 0
    assert stats["conversation"] == 0
    assert stats["fact"] == 0
    assert stats["document"] == 0
    assert stats["entity"] == 0
    assert stats["reflection"] == 0
    assert stats["code"] == 0


@pytest.mark.asyncio
async def test_manager_stats_aggregation(test_config):
    """Test that domain manager properly aggregates stats."""
    manager = MemoryDomainManager(test_config)
    await manager.initialize()
    
    # Store memories through manager
    await manager.store_memory("conversation", {"message": "Hello"}, 0.7)
    await manager.store_memory("fact", {"fact": "Sky is blue"}, 0.9)
    await manager.store_memory("code", {"code": "def hello(): pass"}, 0.5)
    
    # Get aggregated stats
    stats = await manager.get_memory_stats()
    
    # Verify basic counts
    assert stats["total_memories"] == 3
    assert stats["conversation"] == 1
    assert stats["fact"] == 1
    assert stats["code"] == 1
    
    # Verify domain-specific stats are included
    assert "episodic_domain" in stats
    assert "semantic_domain" in stats
    assert "temporal_domain" in stats


@pytest.mark.asyncio
async def test_stats_persistence_across_reloads(test_config):
    """Test that stats remain accurate after reloading from disk."""
    # First session - store memories
    persistence1 = PersistenceDomain(test_config)
    await persistence1.initialize()
    
    memories = [
        {"id": "p1", "type": "conversation", "content": {"msg": "Persist 1"}, "embedding": [0.1] * 384},
        {"id": "p2", "type": "fact", "content": {"fact": "Persist 2"}, "embedding": [0.2] * 384},
    ]
    
    for memory in memories:
        await persistence1.store_memory(memory, "short_term")
    
    stats1 = await persistence1.get_memory_stats()
    
    # Second session - reload and verify
    persistence2 = PersistenceDomain(test_config)
    await persistence2.initialize()
    
    stats2 = await persistence2.get_memory_stats()
    
    # Stats should match
    assert stats2["total_memories"] == stats1["total_memories"]
    assert stats2["conversation"] == stats1["conversation"]
    assert stats2["fact"] == stats1["fact"]


@pytest.mark.asyncio
async def test_stats_with_tier_promotion(test_config):
    """Test stats updates when memories are promoted between tiers."""
    persistence = PersistenceDomain(test_config)
    await persistence.initialize()
    
    # Store in short term
    memory = {"id": "promote1", "type": "fact", "content": {"fact": "Important"}, "embedding": [0.1] * 384}
    await persistence.store_memory(memory, "short_term")
    
    stats = await persistence.get_memory_stats()
    assert stats["short_term_count"] == 1
    assert stats["long_term_count"] == 0
    
    # Promote to long term
    await persistence.promote_memory("promote1", "long_term")
    
    stats = await persistence.get_memory_stats()
    assert stats["short_term_count"] == 0
    assert stats["long_term_count"] == 1
    assert stats["fact"] == 1  # Type count should remain the same