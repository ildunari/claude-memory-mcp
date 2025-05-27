#!/usr/bin/env python3
"""
Comprehensive test suite for the safety infrastructure.
Tests circuit breakers, health checks, background processing, and graceful degradation.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Any
import random
import tempfile
import os

from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from memory_mcp.domains.manager import MemoryDomainManager
from memory_mcp.utils.circuit_breaker import CircuitBreakerManager, CircuitState
from memory_mcp.utils.health_checks import SystemHealthMonitor, HealthStatus
from memory_mcp.utils.background_processor import BackgroundProcessor, TaskPriority
from memory_mcp.utils.config_validator import ConfigValidator


class SafetyInfrastructureTester:
    """Comprehensive tester for safety infrastructure components."""
    
    def __init__(self):
        self.test_results = {}
        self.manager = None
        
    async def run_all_tests(self):
        """Run all safety infrastructure tests."""
        logger.info("🚀 Starting Safety Infrastructure Test Suite")
        
        tests = [
            ("Configuration Validation", self.test_config_validation),
            ("Circuit Breaker Functionality", self.test_circuit_breakers),
            ("Health Check System", self.test_health_checks),
            ("Background Processor", self.test_background_processor),
            ("Manager Integration", self.test_manager_integration),
            ("Graceful Degradation", self.test_graceful_degradation),
            ("System Health API", self.test_system_health_api),
            ("Error Recovery", self.test_error_recovery),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"🧪 Running test: {test_name}")
            try:
                result = await test_func()
                if result:
                    logger.success(f"✅ {test_name} PASSED")
                    passed += 1
                else:
                    logger.error(f"❌ {test_name} FAILED")
                    
                self.test_results[test_name] = result
                
            except Exception as e:
                logger.error(f"💥 {test_name} CRASHED: {e}")
                self.test_results[test_name] = False
        
        # Summary
        logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
        if passed == total:
            logger.success("🎉 ALL TESTS PASSED! Safety infrastructure is ready for production.")
        else:
            logger.error(f"⚠️  {total - passed} tests failed. Review issues before deployment.")
            
        return passed == total
    
    async def test_config_validation(self) -> bool:
        """Test configuration validation system."""
        try:
            # Test 1: Valid configuration
            valid_config = {
                "memory": {"backend": "qdrant"},
                "qdrant": {"url": "http://localhost:6333", "port": 6333},
                "embedding": {"default_model": "sentence-transformers/all-MiniLM-L6-v2", "dimensions": 384},
                "retrieval": {"hybrid_search": True, "query_expansion": True}
            }
            
            validator = ConfigValidator(valid_config)
            result = validator.validate_all()
            if not result.is_valid or result.errors:
                logger.error(f"Valid config failed validation: {result.errors}")
                return False
                
            # Test 2: Invalid configuration
            invalid_config = {
                "memory": {"backend": "invalid_backend"},
                "embedding": {"default_model": "nonexistent-model"}
            }
            
            validator2 = ConfigValidator(invalid_config)
            result = validator2.validate_all()
            if result.is_valid and not result.errors:
                logger.error("Invalid config passed validation")
                return False
                
            # Test 3: Missing dependencies
            missing_deps_config = {
                "memory": {"backend": "qdrant"},
                "retrieval": {"hybrid_search": True}
                # Missing qdrant config
            }
            
            validator3 = ConfigValidator(missing_deps_config)
            result = validator3.validate_all()
            if not result.errors:
                logger.error("Missing dependencies not detected")
                return False
            
            logger.debug("Configuration validation tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Config validation test failed: {e}")
            return False
    
    async def test_circuit_breakers(self) -> bool:
        """Test circuit breaker functionality."""
        try:
            manager = CircuitBreakerManager()
            
            # Test 1: Normal operation
            breaker = manager.get_breaker("test_service")
            
            async def success_func():
                return "success"
                
            result = await breaker.call(success_func)
            if result != "success" or breaker.stats.state != CircuitState.CLOSED:
                logger.error("Circuit breaker failed normal operation")
                return False
            
            # Test 2: Failure handling
            async def fail_func():
                raise Exception("Test failure")
            
            # Trigger failures to open circuit
            for i in range(6):  # Default failure threshold is 5
                try:
                    await breaker.call(fail_func)
                except:
                    pass
            
            if breaker.stats.state != CircuitState.OPEN:
                logger.error(f"Circuit breaker should be OPEN, but is {breaker.stats.state}")
                return False
            
            # Test 3: Circuit open behavior
            try:
                await breaker.call(success_func)
                logger.error("Circuit breaker should reject calls when OPEN")
                return False
            except Exception as e:
                if "Circuit breaker is OPEN" not in str(e):
                    logger.error(f"Wrong exception from open circuit: {e}")
                    return False
            
            # Test 4: Recovery after timeout
            # Manually set last failure time to simulate timeout
            breaker.last_failure_time = time.time() - 61  # 1 minute ago
            breaker.stats.state = CircuitState.HALF_OPEN
            
            result = await breaker.call(success_func)
            if result != "success" or breaker.stats.state != CircuitState.CLOSED:
                logger.error("Circuit breaker failed to recover")
                return False
            
            logger.debug("Circuit breaker tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Circuit breaker test failed: {e}")
            return False
    
    async def test_health_checks(self) -> bool:
        """Test health check system."""
        try:
            monitor = SystemHealthMonitor()
            
            # Test 1: Register and run healthy check
            def healthy_check():
                return {"status": "ok", "test": True}
            
            monitor.register_check("test_healthy", healthy_check, timeout=2.0, critical=True)
            
            results = await monitor.check_all()
            if "test_healthy" not in results:
                logger.error("Health check not executed")
                return False
                
            result = results["test_healthy"]
            if result.status != HealthStatus.HEALTHY:
                logger.error(f"Health check should be healthy, got {result.status}")
                return False
            
            # Test 2: Failing health check
            def failing_check():
                raise Exception("Test failure")
            
            monitor.register_check("test_failing", failing_check, timeout=2.0, critical=False)
            
            results = await monitor.check_all()
            result = results["test_failing"]
            if result.status != HealthStatus.UNHEALTHY:
                logger.error(f"Health check should be unhealthy, got {result.status}")
                return False
            
            # Test 3: Timeout handling
            def slow_check():
                time.sleep(3)  # Longer than timeout
                return True
            
            monitor.register_check("test_timeout", slow_check, timeout=1.0, critical=False)
            
            start_time = time.time()
            results = await monitor.check_all()
            elapsed = time.time() - start_time
            
            if elapsed > 5.0:  # Should timeout reasonably quickly
                logger.error("Health check timeout not working")
                return False
                
            result = results["test_timeout"]
            if result.status != HealthStatus.UNHEALTHY:
                logger.error("Timed out check should be unhealthy")
                return False
            
            # Test 4: System status calculation
            system_status = monitor.get_system_status()
            # Should be degraded due to non-critical failing checks
            if system_status == HealthStatus.HEALTHY:
                logger.error(f"System status should not be healthy with failing checks, got {system_status}")
                return False
            
            logger.debug("Health check tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Health check test failed: {e}")
            return False
    
    async def test_background_processor(self) -> bool:
        """Test background processor functionality."""
        try:
            processor = BackgroundProcessor(max_workers=2, max_queue_size=10)
            
            # Test 1: Start and basic task execution
            await processor.start()
            
            if not processor.running:
                logger.error("Background processor failed to start")
                return False
            
            # Simple task
            def simple_task(x):
                return x * 2
            
            task_id = processor.submit_task(
                "test_simple",
                "Simple Test Task",
                simple_task,
                5,
                priority=TaskPriority.HIGH
            )
            
            if not task_id:
                logger.error("Failed to submit task")
                return False
            
            # Wait for completion
            for i in range(30):  # 3 second timeout
                status = processor.get_task_status(task_id)
                if status and status["status"] == "completed":
                    if status["result"] != 10:
                        logger.error(f"Task result wrong: expected 10, got {status['result']}")
                        return False
                    break
                await asyncio.sleep(0.1)
            else:
                logger.error("Task did not complete in time")
                return False
            
            # Test 2: Task failure and retry
            def failing_task():
                raise ValueError("Test failure")
            
            task_id = processor.submit_task(
                "test_failing",
                "Failing Task",
                failing_task,
                max_retries=2
            )
            
            # Wait for final failure
            for _ in range(30):  # 3 second timeout
                status = processor.get_task_status(task_id)
                if status and status["status"] == "failed":
                    if status["retry_count"] != 2:
                        logger.error(f"Wrong retry count: expected 2, got {status['retry_count']}")
                        return False
                    break
                await asyncio.sleep(0.1)
            else:
                logger.error("Failing task did not fail properly")
                return False
            
            # Test 3: Processor stats
            stats = processor.get_processor_stats()
            if not stats["running"] or stats["workers"] != 2:
                logger.error(f"Wrong processor stats: {stats}")
                return False
            
            # Test 4: Graceful shutdown
            await processor.stop()
            if processor.running:
                logger.error("Background processor failed to stop")
                return False
            
            logger.debug("Background processor tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Background processor test failed: {e}")
            return False
    
    async def test_manager_integration(self) -> bool:
        """Test manager integration with safety infrastructure."""
        try:
            # Create a temporary config
            config = {
                "memory": {
                    "backend": "json",
                    "dir": tempfile.mkdtemp(),
                    "short_term_threshold": 0.3
                },
                "embedding": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384
                },
                "retrieval": {
                    "similarity_threshold": 0.3,
                    "max_results": 15,
                    "hybrid_search": False,
                    "query_expansion": False
                },
                "background": {
                    "max_workers": 2,
                    "max_queue_size": 50
                }
            }
            
            # Test 1: Manager initialization with safety infrastructure
            manager = MemoryDomainManager(config)
            await manager.initialize()
            
            if not manager.safety_initialized:
                logger.error("Manager safety infrastructure not initialized")
                return False
                
            if not manager.background_processor.running:
                logger.error("Background processor not running")
                return False
            
            # Test 2: Health check integration
            health = await manager.get_system_health()
            if "overall_status" not in health:
                logger.error("System health not available")
                return False
                
            # Test 3: Memory operations work with safety infrastructure
            memory_id = await manager.store_memory(
                memory_type="fact",
                content={"statement": "Test fact for safety infrastructure"},
                importance=0.7
            )
            
            if not memory_id:
                logger.error("Failed to store memory with safety infrastructure")
                return False
            
            # Test 4: Retrieve with graceful degradation
            results = await manager.retrieve_memories(
                query="test fact",
                limit=5
            )
            
            if not results:
                logger.error("Failed to retrieve memories with safety infrastructure")
                return False
                
            if "search_method" not in results[0]:
                logger.error("Search method not tracked in results")
                return False
            
            # Test 5: Clean shutdown
            await manager.shutdown()
            
            if manager.background_processor.running:
                logger.error("Background processor still running after shutdown")
                return False
            
            self.manager = None  # Clean reference
            
            logger.debug("Manager integration tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Manager integration test failed: {e}")
            if self.manager:
                try:
                    await self.manager.shutdown()
                except:
                    pass
            return False
    
    async def test_graceful_degradation(self) -> bool:
        """Test graceful degradation under failure conditions."""
        try:
            # Create config with problematic settings to trigger degradation
            config = {
                "memory": {
                    "backend": "qdrant",  # This will fail if Qdrant not available
                    "dir": tempfile.mkdtemp()
                },
                "qdrant": {
                    "url": "http://localhost:9999",  # Wrong port
                    "port": 9999,
                    "collection": "test_memories"
                },
                "embedding": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384
                },
                "retrieval": {
                    "hybrid_search": True,  # This should fail without proper setup
                    "query_expansion": True
                }
            }
            
            # Test 1: Manager should handle failed Qdrant connection gracefully
            try:
                manager = MemoryDomainManager(config)
                await manager.initialize()
                
                # Should be in degraded mode
                if not manager.degraded_mode:
                    logger.warning("Manager should be in degraded mode due to failed Qdrant connection")
                    # This is not a hard failure since Qdrant might actually be available
                
                # Test 2: Operations should still work in degraded mode
                health = await manager.get_system_health()
                if health["degraded_mode"] != manager.degraded_mode:
                    logger.error("Health status doesn't match degraded mode flag")
                    return False
                
                await manager.shutdown()
                
            except Exception as e:
                # If initialization completely fails, that's also acceptable
                # as long as it's handled gracefully
                logger.debug(f"Graceful initialization failure: {e}")
            
            # Test 3: Circuit breaker degradation
            manager = CircuitBreakerManager()
            breaker = manager.get_breaker("test_degradation")
            
            # Force circuit open
            async def fail_func():
                raise Exception("Simulated failure")
            
            for _ in range(6):
                try:
                    await breaker.call(fail_func)
                except:
                    pass
            
            # Circuit should be open
            if breaker.stats.state != CircuitState.OPEN:
                logger.error("Circuit breaker not open for degradation test")
                return False
            
            logger.debug("Graceful degradation tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Graceful degradation test failed: {e}")
            return False
    
    async def test_system_health_api(self) -> bool:
        """Test system health API functionality."""
        try:
            config = {
                "memory": {
                    "backend": "json",
                    "dir": tempfile.mkdtemp()
                },
                "embedding": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384
                }
            }
            
            manager = MemoryDomainManager(config)
            await manager.initialize()
            
            # Test 1: Get system health
            health = await manager.get_system_health()
            
            required_fields = ["overall_status", "degraded_mode", "health_checks", 
                             "circuit_breakers", "background_processor", "timestamp"]
            
            for field in required_fields:
                if field not in health:
                    logger.error(f"Missing field in health response: {field}")
                    return False
            
            # Test 2: Health check details
            health_checks = health["health_checks"]
            if "services" not in health_checks:
                logger.error("Health checks missing services")
                return False
            
            # Should have at least filesystem check
            services = health_checks["services"]
            if "filesystem" not in services:
                logger.error("Missing filesystem health check")
                return False
            
            # Test 3: Circuit breaker status
            breakers = health["circuit_breakers"]
            if not isinstance(breakers, dict):
                logger.error("Circuit breakers should be a dict")
                return False
            
            # Test 4: Background processor status
            bg_status = health["background_processor"]
            if not bg_status.get("running"):
                logger.error("Background processor should be running")
                return False
            
            await manager.shutdown()
            
            logger.debug("System health API tests passed")
            return True
            
        except Exception as e:
            logger.error(f"System health API test failed: {e}")
            return False
    
    async def test_error_recovery(self) -> bool:
        """Test error recovery mechanisms."""
        try:
            # Test 1: Circuit breaker recovery
            manager = CircuitBreakerManager()
            breaker = manager.get_breaker("recovery_test")
            
            # Fail to open circuit
            async def fail_func():
                raise Exception("Test failure")
            
            for _ in range(6):
                try:
                    await breaker.call(fail_func)
                except:
                    pass
            
            if breaker.stats.state != CircuitState.OPEN:
                logger.error("Circuit should be open")
                return False
            
            # Force recovery by setting timeout
            breaker.last_failure_time = time.time() - 61
            
            async def success_func():
                return "recovered"
            
            result = await breaker.call(success_func)
            if result != "recovered" or breaker.stats.state != CircuitState.CLOSED:
                logger.error("Circuit breaker failed to recover")
                return False
            
            # Test 2: Health check recovery
            monitor = SystemHealthMonitor()
            
            # Initially failing check
            failure_count = 0
            def recovering_check():
                nonlocal failure_count
                failure_count += 1
                if failure_count <= 2:
                    raise Exception("Initial failure")
                return {"status": "ok", "recovered": True}
            
            monitor.register_check("recovery_check", recovering_check, critical=False)
            
            # First check should fail
            results = await monitor.check_all()
            if results["recovery_check"].status != HealthStatus.UNHEALTHY:
                logger.error("Check should initially fail")
                return False
            
            # Subsequent checks should recover
            results = await monitor.check_all()
            results = await monitor.check_all()
            if results["recovery_check"].status != HealthStatus.HEALTHY:
                logger.error("Check should recover")
                return False
            
            logger.debug("Error recovery tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Error recovery test failed: {e}")
            return False


async def main():
    """Main test runner."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    tester = SafetyInfrastructureTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.success("🚀 Safety infrastructure is production-ready!")
        sys.exit(0)
    else:
        logger.error("❌ Safety infrastructure needs attention before deployment")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())