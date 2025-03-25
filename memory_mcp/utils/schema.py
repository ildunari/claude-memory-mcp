"""
Schema validation utilities for the Memory MCP Server.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, conlist, constr


class MemoryBase(BaseModel):
    """Base model for memory entries."""
    id: str
    type: str
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: Optional[str] = None
    last_accessed: Optional[str] = None
    last_modified: Optional[str] = None
    access_count: Optional[int] = Field(default=0, ge=0)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class ConversationContent(BaseModel):
    """Model for conversation memory content."""
    role: Optional[str] = None
    message: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    entities: Optional[List[str]] = None
    sentiment: Optional[str] = None
    intent: Optional[str] = None


class FactContent(BaseModel):
    """Model for fact memory content."""
    fact: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    domain: Optional[str] = None
    entities: Optional[List[str]] = None
    references: Optional[List[str]] = None


class DocumentContent(BaseModel):
    """Model for document memory content."""
    title: str
    text: str
    summary: Optional[str] = None
    chunks: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EntityContent(BaseModel):
    """Model for entity memory content."""
    name: str
    entity_type: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relationships: Optional[List[Dict[str, Any]]] = None


class ReflectionContent(BaseModel):
    """Model for reflection memory content."""
    subject: str
    reflection: str
    insights: Optional[List[str]] = None
    action_items: Optional[List[str]] = None


class CodeContent(BaseModel):
    """Model for code memory content."""
    language: str
    code: str
    description: Optional[str] = None
    purpose: Optional[str] = None
    dependencies: Optional[List[str]] = None


class ConversationMemory(MemoryBase):
    """Model for conversation memory entries."""
    type: str = "conversation"
    content: ConversationContent


class FactMemory(MemoryBase):
    """Model for fact memory entries."""
    type: str = "fact"
    content: FactContent


class DocumentMemory(MemoryBase):
    """Model for document memory entries."""
    type: str = "document"
    content: DocumentContent


class EntityMemory(MemoryBase):
    """Model for entity memory entries."""
    type: str = "entity"
    content: EntityContent


class ReflectionMemory(MemoryBase):
    """Model for reflection memory entries."""
    type: str = "reflection"
    content: ReflectionContent


class CodeMemory(MemoryBase):
    """Model for code memory entries."""
    type: str = "code"
    content: CodeContent


# Memory validators
def validate_memory(memory: Dict[str, Any]) -> Union[MemoryBase, Dict[str, Any]]:
    """
    Validate a memory entry against the appropriate schema.
    
    Args:
        memory: Memory entry
        
    Returns:
        Validated memory (Pydantic model or original dict)
    """
    memory_type = memory.get("type")
    
    try:
        if memory_type == "conversation":
            return ConversationMemory(**memory)
        elif memory_type == "fact":
            return FactMemory(**memory)
        elif memory_type == "document":
            return DocumentMemory(**memory)
        elif memory_type == "entity":
            return EntityMemory(**memory)
        elif memory_type == "reflection":
            return ReflectionMemory(**memory)
        elif memory_type == "code":
            return CodeMemory(**memory)
        else:
            return memory  # Return original if no matching schema
    except Exception:
        return memory  # Return original on validation error
