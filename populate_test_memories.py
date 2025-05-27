#!/usr/bin/env python3
"""
Populate memory MCP with diverse test memories for demonstration.

This script adds realistic memories across all types to showcase the system's capabilities.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from memory_mcp.domains.manager import MemoryDomainManager
from memory_mcp.utils.config import load_config


class MemoryPopulator:
    """Populates memory system with diverse test data."""
    
    def __init__(self, config_path: str = None):
        self.config = load_config(config_path)
        self.manager = MemoryDomainManager(self.config)
        
    async def populate_memories(self):
        """Add diverse memories across all types."""
        print("🧠 Populating Memory MCP with test memories...")
        
        # Initialize the manager
        await self.manager.initialize()
        
        memories_added = 0
        
        # 1. Conversation Memories
        conversations = [
            {
                "type": "conversation",
                "content": {
                    "user_message": "How do I implement a binary search algorithm in Python?",
                    "assistant_response": "Here's an efficient binary search implementation:\n\n```python\ndef binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n```\n\nTime complexity: O(log n), Space complexity: O(1)"
                },
                "metadata": {
                    "topic": "algorithms",
                    "programming_language": "python",
                    "difficulty": "intermediate"
                },
                "importance": 0.8
            },
            {
                "type": "conversation", 
                "content": {
                    "user_message": "What's the best way to handle async/await in JavaScript?",
                    "assistant_response": "Here are the key patterns for async/await:\n\n1. **Basic async function:**\n```javascript\nasync function fetchData() {\n  try {\n    const response = await fetch('/api/data');\n    const data = await response.json();\n    return data;\n  } catch (error) {\n    console.error('Error:', error);\n  }\n}\n```\n\n2. **Parallel execution:**\n```javascript\nconst [result1, result2] = await Promise.all([\n  fetchData1(),\n  fetchData2()\n]);\n```\n\nAlways use try/catch blocks and consider Promise.all() for parallel operations."
                },
                "metadata": {
                    "topic": "javascript",
                    "concept": "async_programming",
                    "difficulty": "intermediate"
                },
                "importance": 0.9
            },
            {
                "type": "conversation",
                "content": {
                    "user_message": "Explain the difference between React hooks and class components",
                    "assistant_response": "Key differences between React hooks and class components:\n\n**Class Components:**\n- Use lifecycle methods (componentDidMount, componentDidUpdate)\n- State managed with this.setState()\n- More verbose syntax\n- Can be harder to test and reuse logic\n\n**Hooks (Functional Components):**\n- Use useEffect for lifecycle-like behavior\n- State managed with useState\n- More concise and readable\n- Better logic reuse with custom hooks\n- Easier to test\n\nExample with hooks:\n```jsx\nfunction MyComponent() {\n  const [count, setCount] = useState(0);\n  \n  useEffect(() => {\n    document.title = `Count: ${count}`;\n  }, [count]);\n  \n  return <button onClick={() => setCount(count + 1)}>{count}</button>;\n}\n```\n\nHooks are now the recommended approach for new React applications."
                },
                "metadata": {
                    "topic": "react",
                    "concept": "hooks_vs_classes",
                    "framework": "react"
                },
                "importance": 0.85
            }
        ]
        
        for conv in conversations:
            success = await self.manager.store_memory(conv)
            if success:
                memories_added += 1
                print(f"✅ Added conversation about {conv['metadata'].get('topic', 'programming')}")
        
        # 2. Fact Memories
        facts = [
            {
                "type": "fact",
                "content": {
                    "statement": "Python's Global Interpreter Lock (GIL) prevents true multithreading for CPU-bound tasks",
                    "explanation": "The GIL allows only one thread to execute Python bytecode at a time, making threading ineffective for CPU-intensive work. Use multiprocessing or async/await for better concurrency.",
                    "context": "Python performance optimization"
                },
                "metadata": {
                    "domain": "python",
                    "category": "performance",
                    "verified": True
                },
                "importance": 0.9
            },
            {
                "type": "fact",
                "content": {
                    "statement": "REST APIs should be stateless and use standard HTTP methods",
                    "explanation": "RESTful design principles require that each request contains all necessary information. Use GET for retrieval, POST for creation, PUT for updates, DELETE for removal.",
                    "context": "API design best practices"
                },
                "metadata": {
                    "domain": "web_development",
                    "category": "api_design",
                    "verified": True
                },
                "importance": 0.8
            },
            {
                "type": "fact",
                "content": {
                    "statement": "Database indexing dramatically improves query performance but slows down writes",
                    "explanation": "Indexes create additional data structures that speed up SELECT operations but require maintenance during INSERT, UPDATE, and DELETE operations. Choose indexes carefully based on query patterns.",
                    "context": "Database optimization"
                },
                "metadata": {
                    "domain": "databases",
                    "category": "optimization", 
                    "verified": True
                },
                "importance": 0.85
            }
        ]
        
        for fact in facts:
            success = await self.manager.store_memory(fact)
            if success:
                memories_added += 1
                print(f"✅ Added fact about {fact['metadata']['domain']}")
        
        # 3. Code Memories
        code_snippets = [
            {
                "type": "code",
                "content": {
                    "title": "Efficient Array Deduplication in JavaScript",
                    "code": "// Method 1: Using Set (ES6+)\nconst uniqueArray = [...new Set(array)];\n\n// Method 2: Using filter and indexOf\nconst uniqueArray2 = array.filter((item, index) => array.indexOf(item) === index);\n\n// Method 3: Using reduce (for objects)\nconst uniqueObjects = array.reduce((acc, current) => {\n  const exists = acc.find(item => item.id === current.id);\n  if (!exists) acc.push(current);\n  return acc;\n}, []);",
                    "language": "javascript",
                    "description": "Three different approaches for removing duplicates from arrays, including objects with unique IDs"
                },
                "metadata": {
                    "language": "javascript",
                    "category": "array_manipulation",
                    "difficulty": "beginner",
                    "performance": "O(n) to O(n²)"
                },
                "importance": 0.7
            },
            {
                "type": "code",
                "content": {
                    "title": "Python Context Manager for Database Connections",
                    "code": "from contextlib import contextmanager\nimport sqlite3\n\n@contextmanager\ndef db_connection(db_path):\n    \"\"\"Context manager for database connections with automatic cleanup.\"\"\"\n    conn = None\n    try:\n        conn = sqlite3.connect(db_path)\n        conn.row_factory = sqlite3.Row  # Enable dict-like access\n        yield conn\n    except Exception as e:\n        if conn:\n            conn.rollback()\n        raise e\n    finally:\n        if conn:\n            conn.close()\n\n# Usage\nwith db_connection('app.db') as db:\n    cursor = db.cursor()\n    cursor.execute('SELECT * FROM users WHERE active = 1')\n    users = cursor.fetchall()",
                    "language": "python",
                    "description": "A reusable context manager that ensures proper database connection cleanup and error handling"
                },
                "metadata": {
                    "language": "python",
                    "category": "database",
                    "pattern": "context_manager",
                    "difficulty": "intermediate"
                },
                "importance": 0.85
            },
            {
                "type": "code",
                "content": {
                    "title": "React Custom Hook for API Data Fetching",
                    "code": "import { useState, useEffect } from 'react';\n\nfunction useApiData(url, dependencies = []) {\n  const [data, setData] = useState(null);\n  const [loading, setLoading] = useState(true);\n  const [error, setError] = useState(null);\n\n  useEffect(() => {\n    let isMounted = true;\n    \n    const fetchData = async () => {\n      try {\n        setLoading(true);\n        setError(null);\n        \n        const response = await fetch(url);\n        if (!response.ok) {\n          throw new Error(`HTTP error! status: ${response.status}`);\n        }\n        \n        const result = await response.json();\n        \n        if (isMounted) {\n          setData(result);\n        }\n      } catch (err) {\n        if (isMounted) {\n          setError(err.message);\n        }\n      } finally {\n        if (isMounted) {\n          setLoading(false);\n        }\n      }\n    };\n\n    fetchData();\n    \n    return () => {\n      isMounted = false;\n    };\n  }, [url, ...dependencies]);\n\n  return { data, loading, error };\n}\n\n// Usage\nfunction UserProfile({ userId }) {\n  const { data: user, loading, error } = useApiData(`/api/users/${userId}`, [userId]);\n  \n  if (loading) return <div>Loading...</div>;\n  if (error) return <div>Error: {error}</div>;\n  \n  return <div>Welcome, {user?.name}!</div>;\n}",
                    "language": "javascript",
                    "description": "A reusable React hook for fetching API data with loading states, error handling, and cleanup"
                },
                "metadata": {
                    "language": "javascript",
                    "framework": "react",
                    "category": "custom_hooks",
                    "pattern": "data_fetching",
                    "difficulty": "intermediate"
                },
                "importance": 0.9
            }
        ]
        
        for code in code_snippets:
            success = await self.manager.store_memory(code)
            if success:
                memories_added += 1
                print(f"✅ Added code snippet: {code['content']['title']}")
        
        # 4. Document Memories
        documents = [
            {
                "type": "document",
                "content": {
                    "title": "Microservices Architecture Best Practices",
                    "text": """
