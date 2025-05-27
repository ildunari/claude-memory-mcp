#!/usr/bin/env python3
"""Test Qdrant integration"""

import asyncio
import json
from memory_mcp.utils.config import load_config
from memory_mcp.domains.manager import MemoryDomainManager

async def test_integration():
    # Load Qdrant config
    config = load_config("config.qdrant.json")
    
    # Initialize domain manager
    manager = MemoryDomainManager(config)
    await manager.initialize()
    
    print("✅ Successfully initialized with Qdrant backend!")
    
    # Test storing a memory
    memory_id = await manager.store_memory(
        memory_type="fact",
        content={"text": "Qdrant is a vector database"},
        importance=0.8,
        metadata={"source": "test"}
    )
    print(f"✅ Stored memory with ID: {memory_id}")
    
    # Test retrieving memories
    memories = await manager.retrieve_memories(
        query="vector database",
        limit=5
    )
    print(f"✅ Retrieved {len(memories)} memories")
    
    # Test memory stats
    stats = await manager.get_memory_stats()
    print(f"✅ Memory stats: {json.dumps(stats, indent=2)}")
    
    print("\n🎉 All tests passed! Qdrant integration is working.")

if __name__ == "__main__":
    asyncio.run(test_integration())