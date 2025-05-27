#!/usr/bin/env python3
"""
Comprehensive stress test for Qdrant integration.
Tests performance, reliability, and edge cases.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Any
import random
import string

from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from memory_mcp.domains.persistence_qdrant import QdrantPersistenceDomain


class QdrantStressTester:
    """Comprehensive stress tester for Qdrant integration."""
    
    def __init__(self, config_path: str = "./config.qdrant.json"):
        self.config_path = config_path
        self.persistence = None
        self.test_results = {}
        
    async def initialize(self):
        """Initialize the test environment."""
        logger.info("Initializing Qdrant stress tester")
        
        # Load config
        with open(self.config_path, "r") as f:
            config = json.load(f)
        
        # Initialize persistence domain
        self.persistence = QdrantPersistenceDomain(config)
        await self.persistence.initialize()
        
        logger.info("Stress tester initialized")
    
    def generate_test_memory(self, memory_type: str = "fact", size: str = "small") -> Dict[str, Any]:
        """Generate a test memory of specified type and size."""
        
        # Content size variants
        if size == "small":
            content_length = random.randint(10, 100)
        elif size == "medium":
            content_length = random.randint(100, 1000)
        else:  # large
            content_length = random.randint(1000, 5000)
        
        # Generate random content
        content_text = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=content_length))
        
        # Memory type-specific content
        if memory_type == "fact":
            return {
                "type": "fact",
                "content": {
                    "fact": f"Test fact: {content_text}",
                    "confidence": random.uniform(0.5, 1.0),
                    "domain": random.choice(["science", "history", "geography", "technology"])
                },
                "importance": random.uniform(0.3, 1.0),
                "metadata": {
                    "source": "stress_test",
                    "test_size": size
                }
            }
        elif memory_type == "conversation":
            return {
                "type": "conversation",
                "content": {
                    "user_message": f"User: {content_text[:len(content_text)//2]}",
                    "assistant_response": f"Assistant: {content_text[len(content_text)//2:]}",
                    "turn_number": random.randint(1, 50)
                },
                "importance": random.uniform(0.2, 0.8),
                "metadata": {
                    "conversation_id": f"test_conv_{random.randint(1, 1000)}",
                    "test_size": size
                }
            }
        elif memory_type == "document":
            return {
                "type": "document",
                "content": {
                    "title": f"Test Document {random.randint(1, 1000)}",
                    "content": content_text,
                    "summary": content_text[:100] + "..."
                },
                "importance": random.uniform(0.4, 0.9),
                "metadata": {
                    "document_type": "test",
                    "test_size": size
                }
            }
        else:
            # Generic memory
            return {
                "type": memory_type,
                "content": content_text,
                "importance": random.uniform(0.1, 1.0),
                "metadata": {
                    "test_size": size,
                    "generated": True
                }
            }
    
    async def test_basic_operations(self) -> Dict[str, Any]:
        """Test basic CRUD operations."""
        logger.info("Testing basic CRUD operations")
        
        results = {
            "store_times": [],
            "retrieve_times": [],
            "update_times": [],
            "delete_times": [],
            "errors": []
        }
        
        test_memories = []
        
        # Test store operations
        for i in range(100):
            memory = self.generate_test_memory()
            
            start_time = time.time()
            try:
                await self.persistence.store_memory(memory, "short_term")
                store_time = time.time() - start_time
                results["store_times"].append(store_time)
                test_memories.append(memory)
            except Exception as e:
                results["errors"].append(f"Store error {i}: {e}")
        
        # Test retrieve operations
        for memory in test_memories[:50]:  # Test first 50
            start_time = time.time()
            try:
                retrieved = await self.persistence.get_memory(memory["id"])
                retrieve_time = time.time() - start_time
                results["retrieve_times"].append(retrieve_time)
                
                if not retrieved:
                    results["errors"].append(f"Memory {memory['id']} not found")
            except Exception as e:
                results["errors"].append(f"Retrieve error: {e}")
        
        # Test update operations
        for memory in test_memories[:25]:  # Test first 25
            memory["importance"] = random.uniform(0.5, 1.0)
            memory["metadata"]["updated"] = True
            
            start_time = time.time()
            try:
                await self.persistence.update_memory(memory, "long_term")
                update_time = time.time() - start_time
                results["update_times"].append(update_time)
            except Exception as e:
                results["errors"].append(f"Update error: {e}")
        
        # Test delete operations
        delete_ids = [m["id"] for m in test_memories[50:75]]  # Delete 25 memories
        
        start_time = time.time()
        try:
            success = await self.persistence.delete_memories(delete_ids)
            delete_time = time.time() - start_time
            results["delete_times"].append(delete_time)
            
            if not success:
                results["errors"].append("Bulk delete failed")
        except Exception as e:
            results["errors"].append(f"Delete error: {e}")
        
        return results
    
    async def test_search_performance(self) -> Dict[str, Any]:
        """Test search performance with various query sizes and filters."""
        logger.info("Testing search performance")
        
        results = {
            "search_times": [],
            "search_results_counts": [],
            "embedding_times": [],
            "errors": []
        }
        
        # Generate test queries
        test_queries = [
            "science and technology facts",
            "conversation about programming",
            "historical events and dates",
            "geographic information",
            "test document content",
            "user preferences and settings",
            "code examples and snippets",
            "important business decisions"
        ]
        
        for query in test_queries:
            # Test embedding generation
            start_time = time.time()
            try:
                embedding = await self.persistence.generate_embedding(query)
                embedding_time = time.time() - start_time
                results["embedding_times"].append(embedding_time)
                
                # Test search
                start_time = time.time()
                search_results = await self.persistence.search_memories(
                    embedding=embedding,
                    limit=20,
                    min_similarity=0.5
                )
                search_time = time.time() - start_time
                
                results["search_times"].append(search_time)
                results["search_results_counts"].append(len(search_results))
                
            except Exception as e:
                results["errors"].append(f"Search error for '{query}': {e}")
        
        # Test filtered searches
        memory_types = ["fact", "conversation", "document"]
        tiers = ["short_term", "long_term", "archived"]
        
        for memory_type in memory_types:
            for tier in tiers:
                query = f"test {memory_type} in {tier}"
                
                try:
                    embedding = await self.persistence.generate_embedding(query)
                    
                    start_time = time.time()
                    filtered_results = await self.persistence.search_memories(
                        embedding=embedding,
                        limit=10,
                        types=[memory_type],
                        tier=tier,
                        min_similarity=0.3
                    )
                    search_time = time.time() - start_time
                    
                    results["search_times"].append(search_time)
                    results["search_results_counts"].append(len(filtered_results))
                    
                except Exception as e:
                    results["errors"].append(f"Filtered search error: {e}")
        
        return results
    
    async def test_bulk_operations(self) -> Dict[str, Any]:
        """Test bulk operations and high load scenarios."""
        logger.info("Testing bulk operations")
        
        results = {
            "bulk_store_times": [],
            "bulk_retrieve_times": [],
            "concurrent_operation_times": [],
            "errors": []
        }
        
        # Test bulk storage
        batch_sizes = [50, 100, 500, 1000]
        
        for batch_size in batch_sizes:
            logger.info(f"Testing batch size: {batch_size}")
            
            # Generate batch of memories
            memories = []
            for i in range(batch_size):
                memory_type = random.choice(["fact", "conversation", "document", "entity"])
                size = random.choice(["small", "medium", "large"])
                memories.append(self.generate_test_memory(memory_type, size))
            
            # Test batch storage
            start_time = time.time()
            try:
                for memory in memories:
                    tier = random.choice(["short_term", "long_term", "archived"])
                    await self.persistence.store_memory(memory, tier)
                
                bulk_store_time = time.time() - start_time
                results["bulk_store_times"].append({
                    "batch_size": batch_size,
                    "time": bulk_store_time,
                    "avg_per_item": bulk_store_time / batch_size
                })
                
            except Exception as e:
                results["errors"].append(f"Bulk store error (batch {batch_size}): {e}")
        
        # Test concurrent operations
        async def concurrent_store_task(memory_batch: List[Dict]):
            for memory in memory_batch:
                await self.persistence.store_memory(memory, "short_term")
        
        # Create concurrent batches
        concurrent_batches = []
        for i in range(5):  # 5 concurrent tasks
            batch = [self.generate_test_memory() for _ in range(20)]
            concurrent_batches.append(batch)
        
        start_time = time.time()
        try:
            tasks = [concurrent_store_task(batch) for batch in concurrent_batches]
            await asyncio.gather(*tasks)
            
            concurrent_time = time.time() - start_time
            results["concurrent_operation_times"].append({
                "total_items": 100,
                "concurrent_tasks": 5,
                "total_time": concurrent_time
            })
            
        except Exception as e:
            results["errors"].append(f"Concurrent operations error: {e}")
        
        return results
    
    async def test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases and error conditions."""
        logger.info("Testing edge cases")
        
        results = {
            "edge_case_results": [],
            "errors": []
        }
        
        # Test empty content
        try:
            empty_memory = {
                "type": "fact",
                "content": "",
                "importance": 0.5
            }
            await self.persistence.store_memory(empty_memory, "short_term")
            results["edge_case_results"].append("Empty content: PASSED")
        except Exception as e:
            results["edge_case_results"].append(f"Empty content: FAILED - {e}")
        
        # Test very large content
        try:
            large_content = "x" * 50000  # 50KB content
            large_memory = {
                "type": "document",
                "content": large_content,
                "importance": 0.7
            }
            await self.persistence.store_memory(large_memory, "short_term")
            results["edge_case_results"].append("Large content: PASSED")
        except Exception as e:
            results["edge_case_results"].append(f"Large content: FAILED - {e}")
        
        # Test invalid memory ID retrieval
        try:
            invalid_result = await self.persistence.get_memory("invalid_id_12345")
            if invalid_result is None:
                results["edge_case_results"].append("Invalid ID retrieval: PASSED")
            else:
                results["edge_case_results"].append("Invalid ID retrieval: FAILED - returned result")
        except Exception as e:
            results["edge_case_results"].append(f"Invalid ID retrieval: FAILED - {e}")
        
        # Test search with empty embedding
        try:
            empty_embedding = [0.0] * 384
            empty_results = await self.persistence.search_memories(empty_embedding)
            results["edge_case_results"].append(f"Empty embedding search: PASSED - {len(empty_results)} results")
        except Exception as e:
            results["edge_case_results"].append(f"Empty embedding search: FAILED - {e}")
        
        # Test extreme similarity thresholds
        try:
            test_embedding = await self.persistence.generate_embedding("test query")
            
            # Very high threshold
            high_results = await self.persistence.search_memories(test_embedding, min_similarity=0.99)
            results["edge_case_results"].append(f"High similarity threshold: PASSED - {len(high_results)} results")
            
            # Very low threshold
            low_results = await self.persistence.search_memories(test_embedding, min_similarity=0.01)
            results["edge_case_results"].append(f"Low similarity threshold: PASSED - {len(low_results)} results")
            
        except Exception as e:
            results["edge_case_results"].append(f"Similarity threshold tests: FAILED - {e}")
        
        return results
    
    async def test_memory_stats(self) -> Dict[str, Any]:
        """Test memory statistics functionality."""
        logger.info("Testing memory statistics")
        
        try:
            stats = await self.persistence.get_memory_stats()
            return {
                "stats_success": True,
                "stats": stats
            }
        except Exception as e:
            return {
                "stats_success": False,
                "error": str(e)
            }
    
    def calculate_summary_stats(self, times: List[float]) -> Dict[str, float]:
        """Calculate summary statistics for timing data."""
        if not times:
            return {}
        
        return {
            "count": len(times),
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "total": sum(times)
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive stress test suite."""
        logger.info("🚀 Starting comprehensive Qdrant stress test")
        
        overall_start = time.time()
        
        # Run all test suites
        basic_results = await self.test_basic_operations()
        search_results = await self.test_search_performance()
        bulk_results = await self.test_bulk_operations()
        edge_results = await self.test_edge_cases()
        stats_results = await self.test_memory_stats()
        
        overall_time = time.time() - overall_start
        
        # Compile comprehensive results
        comprehensive_results = {
            "overall_test_time": overall_time,
            "basic_operations": {
                "store_stats": self.calculate_summary_stats(basic_results["store_times"]),
                "retrieve_stats": self.calculate_summary_stats(basic_results["retrieve_times"]),
                "update_stats": self.calculate_summary_stats(basic_results["update_times"]),
                "delete_stats": self.calculate_summary_stats(basic_results["delete_times"]),
                "errors": basic_results["errors"]
            },
            "search_performance": {
                "search_stats": self.calculate_summary_stats(search_results["search_times"]),
                "embedding_stats": self.calculate_summary_stats(search_results["embedding_times"]),
                "avg_results_count": sum(search_results["search_results_counts"]) / len(search_results["search_results_counts"]) if search_results["search_results_counts"] else 0,
                "errors": search_results["errors"]
            },
            "bulk_operations": bulk_results,
            "edge_cases": edge_results,
            "memory_stats": stats_results
        }
        
        return comprehensive_results


async def main():
    """Main stress test execution."""
    logger.add(sys.stderr, level="INFO")
    
    logger.info("🔧 Qdrant Stress Test Suite")
    logger.info("=" * 50)
    
    # Initialize tester
    tester = QdrantStressTester()
    await tester.initialize()
    
    # Run comprehensive tests
    results = await tester.run_all_tests()
    
    # Output results
    logger.info("📊 STRESS TEST RESULTS")
    logger.info("=" * 50)
    
    print(json.dumps(results, indent=2, default=str))
    
    # Summary
    logger.info("📋 SUMMARY")
    logger.info(f"Overall test time: {results['overall_test_time']:.2f}s")
    
    # Basic operations summary
    basic = results["basic_operations"]
    if basic["store_stats"]:
        logger.info(f"Store operations: avg {basic['store_stats']['avg']*1000:.2f}ms, {basic['store_stats']['count']} operations")
    if basic["retrieve_stats"]:
        logger.info(f"Retrieve operations: avg {basic['retrieve_stats']['avg']*1000:.2f}ms, {basic['retrieve_stats']['count']} operations")
    
    # Search performance summary
    search = results["search_performance"]
    if search["search_stats"]:
        logger.info(f"Search operations: avg {search['search_stats']['avg']*1000:.2f}ms, {search['search_stats']['count']} searches")
    if search["embedding_stats"]:
        logger.info(f"Embedding generation: avg {search['embedding_stats']['avg']*1000:.2f}ms")
    
    # Error summary
    total_errors = (len(basic["errors"]) + 
                   len(search["errors"]) + 
                   len(results["bulk_operations"]["errors"]))
    
    if total_errors > 0:
        logger.warning(f"⚠️  Total errors encountered: {total_errors}")
    else:
        logger.success("✅ All tests completed without errors!")


if __name__ == "__main__":
    asyncio.run(main())