"""
Configuration utilities for the memory system.
"""

import os
import json
from typing import Any, Dict

from loguru import logger


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Add default values for required settings
        if "server" not in config:
            config["server"] = {
                "host": "127.0.0.1",
                "port": 8000,
                "debug": False
            }
        
        if "memory" not in config:
            config["memory"] = {
                "max_short_term_items": 100,
                "max_long_term_items": 1000,
                "max_archival_items": 10000,
                "consolidation_interval_hours": 24,
                "file_path": os.path.join(os.path.expanduser("~"), ".memory_mcp", "data", "memory.json")
            }
        
        if "embedding" not in config:
            config["embedding"] = {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimensions": 384,
                "cache_dir": os.path.join(os.path.expanduser("~"), ".memory_mcp", "cache")
            }
        
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise ValueError(f"Invalid configuration format: {e}")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to the configuration file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        raise


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries, with override_config taking precedence.
    
    Args:
        base_config: Base configuration
        override_config: Override configuration
        
    Returns:
        Merged configuration
    """
    merged = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_configs(merged[key], value)
        else:
            # Override or add value
            merged[key] = value
    
    return merged


def get_config_value(
    config: Dict[str, Any], 
    key_path: str, 
    default: Any = None
) -> Any:
    """
    Get a configuration value using a dot-separated path.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path to the value (e.g., "server.host")
        default: Default value to return if the path doesn't exist
        
    Returns:
        Configuration value or default
    """
    keys = key_path.split(".")
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current
