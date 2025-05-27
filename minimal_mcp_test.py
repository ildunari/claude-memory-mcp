#!/usr/bin/env python3
"""
Minimal MCP server test to isolate the timing issue
"""

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Create a minimal MCP server that should respond quickly
app = Server("minimal-test-server")

@app.list_tools()
async def list_tools():
    """List available tools."""
    return [
        types.Tool(
            name="test_tool",
            description="A simple test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name == "test_tool":
        return [types.TextContent(type="text", text=f"Echo: {arguments.get('message', 'No message')}")]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the minimal server"""
    print("Starting minimal MCP server...", file=sys.stderr)
    
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())