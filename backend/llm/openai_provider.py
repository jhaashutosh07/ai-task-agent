from typing import AsyncGenerator
import logging
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base import BaseLLM, Message, ToolDefinition

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLM):
    """OpenAI LLM provider with vision support and retry logic"""

    # Model cost per 1k tokens (input, output)
    MODEL_COSTS = {
        "gpt-4o-mini": (0.00015, 0.0006),
        "gpt-4o": (0.005, 0.015),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4-vision-preview": (0.01, 0.03),
        "gpt-3.5-turbo": (0.0005, 0.0015),
    }

    # Models that support vision
    VISION_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-vision-preview"]

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    @property
    def supports_vision(self) -> bool:
        """Check if the current model supports vision/image inputs"""
        return any(vm in self.model for vm in self.VISION_MODELS)

    @property
    def cost_per_1k_tokens(self) -> tuple[float, float]:
        """Return (input_cost, output_cost) per 1k tokens"""
        return self.MODEL_COSTS.get(self.model, (0.00015, 0.0006))

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        stream: bool = False
    ) -> Message | AsyncGenerator[str, None]:
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_msg = {"role": msg.role, "content": msg.content}
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                openai_msg["tool_calls"] = msg.tool_calls
            openai_messages.append(openai_msg)

        # Convert tools to OpenAI format
        openai_tools = None
        if tools:
            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                }
                for tool in tools
            ]

        if stream:
            return self._stream_response(openai_messages, openai_tools)
        else:
            return await self._get_response(openai_messages, openai_tools)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError, APITimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"OpenAI API call failed, retrying in {retry_state.next_action.sleep} seconds..."
        )
    )
    async def _get_response(
        self,
        messages: list[dict],
        tools: list[dict] | None
    ) -> Message:
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        # Handle tool calls
        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in choice.message.tool_calls
            ]

        return Message(
            role="assistant",
            content=choice.message.content or "",
            tool_calls=tool_calls
        )

    async def _stream_response(
        self,
        messages: list[dict],
        tools: list[dict] | None
    ) -> AsyncGenerator[str, None]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        async for chunk in await self.client.chat.completions.create(**kwargs):
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def health_check(self) -> bool:
        """Check if the OpenAI API is accessible"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            return True
        except (APIError, RateLimitError, APITimeoutError) as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI health check: {e}")
            return False
