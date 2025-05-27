#!/usr/bin/env python3
"""
Test script for hybrid search functionality.

This script tests the new hybrid search implementation with various
query types to demonstrate improved retrieval capabilities.
"""

import asyncio
import json
import time
from pathlib import Path

from memory_mcp.domains.manager import MemoryDomainManager
from memory_mcp.utils.config import load_config


async def load_test_memories(manager: MemoryDomainManager):
    """Load diverse test memories for search testing"""
    
    test_memories = [
        # Technical content
        {
            "type": "fact", 
            "content": "Python uses dynamic typing and garbage collection. It supports multiple programming paradigms including procedural, object-oriented and functional programming.",
            "importance": 0.8
        },
        {
            "type": "fact",
            "content": "Machine learning algorithms like neural networks require large datasets for training. Deep learning is a subset of ML using multi-layer perceptual networks.",
            "importance": 0.9
        },
        {
            "type": "code",
            "content": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            "importance": 0.7
        },
        
        # Natural language content
        {
            "type": "conversation",
            "content": "We discussed the importance of regular exercise for mental health. Studies show that 30 minutes of daily activity can significantly reduce anxiety and depression.",
            "importance": 0.6
        },
        {
            "type": "document",
            "content": "Climate change refers to long-term shifts in global temperatures and weather patterns. While climate variations are natural, human activities since the 1800s have been the main driver of climate change.",
            "importance": 0.8
        },
        
        # Mixed content with specific terms
        {
            "type": "entity",
            "content": "Apple Inc. is a multinational technology company headquartered in Cupertino, California. They design and manufacture consumer electronics, software, and online services.",
            "importance": 0.7
        },
        {
            "type": "fact",
            "content": "Quantum computing uses quantum-mechanical phenomena like superposition and entanglement to perform computations. It could solve certain problems exponentially faster than classical computers.",
            "importance": 0.9
        }
    ]
    
    print("Loading test memories...")
    memory_ids = []
    
    for memory_data in test_memories:
        memory_id = await manager.store_memory(
            memory_type=memory_data["type"],
            content={"text": memory_data["content"]},
            importance=memory_data["importance"]
        )
        memory_ids.append(memory_id)
        print(f"Stored {memory_data['type']}: {memory_id}")
    
    print(f"Loaded {len(memory_ids)} test memories")
    return memory_ids


async def test_search_queries(manager: MemoryDomainManager):
    """Test various search queries to demonstrate hybrid search capabilities"""
    
    test_queries = [
        # Exact keyword matches (should work well with BM25)
        {"query": "Python", "expected": "Programming language content"},
        {"query": "Apple", "expected": "Company information"},
        {"query": "fibonacci", "expected": "Code example"},
        
        # Semantic/contextual queries (should work well with vector search)
        {"query": "programming languages", "expected": "Python content"},
        {"query": "physical activity benefits", "expected": "Exercise content"},
        {"query": "global warming", "expected": "Climate change content"},
        {"query": "tech companies", "expected": "Apple content"},
        
        # Complex queries (should benefit from hybrid approach)
        {"query": "recursive algorithms in Python", "expected": "Code + Python content"},
        {"query": "mental health and wellness", "expected": "Exercise content"},
        {"query": "quantum superposition", "expected": "Quantum computing content"},
        
        # Challenging queries (test recall improvement)
        {"query": "ML neural nets", "expected": "Machine learning content"},
        {"query": "environmental issues", "expected": "Climate change content"},
        {"query": "Cupertino company", "expected": "Apple content"}
    ]
    
    print("\n" + "="*60)
    print("TESTING HYBRID SEARCH PERFORMANCE")
    print("="*60)
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        expected = test_case["expected"]
        
        print(f"\n[TEST {i}] Query: '{query}'")
        print(f"Expected: {expected}")
        
        start_time = time.time()
        
        # Perform search
        results = await manager.retrieve_memories(
            query=query,
            limit=10,
            include_metadata=True
        )
        
        search_time = (time.time() - start_time) * 1000
        
        print(f"Results: {len(results)} memories found ({search_time:.2f}ms)")
        
        # Display top results
        for j, result in enumerate(results[:3], 1):
            content = result["content"]
            if isinstance(content, dict):
                content = content.get("text", str(content))
            
            score = result.get("similarity", result.get("rrf_score", 0))
            search_type = result.get("search_type", "unknown")
            
            # Truncate content for display
            display_content = content[:100] + "..." if len(content) > 100 else content
            
            print(f"  {j}. [{search_type}] Score: {score:.3f}")
            print(f"     Content: {display_content}")
        
        if not results:
            print("  ⚠️  No results found!")
    
    return True


async def test_search_stats(manager: MemoryDomainManager):
    """Display search system statistics"""
    
    print("\n" + "="*60)
    print("SEARCH SYSTEM STATISTICS")
    print("="*60)
    
    stats = await manager.get_memory_stats()
    
    # General stats
    print(f"Total memories: {stats.get('total_memories', 0)}")
    print(f"Memory types: {list(stats.get('memories_by_type', {}).keys())}")
    
    # Hybrid search stats
    if "hybrid_search" in stats:
        hybrid_stats = stats["hybrid_search"]
        print(f"\nHybrid Search Status:")
        print(f"  Indexed memories: {hybrid_stats.get('indexed_memories', 0)}")
        print(f"  BM25 indexed: {hybrid_stats.get('bm25_indexed', False)}")
        print(f"  Vector weight: {hybrid_stats.get('vector_weight', 0)}")
        print(f"  BM25 weight: {hybrid_stats.get('bm25_weight', 0)}")
    
    # Configuration info
    print(f"\nConfiguration:")
    print(f"  Backend: {manager.config.get('memory', {}).get('backend', 'unknown')}")
    print(f"  Embedding model: {manager.config.get('embedding', {}).get('default_model', 'unknown')}")
    print(f"  Dimensions: {manager.config.get('embedding', {}).get('dimensions', 'unknown')}")
    print(f"  Hybrid search enabled: {manager.hybrid_search_enabled}")
    print(f"  Query expansion enabled: {manager.query_expansion_enabled}")


async def main():
    """Main test execution"""
    
    print("CLAUDE MEMORY MCP - HYBRID SEARCH TEST")
    print("="*60)
    
    # Load configuration
    config_path = Path("config.qdrant.json")
    if not config_path.exists():
        print("❌ config.qdrant.json not found!")
        return
    
    config = load_config(str(config_path))
    
    # Initialize manager
    print("Initializing memory manager...")
    manager = MemoryDomainManager(config)
    await manager.initialize()
    
    # Check if hybrid search is available
    if not manager.hybrid_search_enabled:
        print("⚠️  Hybrid search not enabled in configuration")
        print("   Set 'retrieval.hybrid_search': true in config.qdrant.json")
        return
    
    try:
        # Load test data
        await load_test_memories(manager)
        
        # Wait a moment for indexing
        print("Waiting for indexing to complete...")
        await asyncio.sleep(2)
        
        # Test search functionality
        await test_search_queries(manager)
        
        # Display statistics
        await test_search_stats(manager)
        
        print("\n" + "="*60)
        print("✅ HYBRID SEARCH TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())