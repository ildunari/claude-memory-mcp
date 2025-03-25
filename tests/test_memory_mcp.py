"""
Basic tests for the Memory MCP Server.
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import pytest

from memory_mcp.utils.config import load_config, save_config
from memory_mcp.utils.schema import validate_memory


class TestConfig(unittest.TestCase):
    """Test configuration utilities."""
    
    def test_load_config_default(self):
        """Test loading default configuration."""
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            # Load config from non-existent file (should create default)
            config = load_config(tmp.name)
            
            # Check if default config was created
            self.assertTrue(os.path.exists(tmp.name))
            
            # Check if config contains default values
            self.assertIn("server", config)
            self.assertIn("memory", config)
            self.assertIn("embedding", config)
    
    def test_save_config(self):
        """Test saving configuration."""
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            # Create test config
            test_config = {
                "test": "value",
                "nested": {
                    "key": "value"
                }
            }
            
            # Save config
            success = save_config(test_config, tmp.name)
            self.assertTrue(success)
            
            # Load config and verify
            with open(tmp.name, "r") as f:
                loaded_config = json.load(f)
            
            self.assertEqual(loaded_config, test_config)


class TestSchema(unittest.TestCase):
    """Test schema validation."""
    
    def test_validate_conversation_memory(self):
        """Test validating conversation memory."""
        memory = {
            "id": "test-123",
            "type": "conversation",
            "content": {
                "role": "user",
                "message": "Hello!"
            }
        }
        
        validated = validate_memory(memory)
        self.assertEqual(validated.id, "test-123")
        self.assertEqual(validated.type, "conversation")
        self.assertEqual(validated.content.role, "user")
        self.assertEqual(validated.content.message, "Hello!")
    
    def test_validate_fact_memory(self):
        """Test validating fact memory."""
        memory = {
            "id": "test-123",
            "type": "fact",
            "content": {
                "fact": "Paris is the capital of France",
                "confidence": 0.95
            }
        }
        
        validated = validate_memory(memory)
        self.assertEqual(validated.id, "test-123")
        self.assertEqual(validated.type, "fact")
        self.assertEqual(validated.content.fact, "Paris is the capital of France")
        self.assertEqual(validated.content.confidence, 0.95)
    
    def test_invalid_memory(self):
        """Test validating invalid memory."""
        memory = {
            "id": "test-123",
            "type": "unknown",
            "content": {
                "data": "test"
            }
        }
        
        validated = validate_memory(memory)
        self.assertEqual(validated, memory)


@pytest.mark.asyncio
async def test_persistence_domain_initialization():
    """Test initialization of the persistence domain."""
    from memory_mcp.domains.persistence import PersistenceDomain
    
    # Create test config
    config = {
        "memory": {
            "file_path": ":memory:"  # In-memory (non-persistent)
        },
        "embedding": {
            "default_model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": 384
        }
    }
    
    # Mock embedding model
    with patch("memory_mcp.domains.persistence.SentenceTransformer") as mock_model:
        # Mock the encode method
        mock_instance = MagicMock()
        mock_instance.encode.return_value = [0.1, 0.2, 0.3]
        mock_model.return_value = mock_instance
        
        # Initialize domain
        domain = PersistenceDomain(config)
        await domain.initialize()
        
        # Check if model was loaded
        mock_model.assert_called_once()
        
        # Check if memory data was initialized
        assert domain.memory_data is not None
        assert "metadata" in domain.memory_data


@pytest.mark.asyncio
async def test_temporal_domain_initialization():
    """Test initialization of the temporal domain."""
    from memory_mcp.domains.temporal import TemporalDomain
    from memory_mcp.domains.persistence import PersistenceDomain
    
    # Create test config
    config = {
        "memory": {
            "file_path": ":memory:",  # In-memory (non-persistent)
            "consolidation_interval_hours": 24
        },
        "embedding": {
            "default_model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": 384
        }
    }
    
    # Mock persistence domain
    persistence_domain = MagicMock(spec=PersistenceDomain)
    persistence_domain.get_metadata.return_value = None
    
    # Initialize domain
    domain = TemporalDomain(config, persistence_domain)
    await domain.initialize()
    
    # Check if domain was initialized
    persistence_domain.get_metadata.assert_called_once_with("last_consolidation")
