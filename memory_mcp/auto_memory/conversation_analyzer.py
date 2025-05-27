"""
Conversation analyzer for processing and capturing memories from conversations.

This module provides the infrastructure for analyzing conversations,
extracting memory-worthy content, and triggering automatic storage.
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import deque

from loguru import logger

from memory_mcp.auto_memory.enhanced_capture import (
    EnhancedAutoCaptureAnalyzer,
    CaptureCandidate,
    ContentType
)


class ConversationAnalyzer:
    """
    Analyzes conversations and triggers automatic memory capture.
    
    This class maintains conversation context, analyzes messages,
    and coordinates with the memory system for automatic storage.
    """
    
    def __init__(
        self,
        memory_store_callback: Callable,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the conversation analyzer.
        
        Args:
            memory_store_callback: Async callback function to store memories
            config: Optional configuration dictionary
        """
        self.memory_store_callback = memory_store_callback
        self.config = config or {}
        
        # Initialize the capture analyzer
        self.capture_analyzer = EnhancedAutoCaptureAnalyzer(config)
        
        # Conversation context tracking
        self.conversation_history = deque(
            maxlen=self.config.get("context_window_size", 10)
        )
        self.current_session_id = None
        self.session_start_time = None
        
        # Deduplication tracking
        self.recent_captures = deque(
            maxlen=self.config.get("dedup_window_size", 50)
        )
        self.capture_cooldown = timedelta(
            minutes=self.config.get("capture_cooldown_minutes", 5)
        )
        
        # User preferences
        self.auto_capture_enabled = self.config.get("auto_capture_enabled", True)
        self.capture_filters = self.config.get("capture_filters", {})
    
    async def process_message(
        self,
        message: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a message and capture any memory-worthy content.
        
        Args:
            message: The message to process
            role: Role of the message sender (user/assistant)
            metadata: Optional metadata about the message
            
        Returns:
            List of memories that were captured and stored
        """
        if not self.auto_capture_enabled:
            return []
        
        # Update conversation context
        self._update_context(message, role, metadata)
        
        # Only analyze user messages for now
        if role != "user":
            return []
        
        # Build context for analysis
        context = self._build_analysis_context()
        
        # Analyze the message
        candidates = self.capture_analyzer.analyze_message(message, context)
        
        # Filter and deduplicate candidates
        filtered_candidates = self._filter_candidates(candidates)
        
        # Store approved candidates
        stored_memories = []
        for candidate in filtered_candidates:
            if self.capture_analyzer.should_capture(candidate):
                memory = await self._store_candidate(candidate)
                if memory:
                    stored_memories.append(memory)
        
        return stored_memories
    
    def _update_context(
        self,
        message: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update the conversation context with a new message."""
        # Start new session if needed
        if self.current_session_id is None:
            self._start_new_session()
        
        # Add to conversation history
        self.conversation_history.append({
            "message": message,
            "role": role,
            "timestamp": datetime.now(),
            "metadata": metadata or {},
            "session_id": self.current_session_id
        })
    
    def _start_new_session(self):
        """Start a new conversation session."""
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_start_time = datetime.now()
        logger.info(f"Started new conversation session: {self.current_session_id}")
    
    def _build_analysis_context(self) -> Dict[str, Any]:
        """Build context for message analysis."""
        # Get recent conversation turns
        recent_turns = list(self.conversation_history)[-5:]
        
        return {
            "session_id": self.current_session_id,
            "session_duration": (
                (datetime.now() - self.session_start_time).total_seconds()
                if self.session_start_time else 0
            ),
            "recent_messages": [
                {"role": turn["role"], "message": turn["message"][:100]}
                for turn in recent_turns
            ],
            "message_count": len(self.conversation_history)
        }
    
    def _filter_candidates(
        self,
        candidates: List[CaptureCandidate]
    ) -> List[CaptureCandidate]:
        """Filter candidates based on user preferences and deduplication."""
        filtered = []
        
        for candidate in candidates:
            # Check content type filters
            content_type_enabled = self.capture_filters.get(
                candidate.content_type.value, True
            )
            if not content_type_enabled:
                continue
            
            # Check for duplicates
            if self._is_duplicate(candidate):
                logger.debug(f"Skipping duplicate candidate: {candidate.raw_text[:50]}...")
                continue
            
            # Check cooldown
            if self._in_cooldown(candidate):
                logger.debug(f"Candidate in cooldown: {candidate.raw_text[:50]}...")
                continue
            
            filtered.append(candidate)
        
        return filtered
    
    def _is_duplicate(self, candidate: CaptureCandidate) -> bool:
        """Check if a candidate is a duplicate of recent captures."""
        # Simple text similarity check for now
        candidate_text = candidate.raw_text.lower().strip()
        
        for recent in self.recent_captures:
            recent_text = recent.get("raw_text", "").lower().strip()
            
            # Exact match
            if candidate_text == recent_text:
                return True
            
            # Substring match (one contains the other)
            if candidate_text in recent_text or recent_text in candidate_text:
                return True
        
        return False
    
    def _in_cooldown(self, candidate: CaptureCandidate) -> bool:
        """Check if a similar candidate was recently captured."""
        # Check if we've captured similar content recently
        for recent in self.recent_captures:
            if recent.get("content_type") == candidate.content_type.value:
                recent_time = datetime.fromisoformat(recent.get("timestamp"))
                if datetime.now() - recent_time < self.capture_cooldown:
                    return True
        
        return False
    
    async def _store_candidate(self, candidate: CaptureCandidate) -> Optional[Dict[str, Any]]:
        """Store a capture candidate in the memory system."""
        try:
            # Format for storage
            memory_data = self.capture_analyzer.format_for_storage(candidate)
            
            # Call the storage callback
            memory_id = await self.memory_store_callback(
                memory_type=memory_data["type"],
                content=memory_data["content"],
                importance=memory_data["importance"],
                context=memory_data.get("context", {})
            )
            
            # Track the capture for deduplication
            self.recent_captures.append({
                "raw_text": candidate.raw_text,
                "content_type": candidate.content_type.value,
                "timestamp": datetime.now().isoformat(),
                "memory_id": memory_id
            })
            
            logger.info(f"Auto-captured {candidate.content_type.value} memory: {memory_id}")
            
            return {
                "memory_id": memory_id,
                "type": memory_data["type"],
                "content_type": candidate.content_type.value,
                "confidence": candidate.confidence,
                "importance": candidate.importance
            }
            
        except Exception as e:
            logger.error(f"Failed to store capture candidate: {e}")
            return None
    
    def set_auto_capture_enabled(self, enabled: bool):
        """Enable or disable automatic capture."""
        self.auto_capture_enabled = enabled
        self.capture_analyzer.capture_enabled = enabled
        logger.info(f"Auto-capture {'enabled' if enabled else 'disabled'}")
    
    def set_content_type_filter(self, content_type: ContentType, enabled: bool):
        """Enable or disable capture for a specific content type."""
        self.capture_filters[content_type.value] = enabled
        logger.info(f"Content type {content_type.value} capture {'enabled' if enabled else 'disabled'}")
    
    def get_capture_stats(self) -> Dict[str, Any]:
        """Get statistics about recent captures."""
        stats = {
            "auto_capture_enabled": self.auto_capture_enabled,
            "recent_capture_count": len(self.recent_captures),
            "session_id": self.current_session_id,
            "session_message_count": len(self.conversation_history),
            "content_type_filters": self.capture_filters
        }
        
        # Count by content type
        type_counts = {}
        for capture in self.recent_captures:
            content_type = capture.get("content_type", "unknown")
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
        
        stats["captures_by_type"] = type_counts
        
        return stats