"""
MCP tools for controlling the auto-capture system.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from memory_mcp.auto_memory import ContentType


class AutoCaptureControlInput(BaseModel):
    """Input for auto_capture_control tool."""
    enabled: bool = Field(description="Whether to enable or disable auto-capture")


class ContentTypeFilterInput(BaseModel):
    """Input for content_type_filter tool."""
    content_type: str = Field(
        description="Content type to filter",
        pattern="^(fact|preference|decision|personal_info|learning|context|reflection)$"
    )
    enabled: bool = Field(description="Whether to enable or disable capture for this type")


class AutoCaptureStatsInput(BaseModel):
    """Input for auto_capture_stats tool (empty input)."""
    pass


class AutoCaptureToolDefinitions:
    """
    Defines MCP tools for controlling the auto-capture system.
    """
    
    @property
    def auto_capture_control_schema(self) -> Dict[str, Any]:
        """Schema for the auto_capture_control tool."""
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Whether to enable or disable automatic memory capture"
                }
            },
            "required": ["enabled"]
        }
    
    @property
    def content_type_filter_schema(self) -> Dict[str, Any]:
        """Schema for the content_type_filter tool."""
        return {
            "type": "object",
            "properties": {
                "content_type": {
                    "type": "string",
                    "description": "Type of content to filter",
                    "enum": ["fact", "preference", "decision", "personal_info", "learning", "context", "reflection"]
                },
                "enabled": {
                    "type": "boolean",
                    "description": "Whether to enable capture for this content type"
                }
            },
            "required": ["content_type", "enabled"]
        }
    
    @property
    def auto_capture_stats_schema(self) -> Dict[str, Any]:
        """Schema for the auto_capture_stats tool."""
        return {
            "type": "object",
            "properties": {}
        }


def create_auto_capture_tools(conversation_analyzer) -> Dict[str, Any]:
    """
    Create tool handlers for auto-capture control.
    
    Args:
        conversation_analyzer: The conversation analyzer instance
        
    Returns:
        Dictionary of tool handlers
    """
    tools = {}
    
    async def auto_capture_control_handler(arguments: AutoCaptureControlInput) -> List[Dict[str, Any]]:
        """Handle auto_capture_control tool requests."""
        conversation_analyzer.set_auto_capture_enabled(arguments.enabled)
        
        return [{
            "type": "text",
            "text": f"Auto-capture {'enabled' if arguments.enabled else 'disabled'}"
        }]
    
    async def content_type_filter_handler(arguments: ContentTypeFilterInput) -> List[Dict[str, Any]]:
        """Handle content_type_filter tool requests."""
        content_type = ContentType(arguments.content_type)
        conversation_analyzer.set_content_type_filter(content_type, arguments.enabled)
        
        return [{
            "type": "text",
            "text": f"Content type '{arguments.content_type}' capture {'enabled' if arguments.enabled else 'disabled'}"
        }]
    
    async def auto_capture_stats_handler(arguments: AutoCaptureStatsInput) -> List[Dict[str, Any]]:
        """Handle auto_capture_stats tool requests."""
        stats = conversation_analyzer.get_capture_stats()
        
        return [{
            "type": "text",
            "text": f"Auto-capture statistics:\n"
                   f"- Enabled: {stats['auto_capture_enabled']}\n"
                   f"- Recent captures: {stats['recent_capture_count']}\n"
                   f"- Session messages: {stats['session_message_count']}\n"
                   f"- Captures by type: {stats['captures_by_type']}\n"
                   f"- Content filters: {stats['content_type_filters']}"
        }]
    
    tools["auto_capture_control"] = {
        "handler": auto_capture_control_handler,
        "description": "Enable or disable automatic memory capture",
        "input_schema": AutoCaptureControlInput
    }
    
    tools["content_type_filter"] = {
        "handler": content_type_filter_handler,
        "description": "Control which types of content are automatically captured",
        "input_schema": ContentTypeFilterInput
    }
    
    tools["auto_capture_stats"] = {
        "handler": auto_capture_stats_handler,
        "description": "Get statistics about automatic memory capture",
        "input_schema": AutoCaptureStatsInput
    }
    
    return tools