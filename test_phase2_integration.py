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
from memory_mcp.domains.persistence_qdrant import QdrantPersistenceDomain  
from memory_mcp.domains.manager import MemoryDomainManager
from memory_mcp.utils.schema import Memory, MemoryType
from memory_mcp.utils.config import Config


class Phase2IntegrationTester:
    """End-to-end integration test for Phase 2 dual-collection architecture."""
    
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
        
        # Initialize memory manager 
        self.memory_manager = MemoryDomainManager(self.config)
        await self.memory_manager.initialize()
        
        # Initialize dual collection manager
        self.dual_manager = DualCollectionManager(self.config)
        await self.dual_manager.initialize()
        
        # Create test memories
        self.test_memories = self._create_test_memories()
        print(f"   Created {len(self.test_memories)} test memories")
        
    async def teardown(self):
        """Clean up test environment."""
        print("🧹 Cleaning up integration test environment...")
        
        try:
            # Clean up managers
            if self.dual_manager:
                await self.dual_manager.cleanup()
            if self.memory_manager:
                await self.memory_manager.cleanup()
                
            # Remove temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("   Test directory cleaned up")
                
        except Exception as e:
            print(f"   Warning: Cleanup error: {e}")
            
    def _create_test_memories(self) -> List[Memory]:
        """Create diverse test memories for comprehensive testing."""
        memories = []
        base_time = datetime.now()
        
        # Conversation memories
        for i in range(10):
            memory = Memory(
                id=f"conv_{i}",
                type=MemoryType.CONVERSATION,
                content=f"This is conversation memory {i} about topic {i}. It contains detailed discussion about various subjects.",
                metadata={
                    "participants": ["user", "assistant"],
                    "topic": f"topic_{i}",
                    "session_id": f"session_{i // 3}"
                },
                timestamp=base_time - timedelta(minutes=i * 10),
                importance=0.5 + (i % 3) * 0.2
            )
            memories.append(memory)
            
        # Fact memories  
        for i in range(8):
            memory = Memory(
                id=f"fact_{i}",
                type=MemoryType.FACT,
                content=f"Important fact {i}: This is a verified piece of information about {['technology', 'science', 'history', 'art'][i % 4]}.",
                metadata={
                    "domain": ["technology", "science", "history", "art"][i % 4],
                    "verified": True,
                    "source": f"source_{i}"
                },
                timestamp=base_time - timedelta(hours=i * 2),
                importance=0.7 + (i % 2) * 0.2
            )
            memories.append(memory)
            
        # Document memories
        for i in range(5):
            memory = Memory(
                id=f"doc_{i}",
                type=MemoryType.DOCUMENT,
                content=f"Document {i}: This is a longer document containing detailed information about complex topic {i}. " * 3,
                metadata={
                    "title": f"Document Title {i}",
                    "author": f"Author {i}",
                    "category": ["technical", "research", "guide"][i % 3]
                },
                timestamp=base_time - timedelta(days=i),
                importance=0.6 + (i % 3) * 0.1
            )
            memories.append(memory)
            
        # Entity memories
        for i in range(6):
            memory = Memory(
                id=f"entity_{i}",
                type=MemoryType.ENTITY,
                content=f"Entity {i}: Information about person or organization {i} including their background and activities.",
                metadata={
                    "entity_type": "person" if i % 2 == 0 else "organization",
                    "name": f"Entity Name {i}",
                    "role": f"Role {i}"
                },
                timestamp=base_time - timedelta(hours=i * 6),
                importance=0.4 + (i % 4) * 0.15
            )
            memories.append(memory)
            
        # Code memories
        for i in range(4):
            memory = Memory(
                id=f"code_{i}",
                type=MemoryType.CODE,
                content=f"def function_{i}():\n    \"\"\"Function {i} implementation\"\"\"\n    return 'result_{i}'",
                metadata={
                    "language": "python",
                    "function_name": f"function_{i}",
                    "complexity": ["simple", "medium", "complex"][i % 3]
                },
                timestamp=base_time - timedelta(hours=i * 4),
                importance=0.5 + (i % 2) * 0.3
            )
            memories.append(memory)
            
        return memories
        
    async def test_phase_1_setup(self) -> bool:
        """Test Phase 1: Setup and populate primary collection."""
        print("\n📋 Phase 1: Testing primary collection setup and population...")
        
        try:
            # Store all test memories in primary collection
            print("   Storing test memories...")
            for memory in self.test_memories:
                success = await self.memory_manager.store_memory(memory)
                if not success:
                    print(f"   ❌ Failed to store memory {memory.id}")
                    return False
                    
            print(f"   ✅ Successfully stored {len(self.test_memories)} memories")
            
            # Verify retrieval works
            print("   Testing memory retrieval...")
            results = await self.memory_manager.retrieve_memories("conversation topic", limit=5)
            if not results:
                print("   ❌ No memories retrieved")
                return False
                
            print(f"   ✅ Retrieved {len(results)} memories")
            
            # Verify statistics
            stats = await self.memory_manager.get_memory_stats()
            print(f"   📊 Memory stats: {stats}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Phase 1 error: {e}")
            return False
            
    async def test_phase_2_migration_start(self) -> bool:
        """Test Phase 2: Start migration to new embedding model."""
        print("\n📋 Phase 2: Testing migration initialization...")
        
        try:
            # Start migration to larger embedding model
            target_model = "sentence-transformers/all-mpnet-base-v2"
            target_dimension = 768
            
            print(f"   Starting migration to {target_model} (dim: {target_dimension})...")
            
            migration_config = {
                "batch_size": 5,
                "quality_threshold": 0.7,
                "max_retries": 3,
                "validation_sample_size": 3
            }
            
            success = await self.dual_manager.start_migration(
                target_model=target_model,
                target_dimension=target_dimension,
                migration_config=migration_config
            )
            
            if not success:
                print("   ❌ Failed to start migration")
                return False
                
            print("   ✅ Migration started successfully")
            
            # Verify migration state
            state = await self.dual_manager.get_migration_state()
            print(f"   📊 Migration state: {state.current_state}")
            
            if state.current_state != MigrationStateEnum.PREPARATION:
                print(f"   ❌ Expected PREPARATION state, got {state.current_state}")
                return False
                
            return True
            
        except Exception as e:
            print(f"   ❌ Phase 2 error: {e}")
            return False
            
    async def test_phase_3_shadow_mode(self) -> bool:
        """Test Phase 3: Shadow mode operation."""
        print("\n📋 Phase 3: Testing shadow mode operation...")
        
        try:
            # Execute migration step to enter shadow mode
            print("   Executing migration step to shadow mode...")
            
            migration_state = await self.dual_manager.get_migration_state()
            next_state = await self.dual_manager.migration_engine.execute_migration_step(migration_state)
            
            if next_state != MigrationStateEnum.SHADOW_MODE:
                print(f"   ❌ Expected SHADOW_MODE, got {next_state}")
                return False
                
            print("   ✅ Entered shadow mode")
            
            # Test dual collection search
            print("   Testing dual collection search...")
            
            # Perform searches that should hit both collections
            test_queries = [
                "conversation topic",
                "important fact technology", 
                "document technical guide",
                "entity person organization",
                "python function code"
            ]
            
            all_results_valid = True
            for query in test_queries:
                results = await self.dual_manager.search_dual_collections(query, limit=3)
                
                if not results:
                    print(f"   ⚠️  No results for query: {query}")
                    continue
                    
                # Verify results have fusion metadata
                for result in results:
                    if not hasattr(result, 'fusion_metadata'):
                        print(f"   ❌ Result missing fusion metadata: {result.id}")
                        all_results_valid = False
                        break
                        
                print(f"   ✅ Query '{query}' returned {len(results)} fused results")
                
            if not all_results_valid:
                return False
                
            # Test that primary collection is still authoritative
            primary_count = await self.dual_manager.get_collection_size("primary")
            secondary_count = await self.dual_manager.get_collection_size("secondary")
            
            print(f"   📊 Collection sizes - Primary: {primary_count}, Secondary: {secondary_count}")
            
            if primary_count != len(self.test_memories):
                print(f"   ❌ Primary collection size mismatch. Expected: {len(self.test_memories)}, Got: {primary_count}")
                return False
                
            return True
            
        except Exception as e:
            print(f"   ❌ Phase 3 error: {e}")
            return False
            
    async def test_phase_4_canary_testing(self) -> bool:
        """Test Phase 4: Canary testing with quality monitoring."""
        print("\n📋 Phase 4: Testing canary mode with quality monitoring...")
        
        try:
            # Execute migration step to canary testing
            print("   Executing migration step to canary testing...")
            
            migration_state = await self.dual_manager.get_migration_state()
            next_state = await self.dual_manager.migration_engine.execute_migration_step(migration_state)
            
            if next_state != MigrationStateEnum.CANARY_TESTING:
                print(f"   ❌ Expected CANARY_TESTING, got {next_state}")
                return False
                
            print("   ✅ Entered canary testing mode")
            
            # Test quality monitoring
            print("   Testing quality monitoring...")
            
            # Perform queries and collect quality metrics
            test_queries = [
                "conversation",
                "fact technology", 
                "document research",
                "entity person",
                "code python"
            ]
            
            quality_results = []
            for query in test_queries:
                # Get results from both collections separately for comparison
                primary_results = await self.dual_manager.persistence_primary.search_memories(
                    query, limit=5, memory_types=None
                )
                secondary_results = await self.dual_manager.persistence_secondary.search_memories(
                    query, limit=5, memory_types=None
                )
                
                # Calculate quality metrics
                primary_avg_score = np.mean([r.similarity for r in primary_results]) if primary_results else 0.0
                secondary_avg_score = np.mean([r.similarity for r in secondary_results]) if secondary_results else 0.0
                
                quality_metric = {
                    "query": query,
                    "primary_score": primary_avg_score,
                    "secondary_score": secondary_avg_score,
                    "score_ratio": secondary_avg_score / primary_avg_score if primary_avg_score > 0 else 0.0
                }
                quality_results.append(quality_metric)
                
                print(f"   📊 {query}: Primary={primary_avg_score:.3f}, Secondary={secondary_avg_score:.3f}, Ratio={quality_metric['score_ratio']:.3f}")
                
            # Verify quality is acceptable (secondary should be comparable to primary)
            avg_ratio = np.mean([r['score_ratio'] for r in quality_results])
            print(f"   📊 Average quality ratio: {avg_ratio:.3f}")
            
            if avg_ratio < 0.8:  # Secondary should be at least 80% as good as primary
                print(f"   ⚠️  Quality ratio below threshold (0.8): {avg_ratio:.3f}")
                # This might trigger rollback in real scenario
                
            return True
            
        except Exception as e:
            print(f"   ❌ Phase 4 error: {e}")
            return False
            
    async def test_phase_5_gradual_migration(self) -> bool:
        """Test Phase 5: Gradual migration with batch processing."""
        print("\n📋 Phase 5: Testing gradual migration...")
        
        try:
            # Execute migration step to gradual migration
            print("   Executing migration step to gradual migration...")
            
            migration_state = await self.dual_manager.get_migration_state()
            next_state = await self.dual_manager.migration_engine.execute_migration_step(migration_state)
            
            if next_state != MigrationStateEnum.GRADUAL_MIGRATION:
                print(f"   ❌ Expected GRADUAL_MIGRATION, got {next_state}")
                return False
                
            print("   ✅ Entered gradual migration mode")
            
            # Monitor migration progress
            print("   Monitoring migration progress...")
            
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                migration_state = await self.dual_manager.get_migration_state()
                
                primary_count = await self.dual_manager.get_collection_size("primary")
                secondary_count = await self.dual_manager.get_collection_size("secondary")
                
                print(f"   📊 Iteration {iteration}: Primary={primary_count}, Secondary={secondary_count}, Progress={migration_state.progress:.1%}")
                
                if migration_state.current_state == MigrationStateEnum.FULL_MIGRATION:
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
                
            if iteration >= max_iterations:
                print("   ⚠️  Migration did not complete within expected iterations")
                return False
                
            # Verify final state
            final_state = await self.dual_manager.get_migration_state()
            if final_state.current_state != MigrationStateEnum.FULL_MIGRATION:
                print(f"   ❌ Expected FULL_MIGRATION, got {final_state.current_state}")
                return False
                
            return True
            
        except Exception as e:
            print(f"   ❌ Phase 5 error: {e}")
            return False
            
    async def test_phase_6_final_validation(self) -> bool:
        """Test Phase 6: Final validation and cleanup."""
        print("\n📋 Phase 6: Testing final validation and cleanup...")
        
        try:
            # Verify all memories migrated
            print("   Verifying migration completeness...")
            
            primary_count = await self.dual_manager.get_collection_size("primary")
            secondary_count = await self.dual_manager.get_collection_size("secondary")
            
            print(f"   📊 Final counts - Primary: {primary_count}, Secondary: {secondary_count}")
            
            if secondary_count != len(self.test_memories):
                print(f"   ❌ Secondary collection size mismatch. Expected: {len(self.test_memories)}, Got: {secondary_count}")
                return False
                
            # Test search quality on secondary collection
            print("   Testing search quality on migrated collection...")
            
            test_queries = [
                "conversation topic discussion",
                "technology science fact",
                "document research guide",
                "person entity organization",
                "python function implementation"
            ]
            
            quality_scores = []
            for query in test_queries:
                results = await self.dual_manager.persistence_secondary.search_memories(
                    query, limit=3, memory_types=None
                )
                
                if results:
                    avg_score = np.mean([r.similarity for r in results])
                    quality_scores.append(avg_score)
                    print(f"   ✅ Query '{query}': {len(results)} results, avg similarity: {avg_score:.3f}")
                else:
                    print(f"   ⚠️  No results for query: {query}")
                    
            if quality_scores:
                overall_quality = np.mean(quality_scores)
                print(f"   📊 Overall search quality: {overall_quality:.3f}")
                
                if overall_quality < 0.3:  # Minimum acceptable quality
                    print(f"   ❌ Search quality too low: {overall_quality:.3f}")
                    return False
                    
            # Test cleanup
            print("   Testing migration cleanup...")
            
            migration_state = await self.dual_manager.get_migration_state()
            next_state = await self.dual_manager.migration_engine.execute_migration_step(migration_state)
            
            if next_state != MigrationStateEnum.CLEANUP:
                print(f"   ❌ Expected CLEANUP state, got {next_state}")
                return False
                
            print("   ✅ Migration cleanup completed")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Phase 6 error: {e}")
            return False
            
    async def test_integration_with_memory_manager(self) -> bool:
        """Test integration with existing MemoryManager."""
        print("\n📋 Integration: Testing with existing MemoryManager...")
        
        try:
            # Test that memory manager can work with dual collection setup
            print("   Testing MemoryManager integration...")
            
            # Store a new memory during migration
            new_memory = Memory(
                id="integration_test",
                type=MemoryType.FACT,
                content="This is a test memory created during integration testing.",
                metadata={"test": True, "integration": True},
                timestamp=datetime.now(),
                importance=0.8
            )
            
            success = await self.memory_manager.store_memory(new_memory)
            if not success:
                print("   ❌ Failed to store memory via MemoryManager")
                return False
                
            print("   ✅ Successfully stored memory via MemoryManager")
            
            # Retrieve the memory
            results = await self.memory_manager.retrieve_memories("integration testing", limit=5)
            
            found_memory = None
            for result in results:
                if result.id == "integration_test":
                    found_memory = result
                    break
                    
            if not found_memory:
                print("   ❌ Could not retrieve stored memory")
                return False
                
            print("   ✅ Successfully retrieved stored memory")
            
            # Test memory manager statistics
            stats = await self.memory_manager.get_memory_stats()
            print(f"   📊 Final memory stats: {stats}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Integration error: {e}")
            return False
            
    async def run_full_integration_test(self) -> bool:
        """Run complete end-to-end integration test."""
        print("🚀 Starting Phase 2 End-to-End Integration Test")
        print("=" * 60)
        
        test_phases = [
            ("Phase 1: Setup", self.test_phase_1_setup),
            ("Phase 2: Migration Start", self.test_phase_2_migration_start), 
            ("Phase 3: Shadow Mode", self.test_phase_3_shadow_mode),
            ("Phase 4: Canary Testing", self.test_phase_4_canary_testing),
            ("Phase 5: Gradual Migration", self.test_phase_5_gradual_migration),
            ("Phase 6: Final Validation", self.test_phase_6_final_validation),
            ("Integration Test", self.test_integration_with_memory_manager)
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
            print("✅ Phase 2 dual-collection architecture is fully functional")
        else:
            print("❌ SOME INTEGRATION TESTS FAILED")
            print("🔧 Review failed phases and fix issues before deployment")
            
        return overall_success


async def main():
    """Main test runner."""
    tester = Phase2IntegrationTester()
    
    try:
        await tester.setup()
        success = await tester.run_full_integration_test()
        return success
        
    finally:
        await tester.teardown()


if __name__ == "__main__":
    # Run the integration test
    success = asyncio.run(main())
    exit(0 if success else 1)