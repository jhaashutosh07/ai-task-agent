"""
Provider Manager - Unified LLM provider management with fallback chain
"""
from typing import AsyncGenerator, Optional
import logging
from .base import BaseLLM, Message, ToolDefinition
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Manages multiple LLM providers with automatic fallback support.

    Features:
    - Automatic fallback when primary provider fails
    - Provider health checking
    - Per-request provider selection
    - Cost tracking integration
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        ollama_base_url: str = "http://localhost:11434",
        default_provider: str = "openai",
        fallback_chain: Optional[list[str]] = None
    ):
        self.providers: dict[str, BaseLLM] = {}
        self.default_provider = default_provider
        self.fallback_chain = fallback_chain or ["openai", "anthropic", "gemini", "ollama"]

        # Initialize available providers
        if openai_api_key:
            try:
                self.providers["openai"] = OpenAIProvider(api_key=openai_api_key)
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")

        if anthropic_api_key:
            try:
                self.providers["anthropic"] = AnthropicProvider(api_key=anthropic_api_key)
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic provider: {e}")

        if google_api_key:
            try:
                self.providers["gemini"] = GeminiProvider(api_key=google_api_key)
                logger.info("Gemini provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini provider: {e}")

        # Ollama is always attempted (local, no API key needed)
        try:
            self.providers["ollama"] = OllamaProvider(base_url=ollama_base_url)
            logger.info("Ollama provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")

        if not self.providers:
            raise ValueError("No LLM providers could be initialized")

        # Set default to first available if specified default isn't available
        if default_provider not in self.providers:
            self.default_provider = list(self.providers.keys())[0]
            logger.warning(f"Default provider '{default_provider}' not available, using '{self.default_provider}'")

    def get_provider(self, name: Optional[str] = None) -> BaseLLM:
        """Get a specific provider by name or the default provider."""
        provider_name = name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not available. Available: {list(self.providers.keys())}")
        return self.providers[provider_name]

    def list_providers(self) -> list[str]:
        """List all available providers."""
        return list(self.providers.keys())

    async def health_check(self, provider_name: Optional[str] = None) -> dict[str, bool]:
        """Check health of one or all providers."""
        if provider_name:
            if provider_name not in self.providers:
                return {provider_name: False}
            return {provider_name: await self.providers[provider_name].health_check()}

        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        return results

    async def chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        stream: bool = False,
        provider: Optional[str] = None,
        use_fallback: bool = True
    ) -> Message | AsyncGenerator[str, None]:
        """
        Send a chat request with automatic fallback support.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            stream: Whether to stream the response
            provider: Specific provider to use (None for default)
            use_fallback: Whether to try fallback providers on failure
        """
        # Build provider order
        providers_to_try = []
        if provider:
            providers_to_try.append(provider)
        else:
            providers_to_try.append(self.default_provider)

        if use_fallback:
            for p in self.fallback_chain:
                if p not in providers_to_try and p in self.providers:
                    providers_to_try.append(p)

        last_error = None
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue

            try:
                logger.info(f"Attempting chat with provider: {provider_name}")
                llm = self.providers[provider_name]
                response = await llm.chat(messages, tools, stream)
                logger.info(f"Successfully got response from {provider_name}")
                return response
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {e}")
                if not use_fallback:
                    raise

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def chat_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        tools: Optional[list[ToolDefinition]] = None,
        provider: Optional[str] = None,
        use_fallback: bool = True
    ) -> Message:
        """
        Send a vision-enabled chat request with automatic fallback.
        Only uses providers that support vision.
        """
        # Filter to vision-capable providers
        vision_providers = [
            name for name, p in self.providers.items()
            if p.supports_vision
        ]

        if not vision_providers:
            raise ValueError("No vision-capable providers available")

        # Build provider order
        providers_to_try = []
        if provider and provider in vision_providers:
            providers_to_try.append(provider)
        elif self.default_provider in vision_providers:
            providers_to_try.append(self.default_provider)

        if use_fallback:
            for p in self.fallback_chain:
                if p not in providers_to_try and p in vision_providers:
                    providers_to_try.append(p)

        last_error = None
        for provider_name in providers_to_try:
            try:
                logger.info(f"Attempting vision chat with provider: {provider_name}")
                llm = self.providers[provider_name]
                response = await llm.chat_with_vision(messages, images, tools)
                logger.info(f"Successfully got vision response from {provider_name}")
                return response
            except Exception as e:
                last_error = e
                logger.warning(f"Vision provider {provider_name} failed: {e}")
                if not use_fallback:
                    raise

        raise RuntimeError(f"All vision providers failed. Last error: {last_error}")

    def get_cost_info(self) -> dict[str, tuple[float, float]]:
        """Get cost per 1K tokens for all providers."""
        return {
            name: provider.cost_per_1k_tokens
            for name, provider in self.providers.items()
        }

    def get_cheapest_provider(self, for_output: bool = False) -> str:
        """Get the name of the cheapest available provider."""
        costs = self.get_cost_info()
        if for_output:
            # Sort by output cost
            return min(costs.keys(), key=lambda k: costs[k][1])
        else:
            # Sort by input cost
            return min(costs.keys(), key=lambda k: costs[k][0])


# Singleton instance for easy access
_provider_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    """Get the global provider manager instance."""
    global _provider_manager
    if _provider_manager is None:
        raise RuntimeError("Provider manager not initialized. Call init_provider_manager first.")
    return _provider_manager


def init_provider_manager(
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None,
    ollama_base_url: str = "http://localhost:11434",
    default_provider: str = "openai",
    fallback_chain: Optional[list[str]] = None
) -> ProviderManager:
    """Initialize the global provider manager."""
    global _provider_manager
    _provider_manager = ProviderManager(
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        google_api_key=google_api_key,
        ollama_base_url=ollama_base_url,
        default_provider=default_provider,
        fallback_chain=fallback_chain
    )
    return _provider_manager
