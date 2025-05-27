"""
Qdrant-based Persistence Domain for storage and retrieval of memories.

This implementation replaces the JSON/hnswlib approach with Qdrant vector database
for better performance and scalability.
"""

import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, Range, HasIdCondition,
    SearchRequest, UpdateStatus, CollectionStatus
)
from qdrant_client.http import models as rest


class QdrantPersistenceDomain:
    """
    Manages the storage and retrieval of memories using Qdrant vector database.
    
    This domain handles vector operations, metadata filtering, and efficient
    similarity search for the memory system.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the Qdrant persistence domain.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Qdrant configuration
        self.qdrant_config = config.get("qdrant", {})
        self.qdrant_url = self.qdrant_config.get("url", "localhost")
        self.qdrant_port = self.qdrant_config.get("port", 6333)
        self.collection_name = self.qdrant_config.get("collection", "memories")
        
        # Use existing embedding config from original
        self.embedding_model_name = config["embedding"].get(
            "default_model", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.embedding_dimensions = config["embedding"].get("dimensions", 384)
        
        # Mode for hybrid local/remote setup
        self.mode = config.get("mode", "local")
        self.remote_embedding_url = config.get("remote_embedding_url")
        
        # Initialize later in initialize()
        self.client = None
        self.embedding_model = None
        self.is_remote = self.mode == "remote" and self.remote_embedding_url
    
    async def initialize(self) -> None:
        """Initialize the Qdrant persistence domain."""
        logger.info("Initializing Qdrant Persistence Domain")
        logger.info(f"Connecting to Qdrant at {self.qdrant_url}:{self.qdrant_port}")
        
        # Initialize Qdrant client
        self.client = QdrantClient(host=self.qdrant_url, port=self.qdrant_port)
        
        # Check if collection exists, create if not
        try:
            collection_info = self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' exists with {collection_info.points_count} points")
        except Exception:
            logger.info(f"Creating collection '{self.collection_name}'")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimensions,
                    distance=Distance.COSINE
                )
            )
        
        # Initialize embedding model (local mode only)
        if not self.is_remote:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
        else:
            logger.info(f"Using remote embedding service at: {self.remote_embedding_url}")
        
        logger.info("Qdrant Persistence Domain initialized")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as a list of floats
        """
        if self.is_remote:
            # Use remote embedding service (for Windows GPU server)
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.remote_embedding_url}/embed",
                    json={"texts": [text]}
                ) as response:
                    result = await response.json()
                    return result["embeddings"][0]
        else:
            # Local embedding
            if not self.embedding_model:
                raise RuntimeError("Embedding model not initialized")
            
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
    
    async def store_memory(self, memory: Dict[str, Any], tier: str = "short_term") -> None:
        """
        Store a memory in Qdrant.
        
        Args:
            memory: Memory to store
            tier: Memory tier (short_term, long_term, archived)
        """
        # Ensure memory has an ID
        if "id" not in memory:
            memory["id"] = str(uuid4())
        
        # Generate embedding if not provided
        if "embedding" not in memory:
            content = memory.get("content", "") or memory.get("text", "") or str(memory)
            memory["embedding"] = await self.generate_embedding(content)
        
        # Prepare point for Qdrant
        point = PointStruct(
            id=memory["id"],
            vector=memory["embedding"],
            payload={
                **{k: v for k, v in memory.items() if k != "embedding"},
                "tier": tier,
                "stored_at": datetime.now().isoformat()
            }
        )
        
        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        logger.debug(f"Stored memory {memory['id']} in tier {tier}")
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory dict or None if not found
        """
        try:
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
                with_payload=True,
                with_vectors=True
            )
            
            if results:
                point = results[0]
                memory = dict(point.payload)
                memory["id"] = point.id
                memory["embedding"] = point.vector
                return memory
        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {e}")
        
        return None
    
    async def search_memories(
        self,
        embedding: List[float],
        limit: int = 5,
        types: Optional[List[str]] = None,
        min_similarity: float = 0.6,
        tier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for memories using vector similarity.
        
        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            types: Memory types to include (None for all)
            min_similarity: Minimum similarity score
            tier: Filter by memory tier
            
        Returns:
            List of matching memories with similarity scores
        """
        # Build filter conditions
        must_conditions = []
        
        if types:
            must_conditions.append(
                FieldCondition(
                    key="type",
                    match=MatchValue(any=types)
                )
            )
        
        if tier:
            must_conditions.append(
                FieldCondition(
                    key="tier",
                    match=MatchValue(value=tier)
                )
            )
        
        # Prepare filter
        filter_conditions = Filter(must=must_conditions) if must_conditions else None
        
        # Search in Qdrant
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            query_filter=filter_conditions,
            limit=limit,
            score_threshold=min_similarity,
            with_payload=True,
            with_vectors=False  # Don't return vectors to save bandwidth
        )
        
        # Format results
        memories = []
        for result in results:
            memory = dict(result.payload)
            memory["id"] = result.id
            memory["similarity"] = float(result.score)
            memories.append(memory)
        
        return memories
    
    async def list_memories(
        self,
        types: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
        tier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List memories with filtering options.
        
        Args:
            types: Memory types to include (None for all)
            limit: Maximum number of memories to return
            offset: Offset for pagination
            tier: Memory tier to filter by (None for all)
            
        Returns:
            List of memories
        """
        # Build filter
        must_conditions = []
        
        if types:
            must_conditions.append(
                FieldCondition(
                    key="type",
                    match=MatchValue(any=types)
                )
            )
        
        if tier:
            must_conditions.append(
                FieldCondition(
                    key="tier",
                    match=MatchValue(value=tier)
                )
            )
        
        filter_conditions = Filter(must=must_conditions) if must_conditions else None
        
        # Scroll through collection
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filter_conditions,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        # Format results
        memories = []
        for point in results[0]:  # results is (points, next_offset)
            memory = dict(point.payload)
            memory["id"] = point.id
            memories.append(memory)
        
        # Sort by creation time (newest first)
        memories.sort(
            key=lambda m: m.get("created_at", ""),
            reverse=True
        )
        
        return memories
    
    async def update_memory(self, memory: Dict[str, Any], tier: str) -> None:
        """
        Update an existing memory.
        
        Args:
            memory: Updated memory dict
            tier: Memory tier
        """
        # Just store it again - Qdrant will update if ID exists
        await self.store_memory(memory, tier)
    
    async def delete_memories(self, memory_ids: List[str]) -> bool:
        """
        Delete memories.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            Success flag
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=HasIdCondition(
                    has_id=memory_ids
                )
            )
            logger.info(f"Deleted {len(memory_ids)} memories")
            return True
        except Exception as e:
            logger.error(f"Error deleting memories: {e}")
            return False
    
    async def get_memory_tier(self, memory_id: str) -> Optional[str]:
        """
        Get the tier of a memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory tier or None if not found
        """
        memory = await self.get_memory(memory_id)
        return memory.get("tier") if memory else None
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Memory statistics
        """
        collection_info = self.client.get_collection(self.collection_name)
        
        # Count by tier
        tier_counts = {}
        for tier in ["short_term", "long_term", "archived"]:
            count_result = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[FieldCondition(key="tier", match=MatchValue(value=tier))]
                )
            )
            tier_counts[f"{tier}_count"] = count_result.count
        
        # Count by type
        type_counts = {
            "conversation": 0,
            "fact": 0,
            "document": 0,
            "entity": 0,
            "reflection": 0,
            "code": 0
        }
        
        for memory_type in type_counts.keys():
            count_result = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value=memory_type))]
                )
            )
            type_counts[memory_type] = count_result.count
        
        return {
            "total_memories": collection_info.points_count,
            "active_memories": tier_counts.get("short_term_count", 0) + tier_counts.get("long_term_count", 0),
            "archived_memories": tier_counts.get("archived_count", 0),
            **tier_counts,
            **type_counts,
            "vector_dimensions": collection_info.config.params.vectors.size,
            "index_size": collection_info.indexed_vectors_count
        }
    
    async def migrate_from_json(self, json_file_path: str) -> int:
        """
        Migrate memories from JSON file to Qdrant.
        
        Args:
            json_file_path: Path to JSON memory file
            
        Returns:
            Number of memories migrated
        """
        logger.info(f"Starting migration from {json_file_path}")
        
        if not os.path.exists(json_file_path):
            logger.error(f"JSON file not found: {json_file_path}")
            return 0
        
        with open(json_file_path, "r") as f:
            data = json.load(f)
        
        migrated_count = 0
        
        # Migrate each tier
        for tier_key in ["short_term_memory", "long_term_memory", "archived_memory"]:
            if tier_key not in data:
                continue
            
            tier = tier_key.replace("_memory", "")
            memories = data[tier_key]
            
            logger.info(f"Migrating {len(memories)} memories from {tier} tier")
            
            # Batch process for efficiency
            batch_size = 100
            for i in range(0, len(memories), batch_size):
                batch = memories[i:i + batch_size]
                points = []
                
                for memory in batch:
                    # Generate embedding if not present
                    if "embedding" not in memory:
                        content = memory.get("content", "") or memory.get("text", "") or str(memory)
                        memory["embedding"] = await self.generate_embedding(content)
                    
                    point = PointStruct(
                        id=memory.get("id", str(uuid4())),
                        vector=memory["embedding"],
                        payload={
                            **{k: v for k, v in memory.items() if k != "embedding"},
                            "tier": tier,
                            "migrated_at": datetime.now().isoformat()
                        }
                    )
                    points.append(point)
                
                # Batch upsert
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                migrated_count += len(points)
                logger.info(f"Migrated batch {i//batch_size + 1}, total: {migrated_count}")
        
        logger.info(f"Migration complete! Migrated {migrated_count} memories")
        return migrated_count