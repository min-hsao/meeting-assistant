"""Research engine orchestrating AI providers"""

import asyncio
import logging
from typing import Dict, Optional

from .providers.base import BaseProvider, ResearchResult
from .providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ResearchEngine:
    """Orchestrates research queries across multiple AI providers"""
    
    def __init__(self, settings: dict):
        """
        Args:
            settings: Research and API configuration from settings manager
        """
        self.settings = settings
        self._providers: Dict[str, BaseProvider] = {}
        self._default_provider: Optional[str] = None
        self._context = settings.get('research', {}).get('context', '')
        self._meeting_context = settings.get('research', {}).get('meeting_context', '')
        
        self._init_providers()
    
    def _init_providers(self):
        """Initialize enabled providers"""
        api_config = self.settings.get('api', {})
        research_config = self.settings.get('research', {})
        
        # Common settings
        max_tokens = research_config.get('max_tokens', 250)
        temperature = research_config.get('temperature', 0.3)
        timeout = research_config.get('timeout_seconds', 15)
        web_search = research_config.get('web_search', True)
        
        # OpenAI
        if api_config.get('openai', {}).get('enabled', False):
            model = api_config['openai'].get('model', 'gpt-4o-mini')
            self._providers['openai'] = OpenAIProvider(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout_seconds=timeout,
                web_search=web_search,
            )
            logger.info(f"Initialized OpenAI provider with model: {model}")
        
        # TODO: Add other providers (DeepSeek, Gemini, GLM) in Phase 3
        
        # Set default provider
        self._default_provider = research_config.get('default_provider', 'openai')
        if self._default_provider not in self._providers and self._providers:
            self._default_provider = list(self._providers.keys())[0]
            logger.warning(f"Default provider not available, using: {self._default_provider}")
    
    def get_context(self) -> str:
        """Get combined research context"""
        context = self._context
        if self._meeting_context:
            context += f"\n\nMeeting context: {self._meeting_context}"
        return context
    
    def set_meeting_context(self, context: str):
        """Set per-meeting context"""
        self._meeting_context = context
        logger.info(f"Meeting context updated: {context[:50]}...")
    
    def clear_meeting_context(self):
        """Clear per-meeting context"""
        self._meeting_context = ""
        logger.info("Meeting context cleared")
    
    async def research(
        self,
        topic: str,
        provider: Optional[str] = None,
    ) -> ResearchResult:
        """
        Research a topic using the specified or default provider.
        
        Args:
            topic: Topic to research
            provider: Provider name (optional, uses default if not specified)
            
        Returns:
            ResearchResult with summary or error
        """
        provider_name = provider or self._default_provider
        
        if not provider_name or provider_name not in self._providers:
            return ResearchResult(
                topic=topic,
                summary="",
                provider="none",
                model="",
                latency_ms=0,
                success=False,
                error=f"No provider available (requested: {provider_name})",
            )
        
        provider_instance = self._providers[provider_name]
        context = self.get_context()
        
        logger.info(f"Researching '{topic}' with {provider_name}")
        
        return await provider_instance.research(topic, context)
    
    def research_sync(
        self,
        topic: str,
        provider: Optional[str] = None,
    ) -> ResearchResult:
        """Synchronous wrapper for research()"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.research(topic, provider))
        finally:
            loop.close()
    
    @property
    def available_providers(self) -> list:
        """List of available provider names"""
        return list(self._providers.keys())
    
    @property
    def default_provider(self) -> Optional[str]:
        """Current default provider name"""
        return self._default_provider
