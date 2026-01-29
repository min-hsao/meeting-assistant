"""OpenAI provider for research queries"""

import asyncio
import time
import logging
from typing import Optional

from openai import AsyncOpenAI
from .base import BaseProvider, ResearchResult

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider with optional web search"""
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_tokens: int = 250,
        temperature: float = 0.3,
        timeout_seconds: int = 15,
        web_search: bool = True,
        api_key: Optional[str] = None,
    ):
        super().__init__(model, max_tokens, temperature, timeout_seconds, web_search)
        self._client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    async def research(self, topic: str, context: str) -> ResearchResult:
        """Research topic using OpenAI API"""
        start_time = time.time()
        
        try:
            messages = [
                {"role": "system", "content": context},
                {"role": "user", "content": f"Research this topic briefly: {topic}"}
            ]
            
            # Build request kwargs
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "timeout": self.timeout_seconds,
            }
            
            # Note: web_search tool disabled for MVP - model returns content directly
            # TODO: Implement actual web search in Phase 3
            
            # Make API call
            response = await self._client.chat.completions.create(**kwargs)
            
            message = response.choices[0].message
            summary = message.content or ""
            
            logger.info(f"OpenAI response content length: {len(summary)}")
            latency_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"OpenAI research completed in {latency_ms}ms")
            
            return self._create_result(
                topic=topic,
                summary=summary.strip(),
                latency_ms=latency_ms,
                success=True,
            )
            
        except asyncio.TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"OpenAI request timed out after {latency_ms}ms")
            return self._create_result(
                topic=topic,
                latency_ms=latency_ms,
                success=False,
                error="Request timed out",
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"OpenAI request failed: {e}")
            return self._create_result(
                topic=topic,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
            )
