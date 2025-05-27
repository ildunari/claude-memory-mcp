#!/usr/bin/env python3
"""
Debug script to identify what's causing the 2+ minute startup delay
"""

import time
import asyncio
import sys
from pathlib import Path

# Add project to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from memory_mcp.utils.config import load_config
from memory_mcp.domains.manager import MemoryDomainManager


def time_operation(name, func, *args, **kwargs):
    """Time an operation and print results"""
    print(f"⏱️  Starting: {name}")
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"✅ Completed: {name} in {elapsed:.2f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed: {name} in {elapsed:.2f}s - {e}")
        raise


async def time_async_operation(name, coro):
    """Time an async operation and print results"""
    print(f"⏱️  Starting: {name}")
    start_time = time.time()
    try:
        result = await coro
        elapsed = time.time() - start_time
        print(f"✅ Completed: {name} in {elapsed:.2f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed: {name} in {elapsed:.2f}s - {e}")
        raise


async def debug_startup():
    """Debug the startup timing"""
    print("🔍 Debugging Memory MCP Server startup timing...\n")
    
    # Step 1: Load config
    config_path = str(project_dir / "../.memory_mcp/config/config.json")
    config = time_operation("Load configuration", load_config, config_path)
    
    print(f"📋 Configuration backend: {config.get('memory', {}).get('backend', 'json')}")
    print(f"📋 Embedding model: {config.get('embedding', {}).get('default_model', 'unknown')}")
    print()
    
    # Step 2: Create MemoryDomainManager (constructor only)
    manager = time_operation("MemoryDomainManager constructor", MemoryDomainManager, config)
    
    # Step 3: Initialize MemoryDomainManager (async initialize)
    await time_async_operation("MemoryDomainManager.initialize()", manager.initialize())
    
    print("\n🎉 Startup timing analysis complete!")
    

if __name__ == "__main__":
    asyncio.run(debug_startup())