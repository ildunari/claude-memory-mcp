#!/usr/bin/env python3
"""
Test MCP protocol communication to debug the timeout issue
"""

import asyncio
import json
import sys
import time
import os
from pathlib import Path

async def test_mcp_communication():
    """Test MCP protocol communication with timeout"""
    
    project_dir = Path(__file__).parent
    
    print("🔍 Testing Enhanced Memory MCP Server protocol communication...")
    
    try:
        # Start the enhanced server
        proc = await asyncio.create_subprocess_exec(
            "python3", "-m", "memory_mcp",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(project_dir),
            env={**dict(os.environ), "PYTHONPATH": str(project_dir)}
        )
        
        print(f"✓ Server process started (PID: {proc.pid})")
        
        # Test 1: Send initialization request
        print("\n📤 Sending MCP initialization request...")
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
        
        request_line = json.dumps(init_request) + "\n"
        start_time = time.time()
        
        proc.stdin.write(request_line.encode())
        await proc.stdin.drain()
        
        # Wait for response with timeout
        try:
            response_data = await asyncio.wait_for(proc.stdout.readline(), timeout=30.0)
            elapsed = time.time() - start_time
            
            if response_data:
                response = json.loads(response_data.decode().strip())
                print(f"✅ Initialization response received in {elapsed:.2f}s")
                print(f"   Server: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
                
                # Send initialization complete notification (required by MCP protocol)
                print("📤 Sending initialized notification...")
                init_complete = {
                    "jsonrpc": "2.0",
                    "method": "initialized",
                    "params": {}
                }
                
                request_line = json.dumps(init_complete) + "\n"
                proc.stdin.write(request_line.encode())
                await proc.stdin.drain()
                
                # Wait a moment for the server to process initialization complete
                await asyncio.sleep(0.1)
                
                # Test 2: Send tools/list request
                print("\n📤 Sending tools/list request...")
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                request_line = json.dumps(tools_request) + "\n"
                start_time = time.time()
                
                proc.stdin.write(request_line.encode())
                await proc.stdin.drain()
                
                # Wait for tools response
                response_data = await asyncio.wait_for(proc.stdout.readline(), timeout=30.0)
                elapsed = time.time() - start_time
                
                if response_data:
                    tools_response = json.loads(response_data.decode().strip())
                    print(f"✅ Tools list received in {elapsed:.2f}s")
                    
                    tools = tools_response.get('result', {}).get('tools', [])
                    print(f"   Tools discovered: {len(tools)}")
                    for tool in tools[:5]:  # Show first 5 tools
                        print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                    if len(tools) > 5:
                        print(f"   ... and {len(tools) - 5} more tools")
                    
                    print(f"\n🎉 MCP protocol test SUCCESSFUL!")
                    print(f"   Total communication time: {time.time() - start_time:.2f}s")
                    return True
                else:
                    print("❌ No tools response received")
                    return False
            else:
                print(f"❌ No initialization response received after {elapsed:.2f}s")
                return False
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⏰ Timeout after {elapsed:.2f}s - server not responding to MCP requests")
            
            # Check if there's stderr output
            try:
                stderr_data = await asyncio.wait_for(proc.stderr.read(1024), timeout=1.0)
                if stderr_data:
                    print(f"📝 Server stderr output:")
                    print(stderr_data.decode().strip())
            except asyncio.TimeoutError:
                pass
                
            return False
            
    except Exception as e:
        print(f"❌ Error during MCP test: {e}")
        return False
        
    finally:
        # Clean up
        try:
            if 'proc' in locals() and proc:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    proc.kill()
        except:
            pass


async def compare_with_standard_server():
    """Test the standard MCP memory server for comparison"""
    
    print("\n🔄 Testing standard MCP memory server for comparison...")
    
    try:
        # Start standard server
        proc = await asyncio.create_subprocess_exec(
            "npx", "@modelcontextprotocol/server-memory",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        print(f"✓ Standard server process started (PID: {proc.pid})")
        
        # Send same initialization request
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
        
        request_line = json.dumps(init_request) + "\n"
        start_time = time.time()
        
        proc.stdin.write(request_line.encode())
        await proc.stdin.drain()
        
        # Wait for response
        try:
            response_data = await asyncio.wait_for(proc.stdout.readline(), timeout=10.0)
            elapsed = time.time() - start_time
            
            if response_data:
                response = json.loads(response_data.decode().strip())
                print(f"✅ Standard server responded in {elapsed:.2f}s")
                print(f"   Server: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
                return True
            else:
                print(f"❌ Standard server no response after {elapsed:.2f}s")
                return False
                
        except asyncio.TimeoutError:
            print(f"⏰ Standard server timeout after 10s")
            return False
            
    except Exception as e:
        print(f"❌ Error testing standard server: {e}")
        return False
        
    finally:
        try:
            if 'proc' in locals() and proc:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
        except:
            pass


async def main():
    """Run the comprehensive MCP protocol test"""
    print("🧪 MCP Protocol Communication Debug Tool")
    print("=" * 50)
    
    # Test enhanced server
    enhanced_success = await test_mcp_communication()
    
    # Test standard server for comparison
    standard_success = await compare_with_standard_server()
    
    print(f"\n📊 RESULTS:")
    print(f"   Enhanced Server: {'✅ Working' if enhanced_success else '❌ Failed'}")
    print(f"   Standard Server: {'✅ Working' if standard_success else '❌ Failed'}")
    
    if not enhanced_success and standard_success:
        print(f"\n🔧 DIAGNOSIS: Enhanced server has MCP protocol communication issue")
        print(f"   The problem is NOT in MetaMCP - it's in our server's MCP handling")
    elif enhanced_success:
        print(f"\n🎉 SUCCESS: Enhanced server MCP protocol is working correctly")
        print(f"   The issue may be in MetaMCP timeout configuration or environment")
    else:
        print(f"\n⚠️  Both servers failed - may be environment issue")


if __name__ == "__main__":
    asyncio.run(main())