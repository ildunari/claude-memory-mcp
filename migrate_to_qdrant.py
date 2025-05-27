#!/usr/bin/env python3
"""
Migration script to convert JSON-based memories to Qdrant vector database.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from loguru import logger

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from memory_mcp.domains.persistence_qdrant import QdrantPersistenceDomain


async def main():
    """Main migration function."""
    # Configure logging
    logger.add(sys.stderr, level="INFO")
    
    # Check for JSON file
    json_file = "./memory.json"
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        logger.error(f"Memory file not found: {json_file}")
        logger.info("Usage: python migrate_to_qdrant.py [path/to/memory.json]")
        return
    
    # Load configuration
    config_file = "./config.qdrant.json"
    if not os.path.exists(config_file):
        logger.error(f"Config file not found: {config_file}")
        logger.info("Please create config.qdrant.json first")
        return
    
    with open(config_file, "r") as f:
        config = json.load(f)
    
    logger.info("Starting migration to Qdrant")
    logger.info(f"Source: {json_file}")
    logger.info(f"Target: Qdrant at {config['qdrant']['url']}:{config['qdrant']['port']}")
    
    # Initialize Qdrant domain
    persistence = QdrantPersistenceDomain(config)
    await persistence.initialize()
    
    # Perform migration
    count = await persistence.migrate_from_json(json_file)
    
    # Get stats
    stats = await persistence.get_memory_stats()
    
    logger.info(f"Migration complete!")
    logger.info(f"Total memories migrated: {count}")
    logger.info(f"Memory statistics: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())