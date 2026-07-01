"""
Free / OpenAI-compatible LLM providers.

Groq, OpenRouter and Cerebras all expose an OpenAI-compatible Chat Completions
API, so they reuse OpenAIProvider with a different base_url + model. All three
offer generous free tiers — get a free API key from each provider's console.
"""
from .openai_provider import OpenAIProvider


class GroqProvider(OpenAIProvider):
    """Groq — extremely fast inference on open models. Free tier. console.groq.com"""
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        super().__init__(api_key=api_key, model=model, base_url="https://api.groq.com/openai/v1")

    @property
    def supports_vision(self) -> bool:
        return False

    @property
    def cost_per_1k_tokens(self) -> tuple[float, float]:
        return (0.0, 0.0)  # free tier


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter — gateway to many models, several free. openrouter.ai"""
    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.3-70b-instruct:free"):
        super().__init__(api_key=api_key, model=model, base_url="https://openrouter.ai/api/v1")

    @property
    def supports_vision(self) -> bool:
        return False

    @property
    def cost_per_1k_tokens(self) -> tuple[float, float]:
        return (0.0, 0.0)  # free models


class CerebrasProvider(OpenAIProvider):
    """Cerebras — very fast inference on Llama models. Free tier. cloud.cerebras.ai"""
    def __init__(self, api_key: str, model: str = "llama-3.3-70b"):
        super().__init__(api_key=api_key, model=model, base_url="https://api.cerebras.ai/v1")

    @property
    def supports_vision(self) -> bool:
        return False

    @property
    def cost_per_1k_tokens(self) -> tuple[float, float]:
        return (0.0, 0.0)  # free tier
