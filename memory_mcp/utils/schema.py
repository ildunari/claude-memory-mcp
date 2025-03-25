"""
Schemas and validation for memory data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

# Memory types
class MemoryType(str, Enum):
    CONVERSATION = "conversation"
    FACT = "fact"
    DOCUMENT = "document"
    ENTITY = "entity"
    REFLECTION = "reflection"
    CODE = "code"

# Memory tiers
class MemoryTier(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    ARCHIVED = "archived"

# Conversation memory content
class ConversationContent(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    message: str = Field(..., description="Message content")
    summary: Optional[str] = Field(None, description="Summary of the message")
    entities: Optional[List[str]] = Field(None, description="Entities mentioned in the message")
    sentiment: Optional[str] = Field(None, description="Sentiment of the message")
    intent: Optional[str] = Field(None, description="Intent of the message")

# Fact memory content
class FactContent(BaseModel):
    fact: str = Field(..., description="The factual statement")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the fact")
    domain: Optional[str] = Field(None, description="Domain of the fact")
    entities: Optional[List[str]] = Field(None, description="Entities mentioned in the fact")
    references: Optional[List[str]] = Field(None, description="References for the fact")

# Document memory content
class DocumentContent(BaseModel):
    title: str = Field(..., description="Document title")
    text: str = Field(..., description="Document text")
    summary: Optional[str] = Field(None, description="Document summary")
    chunks: Optional[List[str]] = Field(None, description="Document chunk IDs")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")

# Entity memory content
class EntityContent(BaseModel):
    name: str = Field(..., description="Entity name")
    entity_type: str = Field(..., description="Entity type")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Entity attributes")
    relationships: Optional[List[Dict[str, str]]] = Field(None, description="Entity relationships")

# Reflection memory content
class ReflectionContent(BaseModel):
    subject: str = Field(..., description="Reflection subject")
    reflection: str = Field(..., description="Reflection content")
    insights: Optional[List[str]] = Field(None, description="Insights from the reflection")
    action_items: Optional[List[str]] = Field(None, description="Action items from the reflection")

# Code memory content
class CodeContent(BaseModel):
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Code content")
    description: Optional[str] = Field(None, description="Code description")
    purpose: Optional[str] = Field(None, description="Code purpose")
    dependencies: Optional[List[str]] = Field(None, description="Code dependencies")

# Memory context
class MemoryContext(BaseModel):
    session_id: Optional[str] = Field(None, description="Session ID")
    related_memories: Optional[List[str]] = Field(None, description="Related memory IDs")
    preceding_memories: Optional[List[str]] = Field(None, description="Preceding memory IDs")
    following_memories: Optional[List[str]] = Field(None, description="Following memory IDs")
    source: Optional[str] = Field(None, description="Memory source")
    emotional_valence: Optional[str] = Field(None, description="Emotional valence of the memory")

# Memory metadata
class MemoryMetadata(BaseModel):
    created_at: str = Field(..., description="Creation timestamp")
    last_accessed: str = Field(..., description="Last access timestamp")
    last_modified: Optional[str] = Field(None, description="Last modification timestamp")
    access_count: int = Field(0, ge=0, description="Number of times the memory has been accessed")
    importance_score: float = Field(0.5, ge=0.0, le=1.0, description="Memory importance score")
    source: Optional[str] = Field(None, description="Memory source")
    tags: Optional[List[str]] = Field(None, description="Memory tags")

    @field_validator("created_at", "last_accessed", "last_modified")
    @classmethod
    def validate_timestamp(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISO format timestamps."""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid ISO format timestamp: {v}")
        return v

# Memory model
class Memory(BaseModel):
    id: str = Field(..., description="Memory ID")
    type: MemoryType = Field(..., description="Memory type")
    content: Dict[str, Any] = Field(..., description="Type-specific content")
    embedding: Optional[List[float]] = Field(None, description="Embedding vector")
    metadata: MemoryMetadata = Field(..., description="Memory metadata")
    context: Optional[MemoryContext] = Field(None, description="Memory context")
    
    @model_validator(mode="after")
    def validate_content(self) -> "Memory":
        """Validate that the content matches the memory type."""
        memory_type = self.type
        content = self.content
        
        try:
            if memory_type == MemoryType.CONVERSATION:
                ConversationContent(**content)
            elif memory_type == MemoryType.FACT:
                FactContent(**content)
            elif memory_type == MemoryType.DOCUMENT:
                DocumentContent(**content)
            elif memory_type == MemoryType.ENTITY:
                EntityContent(**content)
            elif memory_type == MemoryType.REFLECTION:
                ReflectionContent(**content)
            elif memory_type == MemoryType.CODE:
                CodeContent(**content)
        except Exception as e:
            raise ValueError(f"Invalid content for memory type {memory_type}: {e}")
        
        return self
