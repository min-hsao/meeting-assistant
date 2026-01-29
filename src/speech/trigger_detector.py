"""Trigger phrase detection and topic extraction"""

import re
import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TriggerMatch:
    """Represents a detected trigger phrase match"""
    trigger_type: str  # 'research', 'transcription_start', 'transcription_stop'
    trigger_phrase: str
    topic: Optional[str]  # Extracted topic for research triggers
    confidence: float
    raw_text: str


class TriggerDetector:
    """Detects trigger phrases in transcribed text and extracts topics"""
    
    def __init__(self, triggers_config: dict):
        """
        Args:
            triggers_config: Dictionary with trigger phrase lists:
                - research: ["did you say", "what is", ...]
                - transcription_start: ["can you repeat that", ...]
                - transcription_stop: ["end note", ...]
                - custom: [...]
        """
        self.triggers = triggers_config
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for trigger detection"""
        self._patterns = {}
        
        # Research triggers - need to extract topic
        research_triggers = self.triggers.get('research', []) + self.triggers.get('custom', [])
        research_patterns = []
        for trigger in research_triggers:
            # Escape special chars and create pattern
            # Match trigger phrase followed by topic (rest of text)
            escaped = re.escape(trigger.lower())
            pattern = rf"(?:^|[.\s])({escaped})\s+(.+?)(?:[.?!]|$)"
            research_patterns.append(pattern)
        
        if research_patterns:
            self._patterns['research'] = re.compile(
                '|'.join(research_patterns),
                re.IGNORECASE
            )
        
        # Transcription start triggers - no topic extraction
        start_triggers = self.triggers.get('transcription_start', [])
        if start_triggers:
            patterns = [re.escape(t.lower()) for t in start_triggers]
            self._patterns['transcription_start'] = re.compile(
                '|'.join(patterns),
                re.IGNORECASE
            )
        
        # Transcription stop triggers - no topic extraction
        stop_triggers = self.triggers.get('transcription_stop', [])
        if stop_triggers:
            patterns = [re.escape(t.lower()) for t in stop_triggers]
            self._patterns['transcription_stop'] = re.compile(
                '|'.join(patterns),
                re.IGNORECASE
            )
    
    def detect(self, text: str) -> Optional[TriggerMatch]:
        """
        Detect trigger phrase in text.
        
        Args:
            text: Transcribed text to check
            
        Returns:
            TriggerMatch if trigger detected, None otherwise
        """
        if not text:
            return None
        
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Check research triggers first (most common use case)
        if 'research' in self._patterns:
            match = self._patterns['research'].search(text_lower)
            if match:
                # Find which group matched
                groups = match.groups()
                trigger_phrase = None
                topic = None
                
                # Groups come in pairs (trigger, topic) for each alternative
                for i in range(0, len(groups), 2):
                    if groups[i] is not None:
                        trigger_phrase = groups[i]
                        topic = groups[i + 1] if i + 1 < len(groups) else None
                        break
                
                if trigger_phrase and topic:
                    # Clean up the topic
                    topic = self._clean_topic(topic)
                    if topic:
                        logger.info(f"Research trigger detected: '{trigger_phrase}' -> topic: '{topic}'")
                        return TriggerMatch(
                            trigger_type='research',
                            trigger_phrase=trigger_phrase,
                            topic=topic,
                            confidence=0.9,
                            raw_text=text_clean
                        )
        
        # Check transcription start triggers
        if 'transcription_start' in self._patterns:
            match = self._patterns['transcription_start'].search(text_lower)
            if match:
                logger.info(f"Transcription start trigger detected: '{match.group()}'")
                return TriggerMatch(
                    trigger_type='transcription_start',
                    trigger_phrase=match.group(),
                    topic=None,
                    confidence=0.9,
                    raw_text=text_clean
                )
        
        # Check transcription stop triggers
        if 'transcription_stop' in self._patterns:
            match = self._patterns['transcription_stop'].search(text_lower)
            if match:
                logger.info(f"Transcription stop trigger detected: '{match.group()}'")
                return TriggerMatch(
                    trigger_type='transcription_stop',
                    trigger_phrase=match.group(),
                    topic=None,
                    confidence=0.9,
                    raw_text=text_clean
                )
        
        return None
    
    def _clean_topic(self, topic: str) -> str:
        """Clean up extracted topic"""
        # Remove common filler words at start
        fillers = ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'so', 'well']
        
        topic = topic.strip()
        topic_lower = topic.lower()
        
        for filler in fillers:
            if topic_lower.startswith(filler + ' '):
                topic = topic[len(filler):].strip()
                topic_lower = topic.lower()
        
        # Remove trailing punctuation
        topic = topic.rstrip('.,!?;:')
        
        # Capitalize first letter
        if topic:
            topic = topic[0].upper() + topic[1:]
        
        return topic
    
    def update_triggers(self, triggers_config: dict):
        """Update trigger configuration"""
        self.triggers = triggers_config
        self._compile_patterns()
    
    def add_custom_trigger(self, phrase: str):
        """Add a custom trigger phrase"""
        if 'custom' not in self.triggers:
            self.triggers['custom'] = []
        if phrase.lower() not in [t.lower() for t in self.triggers['custom']]:
            self.triggers['custom'].append(phrase)
            self._compile_patterns()
