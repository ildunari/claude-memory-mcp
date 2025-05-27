"""
MCP server implementation for the memory system.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from loguru import logger
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server

from memory_mcp.mcp.tools import MemoryToolDefinitions
from memory_mcp.mcp.tool_models import (
    StoreMemoryInput, RetrieveMemoryInput, ListMemoriesInput,
    UpdateMemoryInput, DeleteMemoryInput, MemoryStatsInput
)
from memory_mcp.mcp.auto_capture_tools import (
    AutoCaptureControlInput, ContentTypeFilterInput, AutoCaptureStatsInput,
    create_auto_capture_tools
)
from memory_mcp.mcp.conversation_tools import (
    ProcessMessageInput, create_conversation_tools
)
from memory_mcp.domains.manager import MemoryDomainManager
from memory_mcp.auto_memory import ConversationAnalyzer


class MemoryMcpServer:
    """
    MCP server implementation for the memory system.
    
    This class sets up an MCP server that exposes memory-related tools
    and handles MCP protocol communication with Claude Desktop.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the Memory MCP Server.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.domain_manager = MemoryDomainManager(config)
        self.app = FastMCP("memory-mcp-server")
        self.tool_definitions = MemoryToolDefinitions(self.domain_manager)
        
        # Initialize conversation analyzer for auto-capture
        # Temporarily disable auto-capture to isolate the issue
        self.conversation_analyzer = None
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register memory-related tools with the MCP server."""
        
        # Store memory
        @self.app.tool(
            name="store_memory",
            description="Store new information in memory"
        )
        async def store_memory_handler(arguments: StoreMemoryInput) -> List[Dict[str, Any]]:
            """Handle store_memory tool requests."""
            try:
                memory_id = await self.domain_manager.store_memory(
                    memory_type=arguments.type,
                    content=arguments.content,
                    importance=arguments.importance,
                    metadata=arguments.metadata,
                    context=arguments.context
                )
                
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "memory_id": memory_id
                    })
                }]
            except Exception as e:
                logger.error(f"Error in store_memory: {str(e)}")
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": str(e)
                    }),
                    "is_error": True
                }]
        
        # Retrieve memory
        @self.app.tool(
            name="retrieve_memory",
            description="Retrieve relevant memories based on query"
        )
        async def retrieve_memory_handler(arguments: RetrieveMemoryInput) -> List[Dict[str, Any]]:
            """Handle retrieve_memory tool requests."""
            try:
                query = arguments.query
                limit = arguments.limit
                memory_types = arguments.types
                min_similarity = arguments.min_similarity
                include_metadata = arguments.include_metadata
                
                memories = await self.domain_manager.retrieve_memories(
                    query=query,
                    limit=limit,
                    memory_types=memory_types,
                    min_similarity=min_similarity,
                    include_metadata=include_metadata
                )
                
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "memories": memories
                    })
                }]
            except Exception as e:
                logger.error(f"Error in retrieve_memory: {str(e)}")
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": str(e)
                    }),
                    "is_error": True
                }]
        
        # List memories
        @self.app.tool(
            name="list_memories",
            description="List available memories with filtering options"
        )
        async def list_memories_handler(arguments: ListMemoriesInput) -> List[Dict[str, Any]]:
            """Handle list_memories tool requests."""
            try:
                memory_types = arguments.types
                limit = arguments.limit
                offset = 0  # Not in the input model, using default
                tier = None  # Not in the input model, using default
                include_content = False  # Not in the input model, using default
                
                memories = await self.domain_manager.list_memories(
                    memory_types=memory_types,
                    limit=limit,
                    offset=offset,
                    tier=tier,
                    include_content=include_content
                )
                
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "memories": memories
                    })
                }]
            except Exception as e:
                logger.error(f"Error in list_memories: {str(e)}")
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": str(e)
                    }),
                    "is_error": True
                }]
        
        # Update memory
        @self.app.tool(
            name="update_memory",
            description="Update existing memory entries"
        )
        async def update_memory_handler(arguments: UpdateMemoryInput) -> List[Dict[str, Any]]:
            """Handle update_memory tool requests."""
            try:
                memory_id = arguments.memory_id
                updates = arguments.updates
                
                success = await self.domain_manager.update_memory(
                    memory_id=memory_id,
                    updates=updates
                )
                
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": success
                    })
                }]
            except Exception as e:
                logger.error(f"Error in update_memory: {str(e)}")
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": str(e)
                    }),
                    "is_error": True
                }]
        
        # Delete memory
        @self.app.tool(
            name="delete_memory",
            description="Remove specific memories"
        )
        async def delete_memory_handler(arguments: DeleteMemoryInput) -> List[Dict[str, Any]]:
            """Handle delete_memory tool requests."""
            try:
                memory_ids = arguments.memory_ids
                
                success = await self.domain_manager.delete_memories(
                    memory_ids=memory_ids
                )
                
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": success
                    })
                }]
            except Exception as e:
                logger.error(f"Error in delete_memory: {str(e)}")
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": str(e)
                    }),
                    "is_error": True
                }]
        
        # Memory stats
        @self.app.tool(
            name="memory_stats",
            description="Get statistics about the memory store"
        )
        async def memory_stats_handler(arguments: MemoryStatsInput) -> List[Dict[str, Any]]:
            """Handle memory_stats tool requests."""
            try:
                stats = await self.domain_manager.get_memory_stats()
                
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "stats": stats
                    })
                }]
            except Exception as e:
                logger.error(f"Error in memory_stats: {str(e)}")
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": str(e)
                    }),
                    "is_error": True
                }]
    
    async def _auto_store_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        importance: float = 0.5,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Callback for auto-capture system to store memories.
        
        Args:
            memory_type: Type of memory
            content: Memory content
            importance: Importance score
            context: Optional context
            
        Returns:
            Memory ID
        """
        return await self.domain_manager.store_memory(
            memory_type=memory_type,
            content=content,
            importance=importance,
            context=context
        )
    
    def _register_auto_capture_tools(self) -> None:
        """Register auto-capture control tools."""
        auto_capture_tools = create_auto_capture_tools(self.conversation_analyzer)
        
        # Auto-capture control
        @self.app.tool(
            name="auto_capture_control",
            description=auto_capture_tools["auto_capture_control"]["description"]
        )
        async def auto_capture_control_handler(arguments: AutoCaptureControlInput):
            return await auto_capture_tools["auto_capture_control"]["handler"](arguments)
        
        # Content type filter
        @self.app.tool(
            name="content_type_filter",
            description=auto_capture_tools["content_type_filter"]["description"]
        )
        async def content_type_filter_handler(arguments: ContentTypeFilterInput):
            return await auto_capture_tools["content_type_filter"]["handler"](arguments)
        
        # Auto-capture stats
        @self.app.tool(
            name="auto_capture_stats",
            description=auto_capture_tools["auto_capture_stats"]["description"]
        )
        async def auto_capture_stats_handler(arguments: AutoCaptureStatsInput):
            return await auto_capture_tools["auto_capture_stats"]["handler"](arguments)
    
    def _register_conversation_tools(self) -> None:
        """Register conversation processing tools."""
        conversation_tools = create_conversation_tools(self.conversation_analyzer)
        
        # Process message tool
        @self.app.tool(
            name="process_message",
            description=conversation_tools["process_message"]["description"]
        )
        async def process_message_handler(arguments: ProcessMessageInput):
            return await conversation_tools["process_message"]["handler"](arguments)
    
    def start(self) -> None:
        """Start the MCP server."""
        # Initialize the memory domain manager
        asyncio.run(self.domain_manager.initialize())
        
        logger.info("Starting Memory MCP Server using stdio transport")
        
        # Start the server using stdio transport
        self.app.run(transport='stdio')
