from typing import AsyncGenerator
import json
import anthropic
from .base import BaseLLM, Message, ToolDefinition


class AnthropicProvider(BaseLLM):
    """Anthropic Claude LLM provider"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        stream: bool = False
    ) -> Message | AsyncGenerator[str, None]:
        # Separate system message from conversation
        system_message = ""
        conversation = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role == "tool":
                # Convert tool result to Anthropic format
                conversation.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content
                        }
                    ]
                })
            else:
                # Handle assistant messages with tool calls
                if msg.tool_calls:
                    content = []
                    if msg.content:
                        content.append({"type": "text", "text": msg.content})
                    for tc in msg.tool_calls:
                        content.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"])
                        })
                    conversation.append({"role": msg.role, "content": content})
                else:
                    conversation.append({"role": msg.role, "content": msg.content})

        # Convert tools to Anthropic format
        anthropic_tools = None
        if tools:
            anthropic_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.parameters
                }
                for tool in tools
            ]

        if stream:
            return self._stream_response(system_message, conversation, anthropic_tools)
        else:
            return await self._get_response(system_message, conversation, anthropic_tools)

    async def _get_response(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None
    ) -> Message:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        response = await self.client.messages.create(**kwargs)

        # Extract content and tool calls
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input)
                    }
                })

        return Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls if tool_calls else None
        )

    async def _stream_response(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None
    ) -> AsyncGenerator[str, None]:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def chat_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        tools: list[ToolDefinition] | None = None
    ) -> Message:
        """Chat with image understanding"""
        import base64

        # Build conversation with images
        system_message = ""
        conversation = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role == "user":
                # Add images to user message
                content = []
                for img_data in images:
                    base64_img = base64.b64encode(img_data).decode("utf-8")
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_img
                        }
                    })
                content.append({"type": "text", "text": msg.content})
                conversation.append({"role": "user", "content": content})
            else:
                conversation.append({"role": msg.role, "content": msg.content})

        # Convert tools
        anthropic_tools = None
        if tools:
            anthropic_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.parameters
                }
                for tool in tools
            ]

        return await self._get_response(system_message, conversation, anthropic_tools)

    async def health_check(self) -> bool:
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}]
            )
            return True
        except Exception:
            return False

    @property
    def supports_vision(self) -> bool:
        return True

    @property
    def cost_per_1k_tokens(self) -> tuple[float, float]:
        """Return (input_cost, output_cost) per 1K tokens"""
        costs = {
            "claude-3-5-sonnet-20241022": (0.003, 0.015),
            "claude-3-opus-20240229": (0.015, 0.075),
            "claude-3-haiku-20240307": (0.00025, 0.00125),
        }
        return costs.get(self.model, (0.003, 0.015))
