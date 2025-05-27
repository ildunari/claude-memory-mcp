#!/usr/bin/env python3
"""
Simple MCP protocol test to isolate the issue.
"""

import asyncio
import json
import subprocess
import time
import sys

async def test_simple_mcp():
    """Test our MCP server with the simplest possible setup."""
    
    print("🧪 Simple MCP Protocol Test")
    print("=" * 40)
    
    # Start our server
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "memory_mcp",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    print(f"✓ Server started (PID: {proc.pid})")
    
    try:
        # Step 1: Initialize
        print("1. Sending initialize...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        
        start = time.time()
        proc.stdin.write(json.dumps(init_request).encode() + b'\n')
        await proc.stdin.drain()
        
        # Wait for response
        try:
            response_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=10.0)
            init_time = time.time() - start
            
            if response_bytes:
                response = json.loads(response_bytes.decode().strip())
                print(f"   ✅ Initialize OK ({init_time:.2f}s)")
                print(f"   📝 Response: {response.get('result', {}).get('serverInfo', {}).get('name', 'unknown')}")
            else:
                print("   ❌ No initialize response")
                return
        except asyncio.TimeoutError:
            print("   ⏰ Initialize timeout")
            return
        
        # Step 2: Initialized notification
        print("2. Sending initialized notification...")
        init_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        proc.stdin.write(json.dumps(init_notif).encode() + b'\n')
        await proc.stdin.drain()
        
        # Step 3: List tools
        print("3. Sending tools/list...")
        tools_request = {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        start = time.time()
        proc.stdin.write(json.dumps(tools_request).encode() + b'\n')
        await proc.stdin.drain()
        
        # Wait for tools response
        try:
            tools_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=10.0)
            tools_time = time.time() - start
            
            if tools_bytes:
                tools_response = json.loads(tools_bytes.decode().strip())
                print(f"   ✅ Tools list OK ({tools_time:.2f}s)")
                tools = tools_response.get('result', {}).get('tools', [])
                print(f"   🔧 Tools: {[t.get('name') for t in tools]}")
                
                # Test a tool call
                print("4. Testing tool call...")
                tool_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "memory_stats",
                        "arguments": {}
                    }
                }
                
                start = time.time()
                proc.stdin.write(json.dumps(tool_request).encode() + b'\n')
                await proc.stdin.drain()
                
                tool_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=10.0)
                call_time = time.time() - start
                
                if tool_bytes:
                    tool_response = json.loads(tool_bytes.decode().strip())
                    print(f"   ✅ Tool call OK ({call_time:.2f}s)")
                    
                    content = tool_response.get('result', {}).get('content', [])
                    if content:
                        result = json.loads(content[0].get('text', '{}'))
                        print(f"   📊 Result: {result}")
                else:
                    print("   ❌ No tool call response")
                    
            else:
                print("   ❌ No tools response")
                
        except asyncio.TimeoutError:
            print("   ⏰ Tools timeout")
            
        # Check stderr for errors
        print("\n📝 Server stderr:")
        stderr_data = proc.stderr.read_nowait() if proc.stderr else b''
        if stderr_data:
            print(stderr_data.decode())
        else:
            print("   (no stderr output)")
            
    finally:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(test_simple_mcp())