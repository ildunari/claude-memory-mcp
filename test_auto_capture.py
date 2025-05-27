#!/usr/bin/env python3
"""
Test script for the enhanced auto-capture system.
"""

import asyncio
import json
from typing import Dict, Any

from memory_mcp.auto_memory import (
    EnhancedAutoCaptureAnalyzer,
    ConversationAnalyzer,
    ContentType
)
from memory_mcp.domains.manager import MemoryDomainManager
from memory_mcp.utils.config import create_default_config


async def test_enhanced_capture():
    """Test the enhanced capture analyzer."""
    print("\n=== Testing Enhanced Capture Analyzer ===\n")
    
    analyzer = EnhancedAutoCaptureAnalyzer()
    
    # Test messages
    test_messages = [
        # Personal info
        "My name is John Smith and I'm from New York.",
        "I work as a software engineer at Tech Corp.",
        "I'm 28 years old and I have 2 kids.",
        
        # Preferences
        "I really love Italian food, especially pasta.",
        "I hate cold weather and can't stand snow.",
        "My favorite color is blue and my favorite movie is Inception.",
        
        # Decisions
        "I've decided to learn Python programming.",
        "I'm going to start exercising every morning.",
        "I will quit smoking next month.",
        
        # Learning
        "I've learned that meditation really helps with stress.",
        "I realized that I need to manage my time better.",
        
        # Facts
        "Paris is the capital of France.",
        "Python was created by Guido van Rossum.",
        "The Earth orbits around the Sun.",
        
        # Questions (should not capture)
        "What is the capital of Spain?",
        "How do I learn programming?",
    ]
    
    for message in test_messages:
        print(f"\nAnalyzing: {message}")
        candidates = analyzer.analyze_message(message)
        
        if candidates:
            for candidate in candidates:
                print(f"  - Type: {candidate.content_type.value}")
                print(f"    Confidence: {candidate.confidence:.2f}")
                print(f"    Importance: {candidate.importance:.2f}")
                print(f"    Extracted: {json.dumps(candidate.extracted_content, indent=6)}")
        else:
            print("  - No memory-worthy content detected")


async def test_conversation_analyzer():
    """Test the conversation analyzer with automatic storage."""
    print("\n\n=== Testing Conversation Analyzer ===\n")
    
    # Create a mock memory store
    stored_memories = []
    
    async def mock_store_memory(memory_type, content, importance, context=None):
        memory_id = f"mock_{len(stored_memories)}"
        stored_memories.append({
            "id": memory_id,
            "type": memory_type,
            "content": content,
            "importance": importance
        })
        return memory_id
    
    # Create analyzer with mock store
    config = {
        "auto_capture_enabled": True,
        "min_confidence": 0.6,
        "capture_cooldown_minutes": 0  # No cooldown for testing
    }
    
    analyzer = ConversationAnalyzer(mock_store_memory, config)
    
    # Simulate a conversation
    conversation = [
        ("user", "Hi! My name is Sarah and I'm a data scientist."),
        ("assistant", "Nice to meet you, Sarah! How can I help you today?"),
        ("user", "I love working with machine learning, especially neural networks."),
        ("user", "I've decided to specialize in computer vision."),
        ("assistant", "That's exciting! Computer vision is a fascinating field."),
        ("user", "I learned that CNNs are particularly good for image classification."),
        ("user", "My favorite framework is PyTorch because it's so intuitive."),
    ]
    
    print("Processing conversation...\n")
    
    for role, message in conversation:
        print(f"{role.upper()}: {message}")
        captured = await analyzer.process_message(message, role)
        
        if captured:
            print(f"  📝 Captured {len(captured)} memories")
            for mem in captured:
                print(f"     - {mem['content_type']} (importance: {mem['importance']})")
    
    # Show capture statistics
    print("\n\nCapture Statistics:")
    stats = analyzer.get_capture_stats()
    print(json.dumps(stats, indent=2))
    
    # Show stored memories
    print(f"\n\nStored Memories ({len(stored_memories)} total):")
    for i, memory in enumerate(stored_memories):
        print(f"\n{i+1}. Type: {memory['type']}")
        print(f"   Importance: {memory['importance']}")
        print(f"   Content: {json.dumps(memory['content'], indent=3)}")


async def test_user_controls():
    """Test user control mechanisms."""
    print("\n\n=== Testing User Controls ===\n")
    
    stored_memories = []
    
    async def mock_store_memory(memory_type, content, importance, context=None):
        memory_id = f"control_{len(stored_memories)}"
        stored_memories.append({
            "id": memory_id,
            "type": memory_type,
            "content": content
        })
        return memory_id
    
    analyzer = ConversationAnalyzer(mock_store_memory)
    
    # Test disabling auto-capture
    print("1. Testing auto-capture toggle:")
    analyzer.set_auto_capture_enabled(False)
    captured = await analyzer.process_message("My email is test@example.com", "user")
    print(f"   With auto-capture disabled: {len(captured)} memories captured")
    
    analyzer.set_auto_capture_enabled(True)
    captured = await analyzer.process_message("My phone number is 555-1234", "user")
    print(f"   With auto-capture enabled: {len(captured)} memories captured")
    
    # Test content type filters
    print("\n2. Testing content type filters:")
    analyzer.set_content_type_filter(ContentType.PERSONAL_INFO, False)
    
    captured = await analyzer.process_message("I'm Bob and I love pizza", "user")
    print(f"   With personal info disabled: {len(captured)} memories captured")
    
    # Show what was captured
    if stored_memories:
        print("\n   Captured content types:")
        for mem in stored_memories:
            content_type = mem['content'].get('metadata', {}).get('content_type', 'unknown')
            print(f"   - {content_type}")


async def main():
    """Run all tests."""
    print("🧠 Testing Enhanced Auto-Capture System\n")
    
    await test_enhanced_capture()
    await test_conversation_analyzer()
    await test_user_controls()
    
    print("\n\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())