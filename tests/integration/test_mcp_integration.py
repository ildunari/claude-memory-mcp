#!/usr/bin/env python3
"""
Test full MCP integration with auto-capture.
"""

import json
import tempfile
from mcp.client import stdio_client


async def test_mcp_integration():
    """Test the MCP server with auto-capture integration."""
    print("🧪 Testing MCP Server Integration\n")
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "memory": {
                "file_path": f.name + "_memory.json",
                "backend": "json"
            },
            "embedding": {
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            },
            "auto_capture": {
                "enabled": True,
                "min_confidence": 0.6
            }
        }
        json.dump(config, f)
        config_file = f.name
    
    # Start MCP server client
    async with stdio_client(
        "python", "-m", "memory_mcp", "--config", config_file
    ) as client:
        print("✅ Connected to MCP server\n")
        
        # List available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Check that auto-capture tools are registered
        auto_capture_tools = [
            "auto_capture_control",
            "content_type_filter", 
            "auto_capture_stats"
        ]
        
        registered_tools = [tool.name for tool in tools]
        for tool_name in auto_capture_tools:
            if tool_name in registered_tools:
                print(f"\n✅ {tool_name} tool registered")
            else:
                print(f"\n❌ {tool_name} tool NOT registered")
        
        # Test auto-capture stats
        print("\n\n📊 Testing auto-capture stats:")
        result = await client.call_tool("auto_capture_stats", {})
        print(f"Result: {result}")
        
        # Test disabling auto-capture
        print("\n\n🔧 Testing auto-capture control:")
        result = await client.call_tool("auto_capture_control", {"enabled": False})
        print(f"Disable result: {result}")
        
        # Test content type filter
        print("\n\n🎯 Testing content type filter:")
        result = await client.call_tool("content_type_filter", {
            "content_type": "personal_info",
            "enabled": False
        })
        print(f"Filter result: {result}")
        
        # Store a test memory
        print("\n\n💾 Testing memory storage:")
        result = await client.call_tool("store_memory", {
            "type": "conversation",
            "content": {"message": "Test integration message"},
            "importance": 0.7
        })
        print(f"Store result: {result}")
        
        # Get memory stats
        print("\n\n📈 Testing memory stats:")
        result = await client.call_tool("memory_stats", {})
        print(f"Stats result: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_mcp_integration())