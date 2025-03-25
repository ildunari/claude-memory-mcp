"""
Types and constants for memory data structures.
"""

# Memory types
MEMORY_TYPES = [
    "conversation",
    "fact",
    "document",
    "entity",
    "reflection",
    "code"
]

# Memory tiers
MEMORY_TIERS = [
    "short_term",
    "long_term",
    "archived"
]

# Required fields for each memory type
MEMORY_TYPE_REQUIREMENTS = {
    "conversation": ["role", "message"],
    "fact": ["fact", "confidence"],
    "document": ["title", "text"],
    "entity": ["name", "entity_type"],
    "reflection": ["subject", "reflection"],
    "code": ["language", "code"]
}

# Required metadata fields
REQUIRED_METADATA = [
    "created_at",
    "last_accessed",
    "importance_score"
]

# Common memory structure example
"""
{
    "id": "mem_12345",
    "type": "conversation",
    "content": {
        "role": "user",
        "message": "Hello!",
        "summary": "User greeting",
        "entities": [],
        "sentiment": "positive",
        "intent": "greeting"
    },
    "embedding": [0.1, 0.2, 0.3, ...],
    "metadata": {
        "created_at": "2025-03-25T10:00:00Z",
        "last_accessed": "2025-03-25T10:05:00Z",
        "access_count": 1,
        "importance_score": 0.5,
        "source": "user",
        "tags": ["greeting"]
    },
    "context": {
        "session_id": "session_12345",
        "related_memories": [],
        "preceding_memories": [],
        "following_memories": []
    }
}
"""
