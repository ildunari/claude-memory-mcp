"""
Tests for the Memory MCP Server.
"""

import os
import json
import asyncio
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

import pytest

from memory_mcp.domains.manager import MemoryDomainManager
from memory_mcp.utils.config import load_config


class TestMemoryDomainManager(unittest.TestCase):
    """Tests for the MemoryDomainManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test memory file
        self.memory_file_path = os.path.join(self.temp_dir.name, "memory.json")
        
        # Create a test configuration
        self.config = {
            "server": {
                "host": "127.0.0.1",
                "port": 8000,
                "debug": True
            },
            "memory": {
                "max_short_term_items": 100,
                "max_long_term_items": 1000,
                "max_archival_items": 10000,
                "consolidation_interval_hours": 24,
                "file_path": self.memory_file_path,
                "short_term_threshold": 0.3
            },
            "embedding": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimensions": 384,
                "cache_dir": os.path.join(self.temp_dir.name, "cache")
            }
        }
        
        # Create an empty memory file
        with open(self.memory_file_path, "w") as f:
            json.dump({
                "metadata": {
                    "version": "1.0",
                    "created_at": "2025-03-25T00:00:00Z",
                    "updated_at": "2025-03-25T00:00:00Z",
                    "memory_stats": {
                        "total_memories": 0,
                        "active_memories": 0,
                        "archived_memories": 0
                    }
                },
                "short_term_memory": [],
                "long_term_memory": [],
                "archived_memory": [],
                "memory_index": {
                    "index_type": "hnsw",
                    "index_parameters": {
                        "m": 16,
                        "ef_construction": 200,
                        "ef": 50
                    },
                    "entries": {}
                }
            }, f)
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test domain manager initialization."""
        # Create the domain manager
        domain_manager = MemoryDomainManager(self.config)
        
        # Initialize the domain manager
        await domain_manager.initialize()
        
        # Check that each domain was initialized
        self.assertIsNotNone(domain_manager.persistence_domain)
        self.assertIsNotNone(domain_manager.episodic_domain)
        self.assertIsNotNone(domain_manager.semantic_domain)
        self.assertIsNotNone(domain_manager.temporal_domain)
    
    @pytest.mark.asyncio
    async def test_store_memory(self):
        """Test storing a memory."""
        # Create the domain manager
        domain_manager = MemoryDomainManager(self.config)
        
        # Initialize the domain manager
        await domain_manager.initialize()
        
        # Create a test memory
        memory_type = "conversation"
        content = {
            "role": "user",
            "message": "Hello, world!",
            "summary": "User greeting",
            "entities": [],
            "sentiment": "positive",
            "intent": "greeting"
        }
        importance = 0.7
        metadata = {
            "source": "test",
            "tags": ["greeting", "test"]
        }
        context = {
            "session_id": "test_session",
            "related_memories": [],
            "preceding_memories": [],
            "following_memories": []
        }
        
        # Store the memory
        memory_id = await domain_manager.store_memory(
            memory_type=memory_type,
            content=content,
            importance=importance,
            metadata=metadata,
            context=context
        )
        
        # Check that a memory ID was returned
        self.assertIsNotNone(memory_id)
        self.assertTrue(memory_id.startswith("mem_"))
        
        # Check that the memory was stored
        memory = await domain_manager.persistence_domain.get_memory(memory_id)
        self.assertIsNotNone(memory)
        self.assertEqual(memory["type"], memory_type)
        self.assertEqual(memory["content"], content)
        self.assertEqual(memory["importance"], importance)
        
        # Check metadata and context
        for key, value in metadata.items():
            self.assertEqual(memory["metadata"][key], value)
        
        for key, value in context.items():
            self.assertEqual(memory["context"][key], value)
    
    @pytest.mark.asyncio
    async def test_retrieve_memories(self):
        """Test retrieving memories."""
        # Create the domain manager
        domain_manager = MemoryDomainManager(self.config)
        
        # Initialize the domain manager
        await domain_manager.initialize()
        
        # Create test memories
        memory_ids = []
        for i in range(5):
            memory_type = "conversation"
            content = {
                "role": "user",
                "message": f"Test message {i}",
                "summary": f"Test summary {i}",
                "entities": [],
                "sentiment": "neutral",
                "intent": "statement"
            }
            importance = 0.5 + (i * 0.1)
            
            memory_id = await domain_manager.store_memory(
                memory_type=memory_type,
                content=content,
                importance=importance
            )
            memory_ids.append(memory_id)
        
        # Wait a moment for persistence to complete
        await asyncio.sleep(0.1)
        
        # Retrieve memories
        memories = await domain_manager.retrieve_memories(
            query="Test message",
            limit=3,
            memory_types=["conversation"],
            min_similarity=0.0
        )
        
        # Check that memories were returned
        self.assertGreater(len(memories), 0)
        self.assertLessEqual(len(memories), 3)
        
        # Check memory structure
        for memory in memories:
            self.assertIn("id", memory)
            self.assertIn("type", memory)
            self.assertIn("content", memory)
            self.assertIn("similarity", memory)
    
    @pytest.mark.asyncio
    async def test_memory_tiers(self):
        """Test memory tier assignment based on importance."""
        # Create the domain manager
        domain_manager = MemoryDomainManager(self.config)
        
        # Initialize the domain manager
        await domain_manager.initialize()
        
        # Create a test memory with high importance (short-term)
        high_importance_id = await domain_manager.store_memory(
            memory_type="conversation",
            content={
                "role": "user",
                "message": "Important message",
                "summary": "Important summary"
            },
            importance=0.8
        )
        
        # Create a test memory with low importance (long-term)
        low_importance_id = await domain_manager.store_memory(
            memory_type="conversation",
            content={
                "role": "user",
                "message": "Less important message",
                "summary": "Less important summary"
            },
            importance=0.2
        )
        
        # Wait for persistence to complete
        await asyncio.sleep(0.1)
        
        # Check memory tiers
        high_tier = await domain_manager.persistence_domain.get_memory_tier(high_importance_id)
        low_tier = await domain_manager.persistence_domain.get_memory_tier(low_importance_id)
        
        self.assertEqual(high_tier, "short_term")
        self.assertEqual(low_tier, "long_term")