# Microservices Architecture Best Practices

## Core Principles

### 1. Single Responsibility
Each microservice should have a single, well-defined business capability. This ensures loose coupling and high cohesion.

### 2. Decentralized Data Management
- Each service owns its data
- Avoid shared databases across services
- Use event-driven patterns for data consistency

### 3. Communication Patterns
- **Synchronous**: REST APIs, GraphQL for real-time needs
- **Asynchronous**: Message queues, event streams for eventual consistency
- **Service Discovery**: Use tools like Consul, Eureka, or Kubernetes DNS

### 4. Fault Tolerance
- Implement circuit breakers (Hystrix, resilience4j)
- Use bulkhead patterns to isolate failures
- Design for graceful degradation

### 5. Monitoring and Observability
- Distributed tracing (Jaeger, Zipkin)
- Centralized logging (ELK stack, Fluentd)
- Metrics collection (Prometheus, Grafana)

## Common Pitfalls
- **Distributed Monolith**: Services too tightly coupled
- **Chatty Interfaces**: Too many service-to-service calls
- **Data Inconsistency**: Poor event handling patterns
- **Operational Complexity**: Underestimating deployment overhead

## Technology Stack Recommendations
- **API Gateway**: Kong, Zuul, AWS API Gateway
- **Service Mesh**: Istio, Linkerd for advanced networking
- **Container Orchestration**: Kubernetes, Docker Swarm
- **Message Brokers**: Apache Kafka, RabbitMQ, AWS SQS
                    """,
                    "source": "Internal Architecture Guidelines",
                    "document_type": "technical_guide"
                },
                "metadata": {
                    "domain": "software_architecture",
                    "category": "microservices",
                    "document_length": "long",
                    "target_audience": "architects"
                },
                "importance": 0.95
            },
            {
                "type": "document",
                "content": {
                    "title": "Database Performance Optimization Strategies",
                    "text": """
