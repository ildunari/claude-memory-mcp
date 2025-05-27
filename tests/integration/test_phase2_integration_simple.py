#!/usr/bin/env python3

import asyncio
import json
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
from datetime import datetime, timedelta
import uuid

from memory_mcp.domains.dual_collection_manager import DualCollectionManager, MigrationStateEnum
from memory_mcp.domains.manager import MemoryDomainManager
from memory_mcp.utils.config import Config


class Phase2SimpleIntegrationTester:
    """Simplified end-to-end integration test for Phase 2 dual-collection architecture."""
    
    def __init__(self):
        self.temp_dir = None
        self.config = None
        self.memory_manager = None
        self.dual_manager = None
        self.test_memories = []
        
    async def setup(self):
        """Set up test environment with temporary directories and configurations."""
        print("🔧 Setting up integration test environment...")
        
        # Create temporary directory for test
        self.temp_dir = tempfile.mkdtemp()
        print(f"   Test directory: {self.temp_dir}")
        
        # Create test config
        config_data = {
            "backend": "qdrant",
            "memory_file": f"{self.temp_dir}/memories.json",
            "qdrant": {
                "url": "http://localhost:6333",
                "collection_name": "integration_test_memories",
                "dimension": 384,
                "timeout": 30.0,
                "prefer_grpc": False
            },
            "embedding": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "local": True,
                "cache_dir": f"{self.temp_dir}/embeddings_cache"
            },
            "memory_config": {
                "max_memories": 1000,
                "importance_threshold": 0.3,
                "consolidation_threshold": 100
            }
        }
        
        config_path = f"{self.temp_dir}/test_config.json"
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        self.config = Config(config_path)
        
        # Initialize dual collection manager
        self.dual_manager = DualCollectionManager(self.config)
        await self.dual_manager.initialize()
        
        # Create test memories as dictionaries
        self.test_memories = self._create_test_memories()
        print(f"   Created {len(self.test_memories)} test memories")
        
    async def teardown(self):
        """Clean up test environment."""
        print("🧹 Cleaning up integration test environment...")
        
        try:
            # Clean up managers
            if self.dual_manager:
                await self.dual_manager.cleanup()
                
            # Remove temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("   Test directory cleaned up")
                
        except Exception as e:
            print(f"   Warning: Cleanup error: {e}")
            
    def _create_test_memories(self) -> List[Dict[str, Any]]:
        """Create diverse test memories for comprehensive testing."""
        memories = []
        base_time = datetime.now()
        
        # Conversation memories
        for i in range(5):
            memory = {
                "id": f"conv_{i}",
                "type": "conversation",
                "content": f"This is conversation memory {i} about topic {i}. It contains detailed discussion about various subjects.",
                "metadata": {
                    "participants": ["user", "assistant"],
                    "topic": f"topic_{i}",
                    "session_id": f"session_{i // 3}"
                },
                "timestamp": (base_time - timedelta(minutes=i * 10)).isoformat(),
                "importance": 0.5 + (i % 3) * 0.2
            }
            memories.append(memory)
            
        # Fact memories  
        for i in range(4):
            memory = {
                "id": f"fact_{i}",
                "type": "fact",
                "content": f"Important fact {i}: This is a verified piece of information about {['technology', 'science', 'history', 'art'][i % 4]}.",
                "metadata": {
                    "domain": ["technology", "science", "history", "art"][i % 4],
                    "verified": True,
                    "source": f"source_{i}"
                },
                "timestamp": (base_time - timedelta(hours=i * 2)).isoformat(),
                "importance": 0.7 + (i % 2) * 0.2
            }
            memories.append(memory)
            
        # Document memories
        for i in range(3):
            memory = {
                "id": f"doc_{i}",
                "type": "document",
                "content": f"Document {i}: This is a longer document containing detailed information about complex topic {i}. " * 3,
                "metadata": {
                    "title": f"Document Title {i}",
                    "author": f"Author {i}",
                    "category": ["technical", "research", "guide"][i % 3]
                },
                "timestamp": (base_time - timedelta(days=i)).isoformat(),
                "importance": 0.6 + (i % 3) * 0.1
            }
            memories.append(memory)
            
        return memories
        
    async def test_dual_collection_basic_operations(self) -> bool:
        """Test basic dual collection operations."""
        print("\n📋 Testing basic dual collection operations...")
        
        try:
            # Store memories in primary collection
            print("   Storing memories in primary collection...")
            for memory in self.test_memories:
                success = await self.dual_manager.store_memory(memory)
                if not success:
                    print(f"   ❌ Failed to store memory {memory['id']}")
                    return False
                    
            print(f"   ✅ Successfully stored {len(self.test_memories)} memories")
            
            # Verify primary collection size
            primary_count = await self.dual_manager.get_collection_size("primary")
            print(f"   📊 Primary collection size: {primary_count}")
            
            if primary_count != len(self.test_memories):
                print(f"   ❌ Primary collection size mismatch. Expected: {len(self.test_memories)}, Got: {primary_count}")
                return False
                
            # Test search in primary collection
            print("   Testing search in primary collection...")
            results = await self.dual_manager.search_memories("conversation topic", limit=3)
            
            if not results:
                print("   ❌ No search results found")
                return False
                
            print(f"   ✅ Found {len(results)} search results")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Basic operations error: {e}")
            return False
            
    async def test_migration_workflow(self) -> bool:
        """Test the complete migration workflow."""
        print("\n📋 Testing migration workflow...")
        
        try:
            # Start migration
            print("   Starting migration to larger embedding model...")
            
            migration_config = {
                "batch_size": 3,
                "quality_threshold": 0.7,
                "max_retries": 2,
                "validation_sample_size": 2
            }
            
            success = await self.dual_manager.start_migration(
                target_model="sentence-transformers/all-mpnet-base-v2",
                target_dimension=768,
                migration_config=migration_config
            )
            
            if not success:
                print("   ❌ Failed to start migration")
                return False
                
            print("   ✅ Migration started successfully")
            
            # Execute migration steps
            print("   Executing migration steps...")
            
            max_iterations = 15
            iteration = 0
            
            while iteration < max_iterations:
                migration_state = await self.dual_manager.get_migration_state()
                
                print(f"   📊 Iteration {iteration}: State={migration_state.current_state}, Progress={migration_state.progress:.1%}")
                
                if migration_state.current_state == MigrationStateEnum.CLEANUP:
                    print("   ✅ Migration completed successfully")
                    break
                    
                # Execute next migration step
                try:
                    next_state = await self.dual_manager.migration_engine.execute_migration_step(migration_state)
                    print(f"   ➡️  State transition: {migration_state.current_state} → {next_state}")
                except Exception as e:
                    print(f"   ❌ Migration step failed: {e}")
                    return False
                    
                iteration += 1
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)
                
            if iteration >= max_iterations:
                print("   ⚠️  Migration did not complete within expected iterations")
                return False
                
            # Verify final state
            final_state = await self.dual_manager.get_migration_state()
            if final_state.current_state != MigrationStateEnum.CLEANUP:
                print(f"   ❌ Expected CLEANUP state, got {final_state.current_state}")
                return False
                
            return True
            
        except Exception as e:
            print(f"   ❌ Migration workflow error: {e}")
            return False
            
    async def test_search_fusion_during_migration(self) -> bool:
        """Test search result fusion during migration."""
        print("\n📋 Testing search result fusion during migration...")
        
        try:
            # Start a new migration for testing
            print("   Starting migration for fusion testing...")
            
            migration_config = {
                "batch_size": 2,
                "quality_threshold": 0.6,
                "max_retries": 2,
                "validation_sample_size": 1
            }
            
            success = await self.dual_manager.start_migration(
                target_model="sentence-transformers/all-mpnet-base-v2",
                target_dimension=768,
                migration_config=migration_config
            )
            
            if not success:
                print("   ❌ Failed to start migration for fusion testing")
                return False
                
            # Progress to shadow mode
            migration_state = await self.dual_manager.get_migration_state()
            await self.dual_manager.migration_engine.execute_migration_step(migration_state)
            
            # Test dual collection search (fusion)
            print("   Testing dual collection search with fusion...")
            
            test_queries = [
                "conversation topic",
                "fact technology", 
                "document information"
            ]
            
            for query in test_queries:
                results = await self.dual_manager.search_dual_collections(query, limit=3)
                
                if not results:
                    print(f"   ⚠️  No results for query: {query}")
                    continue
                    
                # Verify results have fusion metadata
                fusion_found = False
                for result in results:
                    if hasattr(result, 'fusion_metadata'):
                        fusion_found = True
                        break
                        
                if fusion_found:
                    print(f"   ✅ Query '{query}' returned {len(results)} fused results")
                else:
                    print(f"   ⚠️  Query '{query}' results missing fusion metadata")
                    
            return True
            
        except Exception as e:
            print(f"   ❌ Search fusion error: {e}")
            return False
            
    async def test_error_handling_and_rollback(self) -> bool:
        """Test error handling and rollback capabilities."""
        print("\n📋 Testing error handling and rollback...")
        
        try:
            # Test rollback capability
            print("   Testing migration rollback...")
            
            # Start a migration
            success = await self.dual_manager.start_migration(
                target_model="sentence-transformers/all-mpnet-base-v2",
                target_dimension=768,
                migration_config={"batch_size": 1}
            )
            
            if not success:
                print("   ❌ Failed to start migration for rollback test")
                return False
                
            # Simulate rollback
            migration_state = await self.dual_manager.get_migration_state()
            rollback_success = await self.dual_manager.rollback_migration(
                migration_state, reason="Integration test rollback"
            )
            
            if not rollback_success:
                print("   ❌ Rollback failed")
                return False
                
            print("   ✅ Rollback completed successfully")
            
            # Verify system state after rollback
            final_state = await self.dual_manager.get_migration_state()
            if final_state and final_state.current_state != MigrationStateEnum.PREPARATION:
                print(f"   ⚠️  Unexpected state after rollback: {final_state.current_state}")
                
            return True
            
        except Exception as e:
            print(f"   ❌ Error handling test error: {e}")
            return False
            
    async def run_integration_test(self) -> bool:
        """Run complete integration test."""
        print("🚀 Starting Phase 2 Simplified Integration Test")
        print("=" * 60)
        
        test_phases = [
            ("Basic Operations", self.test_dual_collection_basic_operations),
            ("Migration Workflow", self.test_migration_workflow), 
            ("Search Fusion", self.test_search_fusion_during_migration),
            ("Error Handling", self.test_error_handling_and_rollback)
        ]
        
        results = {}
        overall_success = True
        
        for phase_name, test_func in test_phases:
            print(f"\n⏱️  Starting {phase_name}...")
            
            try:
                success = await test_func()
                results[phase_name] = "PASS" if success else "FAIL"
                
                if success:
                    print(f"✅ {phase_name}: PASS")
                else:
                    print(f"❌ {phase_name}: FAIL")
                    overall_success = False
                    
            except Exception as e:
                print(f"❌ {phase_name}: ERROR - {e}")
                results[phase_name] = f"ERROR: {e}"
                overall_success = False
                
        # Print final results
        print("\n" + "=" * 60)
        print("🎯 INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        for phase_name, result in results.items():
            status_icon = "✅" if result == "PASS" else "❌"
            print(f"{status_icon} {phase_name}: {result}")
            
        print("\n" + "=" * 60)
        
        if overall_success:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Phase 2 dual-collection architecture is functional")
        else:
            print("❌ SOME INTEGRATION TESTS FAILED")
            print("🔧 Review failed phases and fix issues before deployment")
            
        return overall_success


async def main():
    """Main test runner."""
    tester = Phase2SimpleIntegrationTester()
    
    try:
        await tester.setup()
        success = await tester.run_integration_test()
        return success
        
    finally:
        await tester.teardown()


if __name__ == "__main__":
    # Run the integration test
    success = asyncio.run(main())
    exit(0 if success else 1)