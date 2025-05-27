#!/usr/bin/env python3

"""
Quick validation script to ensure Phase 2 components are properly installed.
"""

import sys
import importlib
from pathlib import Path

def test_imports():
    """Test that all Phase 2 components can be imported."""
    print("🔍 Testing Phase 2 Component Imports...")
    
    components = [
        "memory_mcp.domains.dual_collection_manager",
        "memory_mcp.domains.search_result_fusion", 
        "memory_mcp.domains.migration_engine",
        "memory_mcp.domains.manager",
        "memory_mcp.mcp.server",
        "memory_mcp.mcp.tools"
    ]
    
    for component in components:
        try:
            importlib.import_module(component)
            print(f"   ✅ {component}")
        except ImportError as e:
            print(f"   ❌ {component}: {e}")
            return False
            
    return True

def test_files():
    """Test that all Phase 2 files exist."""
    print("\n📁 Testing Phase 2 Files...")
    
    files = [
        "memory_mcp/domains/dual_collection_manager.py",
        "memory_mcp/domains/search_result_fusion.py", 
        "memory_mcp/domains/migration_engine.py",
        "test_phase2_dual_collection.py",
        "demo_phase2_migration.py",
        "config_migration_enabled.json",
        "PHASE2_IMPLEMENTATION_COMPLETE.md"
    ]
    
    for file_path in files:
        path = Path(file_path)
        if path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - Missing!")
            return False
            
    return True

def test_manager_integration():
    """Test that MemoryDomainManager has migration methods."""
    print("\n🔗 Testing Manager Integration...")
    
    try:
        from memory_mcp.domains.manager import MemoryDomainManager
        
        # Check if migration methods exist
        methods = [
            "start_embedding_migration",
            "get_migration_status", 
            "advance_migration",
            "rollback_migration",
            "pause_migration",
            "resume_migration",
            "is_migration_available"
        ]
        
        for method in methods:
            if hasattr(MemoryDomainManager, method):
                print(f"   ✅ {method}")
            else:
                print(f"   ❌ {method} - Missing!")
                return False
                
        return True
        
    except Exception as e:
        print(f"   ❌ Manager integration test failed: {e}")
        return False

def test_mcp_tools():
    """Test that MCP tools include migration tools."""
    print("\n🛠️ Testing MCP Tool Integration...")
    
    try:
        from memory_mcp.mcp.tools import MemoryToolDefinitions
        from memory_mcp.utils.config import load_config
        
        # Create dummy config
        config = {
            "migration": {"enabled": True},
            "memory": {"backend": "qdrant"}
        }
        
        # Test tool schemas exist
        tool_def = MemoryToolDefinitions(None)
        
        schemas = [
            "start_migration_schema",
            "migration_status_schema",
            "advance_migration_schema", 
            "rollback_migration_schema",
            "pause_migration_schema",
            "resume_migration_schema"
        ]
        
        for schema in schemas:
            if hasattr(tool_def, schema):
                print(f"   ✅ {schema}")
            else:
                print(f"   ❌ {schema} - Missing!")
                return False
                
        return True
        
    except Exception as e:
        print(f"   ❌ MCP tools test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Phase 2 Validation Test")
    print("=" * 40)
    
    tests = [
        ("Import Tests", test_imports),
        ("File Tests", test_files),
        ("Manager Integration", test_manager_integration),
        ("MCP Tools", test_mcp_tools)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"   ❌ {test_name} failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 ALL PHASE 2 VALIDATION TESTS PASSED!")
        print("✅ Phase 2 dual-collection architecture is ready for use")
    else:
        print("❌ Some validation tests failed")
        print("🔧 Please check the errors above")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)