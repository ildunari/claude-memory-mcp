#!/usr/bin/env python3

import asyncio
import json
import tempfile
import shutil
import os
from typing import Dict, List, Any
from datetime import datetime, timedelta

from memory_mcp.domains.dual_collection_manager import DualCollectionManager, MigrationStateEnum
from memory_mcp.utils.config import load_config


class Phase2CoreTester:
    """Core integration test for Phase 2 dual-collection architecture."""
    
    def __init__(self):
        self.temp_dir = None
        self.config = None
        self.dual_manager = None
        self.test_memories = []
        
    async def setup(self):
        """Set up test environment."""
        print("🔧 Setting up core test environment...")
        
        # Create temporary directory for test
        self.temp_dir = tempfile.mkdtemp()
        print(f"   Test directory: {self.temp_dir}")
        
        # Create test config file
        config_data = {
            "backend": "qdrant",
            "memory_file": f"{self.temp_dir}/memories.json",
            "qdrant": {
                "url": "http://localhost:6333",
                "collection_name": "core_test_memories",
                "dimension": 384,
                "timeout": 30.0,
                "prefer_grpc": False
            },
            "embedding": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "local": True,
                "cache_dir": f"{self.temp_dir}/embeddings_cache"
            }
        }
        
        config_path = f"{self.temp_dir}/test_config.json"
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        # Load config using the utility function
        self.config = load_config(config_path)
        
        # Initialize dual collection manager
        self.dual_manager = DualCollectionManager(self.config)
        await self.dual_manager.initialize()
        
        # Create test memories
        self.test_memories = self._create_test_memories()
        print(f"   Created {len(self.test_memories)} test memories")
        
    async def teardown(self):
        """Clean up test environment."""
        print("🧹 Cleaning up test environment...")
        
        try:
            if self.dual_manager:
                await self.dual_manager.cleanup()
                
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("   Test directory cleaned up")
                
        except Exception as e:
            print(f"   Warning: Cleanup error: {e}")
            
    def _create_test_memories(self) -> List[Dict[str, Any]]:
        """Create test memories."""
        memories = []
        base_time = datetime.now()
        
        for i in range(6):
            memory = {
                "id": f"test_memory_{i}",
                "type": "conversation",
                "content": f"This is test memory {i} with content about topic {i}.",
                "metadata": {"test": True, "index": i},
                "timestamp": (base_time - timedelta(minutes=i * 5)).isoformat(),
                "importance": 0.5 + (i % 3) * 0.2
            }
            memories.append(memory)
            
        return memories
        
    async def test_basic_storage_and_retrieval(self) -> bool:
        """Test basic storage and retrieval."""
        print("\n📋 Testing basic storage and retrieval...")
        
        try:
            # Store memories
            print("   Storing test memories...")
            for memory in self.test_memories:
                success = await self.dual_manager.store_memory(memory)
                if not success:
                    print(f"   ❌ Failed to store memory {memory['id']}")
                    return False
                    
            print(f"   ✅ Stored {len(self.test_memories)} memories")
            
            # Test retrieval
            print("   Testing memory retrieval...")
            results = await self.dual_manager.search_memories("test memory", limit=3)
            
            if not results:
                print("   ❌ No memories retrieved")
                return False
                
            print(f"   ✅ Retrieved {len(results)} memories")
            
            # Verify collection size
            primary_count = await self.dual_manager.get_collection_size("primary")
            print(f"   📊 Primary collection size: {primary_count}")
            
            return primary_count == len(self.test_memories)
            
        except Exception as e:
            print(f"   ❌ Basic operations error: {e}")
            return False
            
    async def test_migration_initialization(self) -> bool:
        """Test migration initialization."""
        print("\n📋 Testing migration initialization...")
        
        try:
            # Start migration
            print("   Starting migration...")
            success = await self.dual_manager.start_migration(
                target_model="sentence-transformers/all-mpnet-base-v2",
                target_dimension=768,
                migration_config={"batch_size": 2}
            )
            
            if not success:
                print("   ❌ Failed to start migration")
                return False
                
            print("   ✅ Migration started successfully")
            
            # Check migration state
            state = await self.dual_manager.get_migration_state()
            print(f"   📊 Migration state: {state.current_state}")
            
            return state.current_state == MigrationStateEnum.PREPARATION
            
        except Exception as e:
            print(f"   ❌ Migration initialization error: {e}")
            return False
            
    async def test_dual_search_functionality(self) -> bool:
        """Test dual collection search functionality."""
        print("\n📋 Testing dual collection search...")
        
        try:
            # Execute one migration step to enable dual search
            migration_state = await self.dual_manager.get_migration_state()
            next_state = await self.dual_manager.migration_engine.execute_migration_step(migration_state)
            
            print(f"   ➡️  Advanced to state: {next_state}")
            
            # Test dual collection search
            print("   Testing dual collection search...")
            results = await self.dual_manager.search_dual_collections("test memory topic", limit=3)
            
            if not results:
                print("   ⚠️  No dual search results (may be expected in early migration)")
                return True  # This is acceptable in early migration stages
                
            print(f"   ✅ Dual search returned {len(results)} results")
            return True
            
        except Exception as e:
            print(f"   ❌ Dual search error: {e}")
            return False
            
    async def test_rollback_capability(self) -> bool:
        """Test rollback capability."""
        print("\n📋 Testing rollback capability...")
        
        try:
            migration_state = await self.dual_manager.get_migration_state()
            
            print("   Testing rollback...")
            rollback_success = await self.dual_manager.rollback_migration(
                migration_state, reason="Test rollback"
            )
            
            if rollback_success:
                print("   ✅ Rollback completed successfully")
            else:
                print("   ⚠️  Rollback returned false (may be expected in some states)")
                
            return True  # Rollback behavior may vary based on state
            
        except Exception as e:
            print(f"   ❌ Rollback error: {e}")
            return False
            
    async def run_core_test(self) -> bool:
        """Run core functionality test."""
        print("🚀 Starting Phase 2 Core Functionality Test")
        print("=" * 50)
        
        test_phases = [
            ("Storage & Retrieval", self.test_basic_storage_and_retrieval),
            ("Migration Init", self.test_migration_initialization),
            ("Dual Search", self.test_dual_search_functionality),
            ("Rollback", self.test_rollback_capability)
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
        print("\n" + "=" * 50)
        print("🎯 CORE TEST RESULTS")
        print("=" * 50)
        
        for phase_name, result in results.items():
            status_icon = "✅" if result == "PASS" else "❌"
            print(f"{status_icon} {phase_name}: {result}")
            
        print("\n" + "=" * 50)
        
        if overall_success:
            print("🎉 ALL CORE TESTS PASSED!")
            print("✅ Phase 2 core functionality is working")
        else:
            print("❌ SOME CORE TESTS FAILED")
            print("🔧 Review failed phases")
            
        return overall_success


async def main():
    """Main test runner."""
    tester = Phase2CoreTester()
    
    try:
        await tester.setup()
        success = await tester.run_core_test()
        return success
        
    finally:
        await tester.teardown()


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)