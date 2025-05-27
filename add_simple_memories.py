#!/usr/bin/env python3
"""
Simple script to add test memories using the basic JSON backend.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from memory_mcp.domains.persistence import PersistenceDomain


async def add_test_memories():
    """Add test memories directly using the persistence layer."""
    print("🧠 Adding test memories to Memory MCP...")
    
    # Create memories directory if it doesn't exist
    memory_dir = Path.home() / ".memory_mcp"
    memory_dir.mkdir(exist_ok=True)
    
    # Create basic config
    config = {
        "memory": {"file_path": str(memory_dir / "memories.json")},
        "embedding": {
            "default_model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": 384
        }
    }
    
    # Initialize persistence domain
    persistence = PersistenceDomain(config)
    
    await persistence.initialize()
    
    # Test memories to add
    test_memories = [
        {
            "id": "mem_001",
            "type": "conversation",
            "content": {
                "user_message": "How do I implement a binary search algorithm?",
                "assistant_response": "Here's a binary search implementation:\n\n```python\ndef binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n```\n\nTime complexity: O(log n)"
            },
            "metadata": {
                "topic": "algorithms",
                "language": "python"
            },
            "importance": 0.8
        },
        {
            "id": "mem_002",
            "type": "fact",
            "content": {
                "statement": "React hooks allow functional components to use state and lifecycle methods",
                "explanation": "Hooks like useState and useEffect provide the same capabilities as class components but with a more functional approach",
                "context": "React development"
            },
            "metadata": {
                "domain": "react",
                "category": "hooks"
            },
            "importance": 0.9
        },
        {
            "id": "mem_003",
            "type": "code",
            "content": {
                "title": "Python Context Manager for Database Connections",
                "code": "from contextlib import contextmanager\n\n@contextmanager\ndef db_connection(db_path):\n    conn = sqlite3.connect(db_path)\n    try:\n        yield conn\n    finally:\n        conn.close()\n\n# Usage\nwith db_connection('app.db') as db:\n    cursor = db.cursor()\n    cursor.execute('SELECT * FROM users')",
                "language": "python",
                "description": "A reusable context manager for database connections"
            },
            "metadata": {
                "language": "python",
                "category": "database"
            },
            "importance": 0.85
        },
        {
            "id": "mem_004",
            "type": "fact",
            "content": {
                "statement": "Microservices should be designed around business capabilities, not technical layers",
                "explanation": "Each microservice should own a complete business domain rather than being split by technical concerns like UI, business logic, and data",
                "context": "Software architecture principles"
            },
            "metadata": {
                "domain": "architecture",
                "category": "microservices"
            },
            "importance": 0.9
        },
        {
            "id": "mem_005",
            "type": "conversation",
            "content": {
                "user_message": "What's the difference between async/await and promises in JavaScript?",
                "assistant_response": "async/await is syntactic sugar over promises:\n\n**Promises:**\n```javascript\nfetch('/api/data')\n  .then(response => response.json())\n  .then(data => console.log(data))\n  .catch(error => console.error(error));\n```\n\n**async/await:**\n```javascript\ntry {\n  const response = await fetch('/api/data');\n  const data = await response.json();\n  console.log(data);\n} catch (error) {\n  console.error(error);\n}\n```\n\nasync/await makes asynchronous code look more like synchronous code, improving readability."
            },
            "metadata": {
                "topic": "javascript",
                "concept": "async_programming"
            },
            "importance": 0.85
        },
        {
            "id": "mem_006",
            "type": "entity",
            "content": {
                "name": "Express.js",
                "type": "framework",
                "description": "Fast, minimalist web framework for Node.js applications",
                "attributes": {
                    "language": "JavaScript",
                    "type": "web_framework",
                    "features": ["routing", "middleware", "templating"],
                    "popularity": "very_high"
                },
                "context": "Node.js web development"
            },
            "metadata": {
                "entity_type": "technology",
                "category": "web_framework"
            },
            "importance": 0.8
        }
    ]
    
    memories_added = 0
    
    for memory in test_memories:
        try:
            success = await persistence.store_memory(memory)
            if success:
                memories_added += 1
                memory_type = memory["type"]
                if memory_type == "conversation":
                    topic = memory["metadata"].get("topic", "general")
                    print(f"✅ Added conversation about {topic}")
                elif memory_type == "fact":
                    domain = memory["metadata"].get("domain", "general")
                    print(f"✅ Added fact about {domain}")
                elif memory_type == "code":
                    title = memory["content"].get("title", "code snippet")
                    print(f"✅ Added code: {title}")
                elif memory_type == "entity":
                    name = memory["content"].get("name", "entity")
                    print(f"✅ Added entity: {name}")
                else:
                    print(f"✅ Added {memory_type} memory")
            else:
                print(f"❌ Failed to add {memory['type']} memory")
        except Exception as e:
            print(f"❌ Error adding {memory['type']} memory: {e}")
    
    print(f"\n🎉 Successfully added {memories_added} test memories!")
    print(f"📁 Memories stored in: {memory_dir / 'memories.json'}")
    
    # Test retrieval
    try:
        print("\n🔍 Testing memory retrieval...")
        results = await persistence.search_memories(
            await persistence.generate_embedding("binary search algorithm"),
            limit=3
        )
        print(f"✅ Retrieved {len(results)} memories for 'binary search algorithm'")
        
        results = await persistence.search_memories(
            await persistence.generate_embedding("React hooks"),
            limit=3
        )
        print(f"✅ Retrieved {len(results)} memories for 'React hooks'")
        
    except Exception as e:
        print(f"❌ Error testing retrieval: {e}")
    
    print("\n🚀 Memory system is ready for testing!")
    print("\n💡 You can now test with prompts like:")
    print("  • 'What do you remember about binary search?'")
    print("  • 'Show me React hooks examples'")
    print("  • 'Tell me about microservices architecture'")
    print("  • 'What JavaScript frameworks do you know?'")
    
    return memories_added


if __name__ == "__main__":
    try:
        result = asyncio.run(add_test_memories())
        print(f"\n✨ All done! Added {result} memories.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)