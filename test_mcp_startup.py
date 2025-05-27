#!/usr/bin/env python3
"""
Test script to verify MCP server startup and tool discovery
"""

import json
import sys
import subprocess
import asyncio
import os
from pathlib import Path

async def test_mcp_server():
    """Test that the MCP server can start and list tools"""
    
    # Get the project directory
    project_dir = Path(__file__).parent
    script_path = project_dir / "start_memory_server.sh"
    
    print("Testing Memory MCP Server startup...")
    
    try:
        # Start the server process
        proc = await asyncio.create_subprocess_exec(
            "python3", "-m", "memory_mcp",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(project_dir),
            env={**dict(os.environ), "PYTHONPATH": str(project_dir)}
        )
        
        # Send MCP initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send the request
        request_data = json.dumps(init_request) + "\n"
        proc.stdin.write(request_data.encode())
        await proc.stdin.drain()
        
        # Read response with timeout
        try:
            response_data = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
            response = json.loads(response_data.decode().strip())
            
            print(f"✓ Server responded to initialization: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
            
            # Send tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            request_data = json.dumps(tools_request) + "\n"
            proc.stdin.write(request_data.encode())
            await proc.stdin.drain()
            
            # Read tools response
            response_data = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
            tools_response = json.loads(response_data.decode().strip())
            
            tools = tools_response.get('result', {}).get('tools', [])
            print(f"✓ Server discovered {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            
            return True
            
        except asyncio.TimeoutError:
            print("✗ Server did not respond within timeout")
            return False
            
        finally:
            # Clean up
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                proc.kill()
                
    except Exception as e:
        print(f"✗ Error testing server: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)