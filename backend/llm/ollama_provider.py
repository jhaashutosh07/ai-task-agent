from typing import AsyncGenerator
import json
import httpx
from .base import BaseLLM, Message, ToolDefinition


class OllamaProvider(BaseLLM):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        stream: bool = False
    ) -> Message | AsyncGenerator[str, None]:
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Build request payload
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": stream
        }

        # Add tools if provided (Ollama supports function calling)
        if tools:
            payload["tools"] = [
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
            return self._stream_response(payload)
        else:
            return await self._get_response(payload)

    async def _get_response(self, payload: dict) -> Message:
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json=payload
        )
        response.raise_for_status()
        data = response.json()

        # Handle tool calls from Ollama
        tool_calls = None
        if "message" in data and "tool_calls" in data["message"]:
            tool_calls = []
            for i, tc in enumerate(data["message"]["tool_calls"]):
                tool_calls.append({
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": json.dumps(tc["function"]["arguments"])
                    }
                })

        content = data.get("message", {}).get("content", "")
        return Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls
        )

    async def _stream_response(self, payload: dict) -> AsyncGenerator[str, None]:
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