# Database Performance Optimization Strategies

## Indexing Strategies

### B-Tree Indexes
- Best for equality and range queries
- Automatically maintained by most databases
- Consider composite indexes for multi-column queries

### Hash Indexes
- Optimal for equality comparisons
- Not suitable for range queries
- Memory-intensive but very fast

### Partial Indexes
- Index only rows meeting specific conditions
- Reduces index size and maintenance overhead
- Example: CREATE INDEX ON orders (customer_id) WHERE status = 'pending'

## Query Optimization

### Query Analysis
1. Use EXPLAIN PLAN to understand query execution
2. Identify table scans and expensive operations
3. Check for proper index usage

### Common Optimizations
- **Avoid SELECT ***: Specify only needed columns
- **Use LIMIT**: Prevent large result sets
- **Optimize JOINs**: Ensure join conditions use indexed columns
- **Subquery vs JOIN**: Often JOINs perform better than correlated subqueries

## Connection Management

### Connection Pooling
- Reuse database connections to reduce overhead
- Configure appropriate pool sizes based on application load
- Monitor connection pool metrics

### Connection Limits
- Set max_connections appropriately for your hardware
- Consider read replicas for read-heavy workloads
- Use connection multiplexing tools like PgBouncer

## Caching Strategies

### Application-Level Caching
- Redis, Memcached for frequently accessed data
- Implement cache invalidation strategies
- Consider cache-aside, write-through, or write-behind patterns

### Database-Level Caching
- Query result caching
- Buffer pool optimization
- Materialized views for complex aggregations

## Monitoring and Maintenance

### Key Metrics
- Query execution time
- Index hit ratio
- Connection pool utilization
- Lock contention
- Disk I/O patterns

