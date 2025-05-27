#!/usr/bin/env python3
"""
Test basic memory functionality to ensure the MCP server isn't hanging.
"""

import asyncio
import json
from memory_mcp.domains.manager import MemoryDomainManager


async def test_basic_memory():
    """Test basic memory operations."""
    print("Testing basic memory functionality...")
    
    # Create a simple config
    config = {
        "memory": {
            "file_path": "/tmp/test_memory.json"
        },
        "embedding": {
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    }
    
    # Initialize domain manager
    manager = MemoryDomainManager(config)
    
    print("Initializing domain manager...")
    await manager.initialize()
    print("✅ Domain manager initialized")
    
    # Store a simple memory
    print("\nStoring a test memory...")
    memory_id = await manager.store_memory(
        memory_type="fact",
        content={"fact": "Test memory working"},
        importance=0.5
    )
    print(f"✅ Memory stored with ID: {memory_id}")
    
    # Retrieve the memory
    print("\nRetrieving memories...")
    memories = await manager.retrieve_memories(
        query="test memory",
        limit=1
    )
    print(f"✅ Retrieved {len(memories)} memories")
    
    # Get stats
    print("\nGetting memory stats...")
    stats = await manager.get_memory_stats()
    print(f"✅ Stats: {json.dumps(stats, indent=2)}")
    
    print("\n✅ All basic tests passed!")


if __name__ == "__main__":
    asyncio.run(test_basic_memory())