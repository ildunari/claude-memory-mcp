"""
Enhanced automatic memory capture with intelligent content detection.

This module provides advanced analysis and extraction capabilities
for automatically capturing memory-worthy content from conversations.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

import numpy as np
from loguru import logger


class ContentType(Enum):
    """Types of content that can be captured."""
    FACT = "fact"
    PREFERENCE = "preference"
    DECISION = "decision"
    PERSONAL_INFO = "personal_info"
    LEARNING = "learning"
    CONTEXT = "context"
    REFLECTION = "reflection"


@dataclass
class CaptureCandidate:
    """A candidate for memory capture."""
    content_type: ContentType
    raw_text: str
    extracted_content: Dict[str, Any]
    confidence: float = 0.5
    importance: float = 0.5
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EnhancedAutoCaptureAnalyzer:
    """Advanced analyzer for automatic memory capture."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the analyzer with configuration."""
        self.config = config or {}
        self.min_confidence = self.config.get("min_confidence", 0.6)
        self.capture_enabled = self.config.get("auto_capture_enabled", True)
        
        # Initialize pattern sets for different content types
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize regex patterns for content detection."""
        # Personal information patterns
        self.personal_info_patterns = [
            (r"my name is (\w+(?:\s+\w+)*)", "name"),
            (r"call me (\w+)", "nickname"),
            (r"I(?:'m| am) (\d+) years old", "age"),
            (r"I(?:'m| am) from ([^.,]+)", "location"),
            (r"I work (?:at|for|as) ([^.,]+)", "occupation"),
            (r"I live in ([^.,]+)", "residence"),
            (r"my (?:email|mail) is ([^\s,]+@[^\s,]+)", "email"),
            (r"I have (\d+) (?:children|kids|child)", "children"),
            (r"I(?:'m| am) (?:a|an) ([^.,]+) (?:major|student)", "education"),
        ]
        
        # Preference patterns
        self.preference_patterns = [
            (r"I (?:really )?(?:like|love|enjoy|prefer) ([^.,]+)", "likes"),
            (r"I (?:hate|dislike|can't stand) ([^.,]+)", "dislikes"),
            (r"my favorite (\w+) is ([^.,]+)", "favorite"),
            (r"I(?:'m| am) (?:allergic to|intolerant to) ([^.,]+)", "allergies"),
            (r"I (?:always|usually|often) ([^.,]+)", "habits"),
            (r"I never ([^.,]+)", "avoidances"),
        ]
        
        # Decision patterns
        self.decision_patterns = [
            (r"I(?:'ve| have) decided to ([^.,]+)", "decision"),
            (r"I(?:'m| am) going to ([^.,]+)", "plan"),
            (r"I will ([^.,]+)", "commitment"),
            (r"I(?:'m| am) choosing ([^.,]+)", "choice"),
            (r"I(?:'ve| have) chosen ([^.,]+)", "choice_made"),
        ]
        
        # Learning/insight patterns
        self.learning_patterns = [
            (r"I(?:'ve| have) learned that ([^.,]+)", "learning"),
            (r"I(?:'ve| have) realized that ([^.,]+)", "realization"),
            (r"I now understand that ([^.,]+)", "understanding"),
            (r"I discovered that ([^.,]+)", "discovery"),
        ]
        
        # Factual information patterns
        self.fact_patterns = [
            (r"([^.,]+) (?:is|are) (?:the|a|an) ([^.,]+)", "definition"),
            (r"([^.,]+) was (?:born|founded|created|established) in (\d{4})", "historical"),
            (r"the (?:capital|largest city) of ([^.,]+) is ([^.,]+)", "geography"),
            (r"([^.,]+) (?:invented|discovered|created) ([^.,]+)", "attribution"),
        ]
    
    def analyze_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> List[CaptureCandidate]:
        """
        Analyze a message for memory-worthy content.
        
        Args:
            message: The message to analyze
            context: Optional context about the conversation
            
        Returns:
            List of capture candidates found in the message
        """
        if not self.capture_enabled:
            return []
        
        candidates = []
        context = context or {}
        
        # Check each content type
        candidates.extend(self._extract_personal_info(message, context))
        candidates.extend(self._extract_preferences(message, context))
        candidates.extend(self._extract_decisions(message, context))
        candidates.extend(self._extract_learnings(message, context))
        candidates.extend(self._extract_facts(message, context))
        
        # Filter by confidence threshold
        candidates = [c for c in candidates if c.confidence >= self.min_confidence]
        
        # Sort by importance
        candidates.sort(key=lambda x: x.importance, reverse=True)
        
        return candidates
    
    def _extract_personal_info(self, message: str, context: Dict[str, Any]) -> List[CaptureCandidate]:
        """Extract personal information from message."""
        candidates = []
        
        for pattern, info_type in self.personal_info_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                value = match.group(1).strip()
                
                candidate = CaptureCandidate(
                    content_type=ContentType.PERSONAL_INFO,
                    raw_text=match.group(0),
                    extracted_content={
                        "type": "entity",
                        "content": {
                            "name": "user",
                            "entity_type": "person",
                            "attributes": {info_type: value}
                        }
                    },
                    confidence=0.9,  # High confidence for explicit personal info
                    importance=0.8,  # High importance for personal details
                    context=context
                )
                candidates.append(candidate)
        
        return candidates
    
    def _extract_preferences(self, message: str, context: Dict[str, Any]) -> List[CaptureCandidate]:
        """Extract preferences from message."""
        candidates = []
        
        for pattern, pref_type in self.preference_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                if pref_type == "favorite":
                    category = match.group(1).strip()
                    value = match.group(2).strip()
                    pref_value = f"{category}: {value}"
                else:
                    pref_value = match.group(1).strip()
                
                candidate = CaptureCandidate(
                    content_type=ContentType.PREFERENCE,
                    raw_text=match.group(0),
                    extracted_content={
                        "type": "entity",
                        "content": {
                            "name": "user",
                            "entity_type": "person",
                            "attributes": {
                                "preferences": {pref_type: pref_value}
                            }
                        }
                    },
                    confidence=0.8,
                    importance=0.7,
                    context=context
                )
                candidates.append(candidate)
        
        return candidates
    
    def _extract_decisions(self, message: str, context: Dict[str, Any]) -> List[CaptureCandidate]:
        """Extract decisions and commitments from message."""
        candidates = []
        
        for pattern, decision_type in self.decision_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                decision_text = match.group(1).strip()
                
                candidate = CaptureCandidate(
                    content_type=ContentType.DECISION,
                    raw_text=match.group(0),
                    extracted_content={
                        "type": "reflection",
                        "content": {
                            "thought": f"User {decision_type}: {decision_text}",
                            "decision_type": decision_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    },
                    confidence=0.85,
                    importance=0.8,  # Decisions are important
                    context=context
                )
                candidates.append(candidate)
        
        return candidates
    
    def _extract_learnings(self, message: str, context: Dict[str, Any]) -> List[CaptureCandidate]:
        """Extract learnings and insights from message."""
        candidates = []
        
        for pattern, learning_type in self.learning_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                learning_text = match.group(1).strip()
                
                candidate = CaptureCandidate(
                    content_type=ContentType.LEARNING,
                    raw_text=match.group(0),
                    extracted_content={
                        "type": "reflection",
                        "content": {
                            "thought": f"{learning_type}: {learning_text}",
                            "learning_type": learning_type,
                            "confidence": 0.7
                        }
                    },
                    confidence=0.75,
                    importance=0.6,
                    context=context
                )
                candidates.append(candidate)
        
        return candidates
    
    def _extract_facts(self, message: str, context: Dict[str, Any]) -> List[CaptureCandidate]:
        """Extract factual information from message."""
        candidates = []
        
        # Skip if message is a question
        if message.strip().endswith('?'):
            return candidates
        
        for pattern, fact_type in self.fact_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                # Skip if it starts with question words
                if any(match.group(0).lower().startswith(q) for q in ['what', 'who', 'where', 'when', 'why', 'how']):
                    continue
                
                fact_text = match.group(0).strip()
                
                candidate = CaptureCandidate(
                    content_type=ContentType.FACT,
                    raw_text=fact_text,
                    extracted_content={
                        "type": "fact",
                        "content": {
                            "fact": fact_text,
                            "fact_type": fact_type,
                            "confidence": 0.7,
                            "domain": "general"
                        }
                    },
                    confidence=0.7,
                    importance=0.5,
                    context=context
                )
                candidates.append(candidate)
        
        return candidates
    
    def should_capture(self, candidate: CaptureCandidate) -> bool:
        """
        Determine if a capture candidate should be stored.
        
        Args:
            candidate: The capture candidate to evaluate
            
        Returns:
            True if the candidate should be stored
        """
        # Check confidence threshold
        if candidate.confidence < self.min_confidence:
            return False
        
        # Check importance threshold based on content type
        importance_thresholds = {
            ContentType.PERSONAL_INFO: 0.0,  # Always capture personal info
            ContentType.PREFERENCE: 0.3,
            ContentType.DECISION: 0.4,
            ContentType.LEARNING: 0.5,
            ContentType.FACT: 0.6,
            ContentType.CONTEXT: 0.5,
            ContentType.REFLECTION: 0.5,
        }
        
        threshold = importance_thresholds.get(candidate.content_type, 0.5)
        return candidate.importance >= threshold
    
    def format_for_storage(self, candidate: CaptureCandidate) -> Dict[str, Any]:
        """
        Format a capture candidate for storage in the memory system.
        
        Args:
            candidate: The capture candidate to format
            
        Returns:
            Formatted memory object ready for storage
        """
        memory_type = candidate.extracted_content.get("type", "conversation")
        content = candidate.extracted_content.get("content", {})
        
        # Add metadata
        metadata = {
            "auto_captured": True,
            "capture_timestamp": candidate.timestamp.isoformat(),
            "content_type": candidate.content_type.value,
            "confidence": candidate.confidence,
            "raw_text": candidate.raw_text
        }
        
        # Merge with existing metadata
        if "metadata" in content:
            content["metadata"].update(metadata)
        else:
            content["metadata"] = metadata
        
        return {
            "type": memory_type,
            "content": content,
            "importance": candidate.importance,
            "context": candidate.context
        }