### Regular Maintenance
- Update table statistics
- Rebuild fragmented indexes
- Analyze slow query logs
- Monitor storage growth
                    """,
                    "source": "DBA Team Knowledge Base",
                    "document_type": "technical_guide"
                },
                "metadata": {
                    "domain": "databases",
                    "category": "performance",
                    "document_length": "long",
                    "target_audience": "developers"
                },
                "importance": 0.9
            }
        ]
        
        for doc in documents:
            success = await self.manager.store_memory(doc)
            if success:
                memories_added += 1
                print(f"✅ Added document: {doc['content']['title']}")
        
        # 5. Entity Memories
        entities = [
            {
                "type": "entity",
                "content": {
                    "name": "John Smith",
                    "type": "person",
                    "description": "Senior Software Engineer specializing in distributed systems and cloud architecture",
                    "attributes": {
                        "role": "Senior Software Engineer",
                        "company": "TechCorp Inc.",
                        "specialties": ["distributed_systems", "cloud_architecture", "kubernetes", "go", "python"],
                        "experience_years": 8,
                        "location": "San Francisco, CA",
                        "email": "john.smith@techcorp.com"
                    },
                    "relationships": [
                        {"type": "works_with", "entity": "Sarah Johnson", "context": "Same team"},
                        {"type": "reports_to", "entity": "Mike Chen", "context": "Engineering Manager"}
                    ],
                    "context": "Key contributor to the microservices migration project"
                },
                "metadata": {
                    "entity_type": "person",
                    "department": "engineering",
                    "last_interaction": "2024-01-15"
                },
                "importance": 0.7
            },
            {
                "type": "entity",
                "content": {
                    "name": "TechCorp Internal API",
                    "type": "system",
                    "description": "Core REST API serving customer data and business logic across all applications",
                    "attributes": {
                        "technology": "Node.js + Express",
                        "database": "PostgreSQL",
                        "deployment": "Kubernetes cluster",
                        "endpoints": ["users", "orders", "products", "payments"],
                        "rate_limit": "1000 requests/minute",
                        "authentication": "JWT tokens",
                        "base_url": "https://api.techcorp.com/v1"
                    },
                    "relationships": [
                        {"type": "depends_on", "entity": "PostgreSQL Database", "context": "Data persistence"},
                        {"type": "integrates_with", "entity": "Payment Gateway", "context": "Payment processing"}
                    ],
                    "context": "Critical system for all customer-facing applications"
                },
                "metadata": {
                    "entity_type": "system",
                    "criticality": "high",
                    "maintained_by": "Backend Team"
                },
                "importance": 0.95
            }
        ]
        
        for entity in entities:
            success = await self.manager.store_memory(entity)
            if success:
                memories_added += 1
                print(f"✅ Added entity: {entity['content']['name']}")
        
        # 6. Reflection Memories
        reflections = [
            {
                "type": "reflection",
                "content": {
                    "observation": "The user frequently asks about performance optimization across different technologies",
                    "insight": "There's a consistent pattern of interest in scalability and efficiency. The user likely works on high-performance systems and values optimization techniques.",
                    "implications": "Future responses should include performance considerations and provide benchmarks or metrics when possible. Suggest profiling tools and monitoring strategies.",
                    "confidence": 0.85,
                    "context": "Analysis of recent conversation patterns"
                },
                "metadata": {
                    "reflection_type": "user_preference",
                    "pattern_observed": "performance_focus",
                    "conversation_count": 12
                },
                "importance": 0.8
            },
            {
                "type": "reflection",
                "content": {
                    "observation": "Code examples with error handling and edge cases are received more positively",
                    "insight": "The user appreciates robust, production-ready code samples rather than minimal examples. Including error handling, validation, and edge cases improves response quality.",
                    "implications": "Always include proper error handling in code examples. Add comments explaining edge cases and potential issues. Provide complete, runnable examples when possible.",
                    "confidence": 0.9,
                    "context": "Feedback analysis on code snippet quality"
                },
                "metadata": {
                    "reflection_type": "response_quality",
                    "pattern_observed": "preference_for_robust_code",
                    "feedback_sessions": 5
                },
                "importance": 0.85
            }
        ]
        
        for reflection in reflections:
            success = await self.manager.store_memory(reflection)
            if success:
                memories_added += 1
                print(f"✅ Added reflection: {reflection['content']['observation'][:50]}...")
        
        # Summary
        print(f"\n🎉 Successfully added {memories_added} test memories!")
        print("\n📋 Memory Types Added:")
        print(f"  • 3 Conversations (programming Q&A)")
        print(f"  • 3 Facts (technical principles)")  
        print(f"  • 3 Code Snippets (reusable solutions)")
        print(f"  • 2 Documents (architecture guides)")
        print(f"  • 2 Entities (people & systems)")
        print(f"  • 2 Reflections (behavioral insights)")
        print(f"\n💡 Total: {memories_added} memories ready for testing!")
        
        return memories_added


async def main():
    """Main function to populate memories."""
    try:
        # Use Qdrant config if available, fallback to default
        config_path = "config.qdrant.json" if Path("config.qdrant.json").exists() else None
        
        populator = MemoryPopulator(config_path)
        await populator.populate_memories()
        
        print("\n🚀 Memory population complete! You can now test the memory features.")
        print("\n🧪 Suggested test prompts:")
        print("  • 'What do you remember about binary search algorithms?'")
        print("  • 'Show me examples of React hooks usage'")
        print("  • 'What are the best practices for microservices?'")
        print("  • 'Tell me about John Smith and his expertise'")
        print("  • 'How should I optimize database performance?'")
        
    except Exception as e:
        print(f"❌ Error populating memories: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)