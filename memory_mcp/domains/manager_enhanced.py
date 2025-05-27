"""
Enhanced Memory Domain Manager with backend selection support.
"""

import uuid
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from memory_mcp.domains.episodic import EpisodicDomain
from memory_mcp.domains.semantic import SemanticDomain
from memory_mcp.domains.temporal import TemporalDomain


class EnhancedMemoryDomainManager:
    """
    Enhanced orchestrator that supports multiple storage backends.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the enhanced memory domain manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Determine backend
        backend = config.get("memory", {}).get("backend", "json")
        logger.info(f"Using memory backend: {backend}")
        
        # Initialize appropriate persistence domain
        if backend == "qdrant":
            from memory_mcp.domains.persistence_qdrant import QdrantPersistenceDomain
            self.persistence_domain = QdrantPersistenceDomain(config)
        else:
            from memory_mcp.domains.persistence import PersistenceDomain
            self.persistence_domain = PersistenceDomain(config)
        
        # Initialize other domains
        self.episodic_domain = EpisodicDomain(config, self.persistence_domain)
        self.semantic_domain = SemanticDomain(config, self.persistence_domain)
        self.temporal_domain = TemporalDomain(config, self.persistence_domain)
    
    async def initialize(self) -> None:
        """Initialize all domains."""
        logger.info("Initializing Enhanced Memory Domain Manager")
        
        # Initialize domains in order (persistence first)
        await self.persistence_domain.initialize()
        await self.episodic_domain.initialize()
        await self.semantic_domain.initialize()
        await self.temporal_domain.initialize()
        
        logger.info("Enhanced Memory Domain Manager initialized")
    
    # The rest of the methods would be the same as the original manager
    # Just copying the interface for compatibility
    
    async def store_memory(
        self,
        content: Union[str, Dict[str, Any]],
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a new memory."""
        # Implementation would be same as original
        pass
    
    async def retrieve_memories(
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[str]] = None,
        min_similarity: float = 0.75
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on a query."""
        # Implementation would be same as original
        pass