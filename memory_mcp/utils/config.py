"""
Configuration utilities for the Memory MCP Server.
"""

import os
import json
from typing import Any, Dict, Optional

from loguru import logger


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    # Default configuration
    default_config = {
        "server": {
            "host": "127.0.0.1",
            "port": 8000,
            "debug": False
        },
        "memory": {
            "max_short_term_items": 100,
            "max_long_term_items": 1000,
            "max_archival_items": 10000,
            "consolidation_interval_hours": 24,
            "file_path": os.path.expanduser("~/.memory_mcp/data/memory.json"),
            "short_term_threshold": 0.3
        },
        "embedding": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": 384,
            "cache_dir": os.path.expanduser("~/.memory_mcp/cache")
        }
    }
    
    # Try to load configuration file
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                loaded_config = json.load(f)
                logger.info(f"Loaded configuration from {config_path}")
                
            # Deep merge loaded config with default config
            merged_config = deep_merge(default_config, loaded_config)
            return merged_config
        else:
            logger.warning(f"Configuration file not found: {config_path}")
            logger.info("Using default configuration")
            
            # Create directory for config file
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Save default config to file
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        logger.info("Using default configuration")
        return default_config


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Dictionary with override values
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to the configuration file
        
    Returns:
        Success flag
    """
    try:
        # Create directory for config file
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Create temp file
        temp_file = f"{config_path}.tmp"
        
        with open(temp_file, "w") as f:
            json.dump(config, f, indent=2)
        
        # Rename temp file to actual file (atomic operation)
        os.replace(temp_file, config_path)
        
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        
        # Clean up temp file if it exists
        if os.path.exists(f"{config_path}.tmp"):
            os.remove(f"{config_path}.tmp")
        
        return False
