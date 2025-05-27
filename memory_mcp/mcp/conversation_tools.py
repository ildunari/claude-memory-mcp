"""
MCP tools for processing conversation messages for auto-capture.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from loguru import logger


class ProcessMessageInput(BaseModel):
    """Input for process_message tool."""
    message: str = Field(description="The message to process")
    role: str = Field(
        description="Role of the message sender", 
        default="user",
        pattern="^(user|assistant)$"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        description="Optional metadata about the message",
        default=None
    )


def create_conversation_tools(conversation_analyzer) -> Dict[str, Any]:
    """
    Create tool handlers for conversation processing.
    
    Args:
        conversation_analyzer: The conversation analyzer instance
        
    Returns:
        Dictionary of tool handlers
    """
    tools = {}
    
    async def process_message_handler(arguments: ProcessMessageInput) -> List[Dict[str, Any]]:
        """Handle process_message tool requests."""
        try:
            # Process the message for auto-capture
            captured = await conversation_analyzer.process_message(
                message=arguments.message,
                role=arguments.role,
                metadata=arguments.metadata
            )
            
            if captured:
                logger.info(f"Auto-captured {len(captured)} memories from message")
                return [{
                    "type": "text",
                    "text": f"Processed message and captured {len(captured)} memories"
                }]
            else:
                return [{
                    "type": "text",
                    "text": "Message processed (no memories captured)"
                }]
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return [{
                "type": "text",
                "text": f"Error processing message: {str(e)}",
                "is_error": True
            }]
    
    tools["process_message"] = {
        "handler": process_message_handler,
        "description": "Process a conversation message for automatic memory capture",
        "input_schema": ProcessMessageInput
    }
    
    return tools