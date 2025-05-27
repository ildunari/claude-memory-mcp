#!/usr/bin/env python3
"""
Test MCP server directly without client.
"""

import asyncio
import json
import tempfile
import os

from memory_mcp.mcp.server import MemoryMcpServer
from memory_mcp.utils.config import load_config


async def test_direct_integration():
    """Test MCP server components directly."""
    print("🧪 Testing MCP Server Direct Integration\n")
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_memory_file = f.name + "_memory.json"
    
    config = {
        "memory": {
            "file_path": temp_memory_file,
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
    
    try:
        # Create server instance
        server = MemoryMcpServer(config)
        
        # Initialize domain manager
        await server.domain_manager.initialize()
        print("✅ Server initialized\n")
        
        # Test conversation analyzer
        print("📝 Testing ConversationAnalyzer:")
        test_message = "My name is Alice and I'm a software engineer."
        captured = await server.conversation_analyzer.process_message(
            test_message, "user"
        )
        print(f"Message: {test_message}")
        print(f"Captured: {len(captured)} memories")
        for mem in captured:
            print(f"  - {mem['content_type']} (importance: {mem['importance']})")
        
        # Test auto-capture controls
        print("\n\n🔧 Testing auto-capture controls:")
        
        # Check initial state
        stats = server.conversation_analyzer.get_capture_stats()
        print(f"Initial state - Enabled: {stats['auto_capture_enabled']}")
        
        # Disable auto-capture
        server.conversation_analyzer.set_auto_capture_enabled(False)
        stats = server.conversation_analyzer.get_capture_stats()
        print(f"After disable - Enabled: {stats['auto_capture_enabled']}")
        
        # Test with disabled
        captured = await server.conversation_analyzer.process_message(
            "I love Python programming", "user"
        )
        print(f"With disabled - Captured: {len(captured)} memories")
        
        # Re-enable
        server.conversation_analyzer.set_auto_capture_enabled(True)
        
        # Test content type filter
        print("\n\n🎯 Testing content type filters:")
        from memory_mcp.auto_memory import ContentType
        
        # Disable personal info
        server.conversation_analyzer.set_content_type_filter(
            ContentType.PERSONAL_INFO, False
        )
        
        # Test messages
        test_cases = [
            ("I'm Bob from New York", "personal_info"),
            ("I prefer tea over coffee", "preference"),
            ("Python was created in 1991", "fact")
        ]
        
        for message, expected_type in test_cases:
            captured = await server.conversation_analyzer.process_message(
                message, "user"
            )
            print(f"\nMessage: {message}")
            print(f"Expected type: {expected_type}")
            print(f"Captured: {len(captured)} memories")
            if captured:
                for mem in captured:
                    print(f"  - {mem['content_type']}")
        
        # Test memory stats
        print("\n\n📊 Testing memory stats:")
        stats = await server.domain_manager.get_memory_stats()
        print(f"Total memories: {stats.get('total_memories', 0)}")
        print(f"Conversation: {stats.get('conversation', 0)}")
        print(f"Entity: {stats.get('entity', 0)}")
        print(f"Fact: {stats.get('fact', 0)}")
        print(f"Reflection: {stats.get('reflection', 0)}")
        
        # Test auto-capture stats
        print("\n\n📈 Auto-capture statistics:")
        capture_stats = server.conversation_analyzer.get_capture_stats()
        print(json.dumps(capture_stats, indent=2))
        
        print("\n\n✅ All tests completed successfully!")
        
    finally:
        # Cleanup
        if os.path.exists(temp_memory_file):
            os.remove(temp_memory_file)


if __name__ == "__main__":
    asyncio.run(test_direct_integration())