"""
Schemas and validation for memory data structures.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


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


# Basic memory schema
class MemorySchema(BaseModel):
    """Base schema for all memory types."""
    id: str = Field(..., description="Memory ID")
    type: str = Field(..., description="Memory type")
    content: Dict[str, Any] = Field(..., description="Type-specific content")
    embedding: Optional[List[float]] = Field(None, description="Embedding vector")
    metadata: Dict[str, Any] = Field(..., description="Memory metadata")
    context: Optional[Dict[str, Any]] = Field(None, description="Memory context")
