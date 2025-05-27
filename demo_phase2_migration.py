#!/usr/bin/env python3

"""
Phase 2 Migration Demo Script

This script demonstrates the complete embedding migration workflow using the
dual-collection architecture. It shows:

1. Setup with initial memories using 384-dim embeddings
2. Migration initiation to 768-dim embeddings  
3. Step-by-step migration process
4. Search result fusion during migration
5. Quality monitoring and rollback capabilities
6. Migration completion and cleanup

Usage:
    python demo_phase2_migration.py [--config CONFIG_FILE] [--interactive]
"""

import asyncio
import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import argparse

from loguru import logger

from memory_mcp.domains.manager import MemoryDomainManager
from memory_mcp.domains.dual_collection_manager import MigrationStateEnum
from memory_mcp.utils.config import load_config


class Phase2MigrationDemo:
    """Demonstrates the complete Phase 2 migration workflow."""
    
    def __init__(self, config_path: str = None, interactive: bool = False):
        self.config_path = config_path
        self.interactive = interactive
        self.temp_dir = None
        self.config = None
        self.memory_manager = None
        self.demo_memories = []
        
    async def setup_demo_environment(self):
        """Setup demo environment with sample data."""
        print("🚀 Setting up Phase 2 Migration Demo Environment")
        print("=" * 60)
        
        # Create temporary directory if no config provided
        if not self.config_path:
            self.temp_dir = tempfile.mkdtemp()
            config_path = f"{self.temp_dir}/demo_config.json"
            
            # Create demo configuration
            demo_config = {
                "memory": {
                    "backend": "qdrant",
                    "file_path": f"{self.temp_dir}/demo_memories.json",
                    "dir": self.temp_dir
                },
                "qdrant": {
                    "url": "http://localhost:6333",
                    "collection_name": "demo_migration_memories",
                    "dimension": 384,
                    "timeout": 30.0,
                    "prefer_grpc": False
                },
                "embedding": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "local": True,
                    "cache_dir": f"{self.temp_dir}/embeddings_cache"
                },
                "migration": {
                    "enabled": True,
                    "quality_threshold": 0.75,
                    "rollback_threshold": 0.6,
                    "max_time_hours": 2,
                    "state_file": f"{self.temp_dir}/migration_state.json"
                },
                "background": {
                    "max_workers": 2,
                    "max_queue_size": 50
                },
                "retrieval": {
                    "hybrid_search": True,
                    "query_expansion": False
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(demo_config, f, indent=2)
                
            self.config_path = config_path
            
        # Load configuration
        self.config = load_config(self.config_path)
        
        # Initialize memory manager
        print("📋 Initializing Memory Domain Manager...")
        self.memory_manager = MemoryDomainManager(self.config)
        await self.memory_manager.initialize()
        
        # Check if migration is available
        if not self.memory_manager.is_migration_available():
            print("❌ Migration functionality not available!")
            print("   Please ensure:")
            print("   - Qdrant is running (docker run -p 6333:6333 qdrant/qdrant)")
            print("   - Migration is enabled in configuration")
            raise RuntimeError("Migration not available")
            
        print("✅ Memory Domain Manager initialized with migration support")
        
        # Create demo memories
        await self._create_demo_memories()
        
        if self.interactive:
            input("\n⏸️  Press Enter to continue with migration demo...")
            
    async def _create_demo_memories(self):
        """Create diverse demo memories for migration testing."""
        print("\n📝 Creating demo memories...")
        
        demo_data = [
            {
                "type": "conversation",
                "content": {
                    "role": "user",
                    "message": "How does machine learning work in natural language processing?"
                },
                "importance": 0.8,
                "metadata": {"topic": "machine_learning", "domain": "AI"}
            },
            {
                "type": "fact", 
                "content": {
                    "statement": "Vector embeddings represent text as high-dimensional numerical vectors.",
                    "domain": "NLP",
                    "verified": True
                },
                "importance": 0.9,
                "metadata": {"category": "technical", "accuracy": "high"}
            },
            {
                "type": "document",
                "content": {
                    "title": "Introduction to Transformer Architecture",
                    "text": "Transformers revolutionized NLP by introducing attention mechanisms that allow models to focus on relevant parts of the input sequence when making predictions.",
                    "author": "Demo Author"
                },
                "importance": 0.7,
                "metadata": {"type": "educational", "complexity": "intermediate"}
            },
            {
                "type": "entity",
                "content": {
                    "name": "BERT",
                    "type": "model",
                    "description": "Bidirectional Encoder Representations from Transformers - a pre-trained language model."
                },
                "importance": 0.8,
                "metadata": {"model_type": "transformer", "year": "2018"}
            },
            {
                "type": "code",
                "content": {
                    "language": "python",
                    "code": "from sentence_transformers import SentenceTransformer\nmodel = SentenceTransformer('all-MiniLM-L6-v2')",
                    "description": "Load a sentence transformer model"
                },
                "importance": 0.6,
                "metadata": {"framework": "sentence-transformers", "complexity": "basic"}
            },
            {
                "type": "reflection",
                "content": {
                    "observation": "Users often ask about embedding dimensions and their impact on performance.",
                    "insight": "Larger embeddings generally capture more nuances but require more computational resources.",
                    "confidence": 0.85
                },
                "importance": 0.5,
                "metadata": {"category": "user_behavior", "data_source": "interaction_logs"}
            }
        ]
        
        for i, memory_data in enumerate(demo_data):
            try:
                memory_id = await self.memory_manager.store_memory(
                    memory_type=memory_data["type"],
                    content=memory_data["content"],
                    importance=memory_data["importance"],
                    metadata=memory_data["metadata"]
                )
                self.demo_memories.append(memory_id)
                print(f"   ✅ Created {memory_data['type']} memory: {memory_id}")
                
            except Exception as e:
                print(f"   ❌ Failed to create {memory_data['type']} memory: {e}")
                
        print(f"\n📊 Successfully created {len(self.demo_memories)} demo memories")
        
        # Test initial search
        print("\n🔍 Testing initial search capabilities...")
        results = await self.memory_manager.retrieve_memories("machine learning transformers", limit=3)
        print(f"   Found {len(results)} relevant memories for 'machine learning transformers'")
        
        for result in results[:2]:  # Show first 2 results
            print(f"   - {result['type']}: {result.get('content', {}).get('title', result.get('content', {}).get('statement', str(result['content'])[:50]))}...")
            
    async def demonstrate_migration_workflow(self):
        """Demonstrate the complete migration workflow."""
        print("\n🔄 Starting Migration Workflow Demonstration")
        print("=" * 60)
        
        # Phase 1: Migration Initiation
        await self._demo_migration_initiation()
        
        # Phase 2: Migration Execution
        await self._demo_migration_execution()
        
        # Phase 3: Search Fusion During Migration
        await self._demo_search_fusion()
        
        # Phase 4: Quality Monitoring
        await self._demo_quality_monitoring()
        
        # Phase 5: Migration Completion
        await self._demo_migration_completion()
        
    async def _demo_migration_initiation(self):
        """Demonstrate migration initiation."""
        print("\n🚀 Phase 1: Migration Initiation")
        print("-" * 40)
        
        target_model = "sentence-transformers/all-mpnet-base-v2"
        target_dimension = 768
        
        migration_config = {
            "batch_size": 2,
            "quality_threshold": 0.7,
            "max_retries": 3,
            "validation_sample_size": 2
        }
        
        print(f"   Target Model: {target_model}")
        print(f"   Target Dimension: {target_dimension}")
        print(f"   Migration Config: {migration_config}")
        
        if self.interactive:
            input("\n⏸️  Press Enter to start migration...")
            
        success = await self.memory_manager.start_embedding_migration(
            target_model=target_model,
            target_dimension=target_dimension,
            migration_config=migration_config
        )
        
        if success:
            print("   ✅ Migration started successfully!")
        else:
            print("   ❌ Failed to start migration")
            return False
            
        # Show initial status
        status = await self.memory_manager.get_migration_status()
        if status:
            print(f"   📊 Initial Status: {status['state']} ({status['progress']:.1%} complete)")
            
        return True
        
    async def _demo_migration_execution(self):
        """Demonstrate step-by-step migration execution."""
        print("\n⚙️ Phase 2: Migration Execution")
        print("-" * 40)
        
        max_steps = 10
        step = 0
        
        while step < max_steps:
            status = await self.memory_manager.get_migration_status()
            if not status:
                print("   ℹ️  No active migration found")
                break
                
            current_state = status['state']
            progress = status['progress']
            
            print(f"   Step {step + 1}: {current_state} ({progress:.1%} complete)")
            
            if current_state in ['cleanup', 'completed']:
                print("   🎉 Migration completed!")
                break
                
            if self.interactive and step > 0:
                input("   ⏸️  Press Enter to advance migration...")
                
            # Advance migration
            advanced = await self.memory_manager.advance_migration()
            if not advanced:
                print("   ⚠️  Migration could not be advanced")
                break
                
            step += 1
            await asyncio.sleep(0.5)  # Brief pause for demo effect
            
        if step >= max_steps:
            print("   ⚠️  Migration demo stopped after maximum steps")
            
    async def _demo_search_fusion(self):
        """Demonstrate search result fusion during migration."""
        print("\n🔍 Phase 3: Search Result Fusion During Migration")
        print("-" * 40)
        
        test_queries = [
            "machine learning",
            "transformer architecture", 
            "embedding vectors",
            "BERT model",
            "python code"
        ]
        
        print("   Testing search fusion with dual collections...")
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            
            try:
                results = await self.memory_manager.retrieve_memories(query, limit=3)
                print(f"   📊 Found {len(results)} results")
                
                for i, result in enumerate(results[:2], 1):
                    content_preview = self._get_content_preview(result)
                    similarity = result.get('similarity', 'N/A')
                    print(f"      {i}. [{result['type']}] {content_preview} (sim: {similarity})")
                    
            except Exception as e:
                print(f"   ❌ Search error: {e}")
                
            if self.interactive and query != test_queries[-1]:
                input("   ⏸️  Press Enter for next query...")
                
    def _get_content_preview(self, memory: Dict[str, Any]) -> str:
        """Get a preview of memory content."""
        content = memory.get('content', {})
        
        if isinstance(content, dict):
            # Try different content fields
            for field in ['title', 'statement', 'message', 'name', 'description']:
                if field in content:
                    return str(content[field])[:50] + "..."
                    
            # Fallback to first value
            if content:
                first_value = list(content.values())[0]
                return str(first_value)[:50] + "..."
                
        return str(content)[:50] + "..."
        
    async def _demo_quality_monitoring(self):
        """Demonstrate quality monitoring and rollback capabilities."""
        print("\n📊 Phase 4: Quality Monitoring & Rollback Demo")
        print("-" * 40)
        
        # Show current migration status
        status = await self.memory_manager.get_migration_status()
        if status:
            print(f"   Current State: {status['state']}")
            print(f"   Progress: {status['progress']:.1%}")
            print(f"   Quality Gates: {status.get('quality_gates', {})}")
            
        # Demonstrate rollback capability (but don't actually rollback unless interactive)
        print("\n   🔄 Rollback Capability Demo")
        
        if self.interactive:
            response = input("   Would you like to demonstrate rollback? (y/N): ")
            if response.lower() == 'y':
                print("   Executing rollback...")
                success = await self.memory_manager.rollback_migration("Demo rollback")
                if success:
                    print("   ✅ Rollback completed successfully")
                    # Restart migration for completion demo
                    print("   🔄 Restarting migration for completion demo...")
                    await self._demo_migration_initiation()
                else:
                    print("   ❌ Rollback failed")
        else:
            print("   ℹ️  Rollback available but skipped in non-interactive mode")
            
    async def _demo_migration_completion(self):
        """Demonstrate migration completion."""
        print("\n🏁 Phase 5: Migration Completion")
        print("-" * 40)
        
        # Complete remaining migration steps
        while True:
            status = await self.memory_manager.get_migration_status()
            if not status:
                print("   ℹ️  No active migration")
                break
                
            if status['state'] in ['cleanup', 'completed']:
                print("   🎉 Migration already completed!")
                break
                
            print(f"   Completing migration... (current: {status['state']})")
            advanced = await self.memory_manager.advance_migration()
            
            if not advanced:
                break
                
            await asyncio.sleep(0.3)
            
        # Test final search performance
        print("\n   🔍 Testing post-migration search performance...")
        
        test_query = "transformer machine learning embeddings"
        start_time = time.time()
        results = await self.memory_manager.retrieve_memories(test_query, limit=5)
        search_time = (time.time() - start_time) * 1000
        
        print(f"   📊 Search Results for '{test_query}':")
        print(f"      - Found: {len(results)} memories")
        print(f"      - Search time: {search_time:.1f}ms")
        print(f"      - Average similarity: {sum(r.get('similarity', 0) for r in results) / len(results):.3f}")
        
        # Show system health
        health = await self.memory_manager.get_system_health()
        print(f"\n   🏥 System Health: {health.get('status', 'Unknown')}")
        
        if 'checks' in health:
            for check_name, check_result in health['checks'].items():
                status_icon = "✅" if check_result.get('status') == 'ok' else "❌"
                print(f"      {status_icon} {check_name}: {check_result.get('status', 'unknown')}")
                
    async def cleanup(self):
        """Clean up demo environment."""
        print("\n🧹 Cleaning up demo environment...")
        
        try:
            if self.memory_manager:
                await self.memory_manager.shutdown()
                
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                print("   ✅ Temporary files cleaned up")
                
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {e}")
            
    async def run_demo(self):
        """Run the complete demo."""
        try:
            await self.setup_demo_environment()
            await self.demonstrate_migration_workflow()
            
            print("\n" + "=" * 60)
            print("🎉 Phase 2 Migration Demo Completed Successfully!")
            print("=" * 60)
            print("\nKey Features Demonstrated:")
            print("✅ Zero-downtime migration workflow")
            print("✅ Search result fusion across embedding dimensions") 
            print("✅ Quality monitoring and rollback capabilities")
            print("✅ Step-by-step migration state management")
            print("✅ Production-ready safety infrastructure")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            logger.exception("Demo failure details")
            
        finally:
            await self.cleanup()


async def main():
    """Main demo runner."""
    parser = argparse.ArgumentParser(description="Phase 2 Migration Demo")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.remove()
        logger.add(lambda msg: print(msg), level="DEBUG")
    
    # Check Qdrant availability
    print("🔍 Checking Qdrant availability...")
    try:
        import requests
        response = requests.get("http://localhost:6333/collections", timeout=5)
        if response.status_code == 200:
            print("✅ Qdrant is running and accessible")
        else:
            print("❌ Qdrant responded with error status")
            return False
    except Exception as e:
        print("❌ Qdrant is not accessible!")
        print("   Please start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        return False
    
    # Run demo
    demo = Phase2MigrationDemo(config_path=args.config, interactive=args.interactive)
    await demo.run_demo()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)