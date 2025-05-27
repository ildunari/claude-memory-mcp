#!/usr/bin/env python3
"""
Absolutely minimal MCP server for the enhanced memory system
"""

import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

def create_minimal_server():
    """Create minimal enhanced memory server"""
    app = Server("enhanced-memory-minimal")
    
    @app.list_tools()
    async def list_tools():
        return [
            types.Tool(
                name="store_memory",
                description="Store new information in memory",
                inputSchema={"type": "object", "properties": {}}
            ),
            types.Tool(
                name="retrieve_memory",
                description="Retrieve relevant memories",
                inputSchema={"type": "object", "properties": {}}
            )
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        return [types.TextContent(type="text", text=f"Enhanced tool {name} called with {arguments}")]
    
    return app

async def main():
    app = create_minimal_server()
    
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())