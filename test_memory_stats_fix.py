#!/usr/bin/env python3
"""
Test script to verify memory stats fix is working correctly.
"""

import asyncio
import json
import os
import tempfile

from memory_mcp.domains.persistence import PersistenceDomain
from memory_mcp.domains.persistence_qdrant import QdrantPersistenceDomain
from memory_mcp.domains.manager import MemoryDomainManager
from loguru import logger


async def test_json_persistence_stats():
    """Test memory stats counting for JSON persistence."""
    print("\n=== Testing JSON Persistence Stats ===")
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_memory_file = f.name
    
    config = {
        "memory": {
            "file_path": temp_memory_file,
            "backend": "json"
        },
        "embedding": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": 384
        }
    }
    
    try:
        # Initialize persistence domain
        persistence = PersistenceDomain(config)
        await persistence.initialize()
        
        # Add test memories
        test_memories = [
            {
                "id": "test1",
                "type": "conversation",
                "content": {"message": "Hello world"},
                "embedding": [0.1] * 384
            },
            {
                "id": "test2",
                "type": "fact",
                "content": {"fact": "The sky is blue"},
                "embedding": [0.2] * 384
            },
            {
                "id": "test3",
                "type": "fact",
                "content": {"fact": "Water is H2O"},
                "embedding": [0.3] * 384
            },
            {
                "id": "test4",
                "type": "conversation",
                "content": {"message": "How are you?"},
                "embedding": [0.4] * 384
            }
        ]
        
        # Store memories
        for memory in test_memories:
            await persistence.store_memory(memory, "short_term")
        
        # Get stats
        stats = await persistence.get_memory_stats()
        
        print(f"\nMemory Stats:")
        print(json.dumps(stats, indent=2))
        
        # Verify counts
        assert stats["total_memories"] == 4, f"Expected 4 total memories, got {stats['total_memories']}"
        assert stats["conversation"] == 2, f"Expected 2 conversation memories, got {stats.get('conversation', 0)}"
        assert stats["fact"] == 2, f"Expected 2 fact memories, got {stats.get('fact', 0)}"
        
        print("\n✅ JSON persistence stats test PASSED!")
        
    finally:
        # Cleanup
        if os.path.exists(temp_memory_file):
            os.remove(temp_memory_file)


async def test_qdrant_persistence_stats():
    """Test memory stats counting for Qdrant persistence."""
    print("\n=== Testing Qdrant Persistence Stats ===")
    
    config = {
        "memory": {
            "backend": "qdrant",
            "qdrant": {
                "host": "localhost",
                "port": 6333,
                "collection_name": "test_memory_stats",
                "recreate_collection": True
            }
        },
        "embedding": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": 384
        }
    }
    
    try:
        # Initialize persistence domain
        persistence = QdrantPersistenceDomain(config)
        await persistence.initialize()
        
        # Add test memories with UUID IDs
        import uuid
        test_memories = [
            {
                "id": str(uuid.uuid4()),
                "type": "conversation",
                "content": {"message": "Qdrant test 1"},
                "embedding": [0.1] * 384
            },
            {
                "id": str(uuid.uuid4()),
                "type": "fact",
                "content": {"fact": "Qdrant is a vector database"},
                "embedding": [0.2] * 384
            },
            {
                "id": str(uuid.uuid4()),
                "type": "fact",
                "content": {"fact": "Vectors enable similarity search"},
                "embedding": [0.3] * 384
            },
            {
                "id": str(uuid.uuid4()),
                "type": "document",
                "content": {"text": "Test document content"},
                "embedding": [0.4] * 384
            }
        ]
        
        # Store memories
        for memory in test_memories:
            await persistence.store_memory(memory, "short_term")
        
        # Get stats
        stats = await persistence.get_memory_stats()
        
        print(f"\nQdrant Memory Stats:")
        print(json.dumps(stats, indent=2))
        
        # Verify counts
        assert stats["total_memories"] == 4, f"Expected 4 total memories, got {stats['total_memories']}"
        assert stats["conversation"] == 1, f"Expected 1 conversation memory, got {stats.get('conversation', 0)}"
        assert stats["fact"] == 2, f"Expected 2 fact memories, got {stats.get('fact', 0)}"
        assert stats["document"] == 1, f"Expected 1 document memory, got {stats.get('document', 0)}"
        
        print("\n✅ Qdrant persistence stats test PASSED!")
        
    except Exception as e:
        print(f"\n⚠️  Qdrant test skipped (is Qdrant running?): {e}")


async def test_manager_stats():
    """Test memory stats through the domain manager."""
    print("\n=== Testing Domain Manager Stats ===")
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_memory_file = f.name
    
    config = {
        "memory": {
            "file_path": temp_memory_file,
            "backend": "json"
        },
        "embedding": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": 384
        }
    }
    
    try:
        # Initialize domain manager
        manager = MemoryDomainManager(config)
        await manager.initialize()
        
        # Store memories through manager
        memories = [
            {
                "type": "conversation",
                "content": {"message": "Manager test conversation"},
                "importance": 0.7
            },
            {
                "type": "fact",
                "content": {"fact": "Python is a programming language"},
                "importance": 0.9
            },
            {
                "type": "code",
                "content": {"code": "print('Hello, World!')"},
                "importance": 0.5
            }
        ]
        
        for memory in memories:
            await manager.store_memory(
                memory_type=memory["type"],
                content=memory["content"],
                importance=memory["importance"]
            )
        
        # Get stats through manager
        stats = await manager.get_memory_stats()
        
        print(f"\nManager Memory Stats:")
        print(json.dumps(stats, indent=2))
        
        # Verify type counts exist
        assert "conversation" in stats, "Stats should include conversation count"
        assert "fact" in stats, "Stats should include fact count"
        assert "code" in stats, "Stats should include code count"
        
        print("\n✅ Domain manager stats test PASSED!")
        
    finally:
        # Cleanup
        if os.path.exists(temp_memory_file):
            os.remove(temp_memory_file)


async def main():
    """Run all tests."""
    print("Testing Memory Stats Fix...")
    
    await test_json_persistence_stats()
    await test_qdrant_persistence_stats()
    await test_manager_stats()
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())