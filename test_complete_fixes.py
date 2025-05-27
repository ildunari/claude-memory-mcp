#!/usr/bin/env python3
"""
Test complete fixes for stats and auto-capture.
"""

import asyncio
import json
import tempfile
import os

from memory_mcp.mcp.server import MemoryMcpServer
from memory_mcp.utils.config import load_config


async def test_complete_fixes():
    """Test both stats fix and auto-capture activation."""
    print("🧪 Testing Complete Fixes\n")
    
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
        
        # Test 1: Store some memories
        print("📝 Storing test memories...")
        memories = [
            ("conversation", {"message": "I'm learning about memory systems"}),
            ("fact", {"fact": "Memory stats should count correctly"}),
            ("entity", {"name": "TestUser", "attributes": {"role": "tester"}}),
            ("reflection", {"thought": "Testing is important"})
        ]
        
        for mem_type, content in memories:
            await server.domain_manager.store_memory(
                memory_type=mem_type,
                content=content,
                importance=0.7
            )
        
        # Test 2: Check memory stats (including domain-specific counts)
        print("\n📊 Testing Memory Stats (Complete):")
        stats = await server.domain_manager.get_memory_stats()
        
        print(f"\nOverall Stats:")
        print(f"  Total memories: {stats.get('total_memories', 0)}")
        print(f"  Conversation: {stats.get('conversation', 0)}")
        print(f"  Fact: {stats.get('fact', 0)}")
        print(f"  Entity: {stats.get('entity', 0)}")
        print(f"  Reflection: {stats.get('reflection', 0)}")
        
        print(f"\nDomain-Specific Stats:")
        print(f"  Episodic Domain:")
        episodic_stats = stats.get('episodic_domain', {})
        print(f"    - Conversation: {episodic_stats.get('memory_types', {}).get('conversation', 0)}")
        print(f"    - Reflection: {episodic_stats.get('memory_types', {}).get('reflection', 0)}")
        
        print(f"  Semantic Domain:")
        semantic_stats = stats.get('semantic_domain', {})
        print(f"    - Fact: {semantic_stats.get('memory_types', {}).get('fact', 0)}")
        print(f"    - Entity: {semantic_stats.get('memory_types', {}).get('entity', 0)}")
        
        # Test 3: Auto-capture functionality
        print("\n\n🤖 Testing Auto-Capture:")
        
        # Process some messages
        test_messages = [
            "My name is Alice and I work as a data scientist.",
            "I love machine learning and neural networks.",
            "I've decided to specialize in NLP.",
            "Python is my favorite programming language."
        ]
        
        for message in test_messages:
            print(f"\nProcessing: {message}")
            captured = await server.conversation_analyzer.process_message(
                message, "user"
            )
            print(f"  Captured: {len(captured)} memories")
            for cap in captured:
                print(f"    - {cap['content_type']} (importance: {cap['importance']})")
        
        # Check auto-capture stats
        print("\n\n📈 Auto-Capture Stats:")
        capture_stats = server.conversation_analyzer.get_capture_stats()
        print(json.dumps(capture_stats, indent=2))
        
        # Final memory stats after auto-capture
        print("\n\n📊 Final Memory Stats (After Auto-Capture):")
        final_stats = await server.domain_manager.get_memory_stats()
        print(f"  Total memories: {final_stats.get('total_memories', 0)}")
        print(f"  Entity memories: {final_stats.get('entity', 0)}")
        
        print("\n\n✅ Testing complete!")
        
        # Verify fixes
        issues_found = []
        
        # Check domain stats
        if episodic_stats.get('memory_types', {}).get('conversation', 0) != 1:
            issues_found.append("❌ Episodic domain conversation count still wrong")
        else:
            print("✅ Domain stats fixed!")
            
        # Check auto-capture
        if capture_stats['recent_capture_count'] == 0:
            issues_found.append("❌ Auto-capture not capturing")
        else:
            print("✅ Auto-capture is working!")
        
        if issues_found:
            print("\n⚠️  Issues remaining:")
            for issue in issues_found:
                print(f"  {issue}")
        else:
            print("\n🎉 All fixes working correctly!")
        
    finally:
        # Cleanup
        if os.path.exists(temp_memory_file):
            os.remove(temp_memory_file)


if __name__ == "__main__":
    asyncio.run(test_complete_fixes())