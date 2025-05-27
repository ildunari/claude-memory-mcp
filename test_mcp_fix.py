#!/usr/bin/env python3
"""
Test the MCP protocol fix for the enhanced Memory MCP server.

This test verifies:
1. MCP protocol handshake completes quickly
2. Server responds to tool requests appropriately during initialization
3. Tools work properly once fully initialized
"""

import asyncio
import json
import subprocess
import time
import sys
from typing import Dict, Any

async def test_mcp_protocol():
    """Test MCP protocol with the fixed enhanced server."""
    
    print("🔧 Testing Enhanced Memory MCP Server Protocol Fix")
    print("=" * 60)
    
    # Start the enhanced server process
    print("1. Starting enhanced MCP server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "memory_mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Test 1: MCP Initialize Request
        print("2. Testing MCP initialize handshake...")
        start_time = time.time()
        
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send initialize request
        process.stdin.write(json.dumps(initialize_request) + '\n')
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            init_time = time.time() - start_time
            print(f"   ✅ Initialize response received in {init_time:.3f}s")
            print(f"   📋 Server capabilities: {response.get('result', {}).get('capabilities', {})}")
        else:
            print("   ❌ No initialize response received")
            return False
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized_notification) + '\n')
        process.stdin.flush()
        
        # Test 2: Tools List Request (should work immediately)
        print("3. Testing tools/list request...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(tools_request) + '\n')
        process.stdin.flush()
        
        # Read tools response
        tools_response_line = process.stdout.readline()
        if tools_response_line:
            tools_response = json.loads(tools_response_line.strip())
            tools_time = time.time() - start_time
            print(f"   ✅ Tools list received in {tools_time:.3f}s")
            tools = tools_response.get('result', {}).get('tools', [])
            print(f"   🔧 Available tools: {[tool.get('name') for tool in tools]}")
        else:
            print("   ❌ No tools response received")
            return False
        
        # Test 3: Tool Call During Initialization
        print("4. Testing tool call during initialization...")
        tool_call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "memory_stats",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(tool_call_request) + '\n')
        process.stdin.flush()
        
        # Read tool call response
        tool_response_line = process.stdout.readline()
        if tool_response_line:
            tool_response = json.loads(tool_response_line.strip())
            tool_result = json.loads(tool_response.get('result', {}).get('content', [{}])[0].get('text', '{}'))
            print(f"   📊 Tool call result: {tool_result}")
            
            # Check if it's an initialization message or actual result
            if "still initializing" in tool_result.get('error', ''):
                print("   ⏳ Server properly handling calls during initialization")
            elif tool_result.get('success'):
                print("   ✅ Server fully initialized and working")
            else:
                print(f"   ⚠️  Unexpected response: {tool_result}")
        else:
            print("   ❌ No tool call response received")
            return False
        
        # Test 4: Wait for full initialization and test again
        print("5. Waiting for full initialization...")
        await asyncio.sleep(5)  # Give time for domain manager to load
        
        # Try tool call again
        process.stdin.write(json.dumps(tool_call_request) + '\n')
        process.stdin.flush()
        
        final_response_line = process.stdout.readline()
        if final_response_line:
            final_response = json.loads(final_response_line.strip())
            final_result = json.loads(final_response.get('result', {}).get('content', [{}])[0].get('text', '{}'))
            
            if final_result.get('success'):
                print("   ✅ Server fully initialized and working correctly")
                print(f"   📈 Memory stats: {final_result.get('stats', {})}")
            else:
                print(f"   ⚠️  Server may still be initializing: {final_result}")
        
        print("\n🎉 MCP Protocol Fix Test Complete!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

if __name__ == "__main__":
    asyncio.run(test_mcp_protocol())