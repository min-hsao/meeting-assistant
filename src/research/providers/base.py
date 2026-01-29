"""Base class for AI research providers"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class ResearchResult:
    """Result from a research query"""
    topic: str
    summary: str
    provider: str
    model: str
    latency_ms: int
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "summary": self.summary,
            "provider": self.provider,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error": self.error,
        }


class BaseProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(
        self,
        model: str,
        max_tokens: int = 250,
        temperature: float = 0.3,
        timeout_seconds: int = 15,
        web_search: bool = True,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.web_search = web_search
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name"""
        pass
    
    @abstractmethod
    async def research(self, topic: str, context: str) -> ResearchResult:
        """
        Research a topic and return summary.
        
        Args:
            topic: The topic to research
            context: System context/instructions
            
        Returns:
            ResearchResult with summary or error
        """
        pass
    
    def _create_result(
        self,
        topic: str,
        summary: str = "",
        latency_ms: int = 0,
        success: bool = True,
        error: Optional[str] = None,
    ) -> ResearchResult:
        """Helper to create a ResearchResult"""
        return ResearchResult(
            topic=topic,
            summary=summary,
            provider=self.provider_name,
            model=self.model,
            latency_ms=latency_ms,
            success=success,
            error=error,
        )
