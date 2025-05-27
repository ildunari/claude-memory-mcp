"""
Pydantic models for MCP tool inputs.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class StoreMemoryInput(BaseModel):
    """Input for store_memory tool."""
    type: str = Field(
        description="Type of memory to store (conversation, fact, document, entity, reflection, code)",
        pattern="^(conversation|fact|document|entity|reflection|code)$"
    )
    content: Dict[str, Any] = Field(
        description="Content of the memory (type-specific structure)"
    )
    importance: float = Field(
        default=0.5,
        description="Importance score (0.0-1.0, higher is more important)",
        ge=0.0,
        le=1.0
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the memory"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context for episodic memory types"
    )


class RetrieveMemoryInput(BaseModel):
    """Input for retrieve_memory tool."""
    query: str = Field(
        description="Query string to search for relevant memories"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of memories to retrieve",
        gt=0,
        le=50
    )
    types: Optional[List[str]] = Field(
        default=None,
        description="Optional list of memory types to filter by"
    )
    min_similarity: float = Field(
        default=0.6,
        description="Minimum similarity score for retrieval",
        ge=0.0,
        le=1.0
    )
    include_metadata: bool = Field(
        default=False,
        description="Whether to include metadata in the response"
    )


class ListMemoriesInput(BaseModel):
    """Input for list_memories tool."""
    limit: int = Field(
        default=20,
        description="Maximum number of memories to list",
        gt=0,
        le=100
    )
    types: Optional[List[str]] = Field(
        default=None,
        description="Optional list of memory types to filter by"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date for filtering (ISO format)"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date for filtering (ISO format)"
    )


class UpdateMemoryInput(BaseModel):
    """Input for update_memory tool."""
    memory_id: str = Field(
        description="ID of the memory to update"
    )
    updates: Dict[str, Any] = Field(
        description="Fields to update in the memory"
    )


class DeleteMemoryInput(BaseModel):
    """Input for delete_memory tool."""
    memory_ids: List[str] = Field(
        description="List of memory IDs to delete"
    )


class MemoryStatsInput(BaseModel):
    """Input for memory_stats tool (empty input)."""
    pass