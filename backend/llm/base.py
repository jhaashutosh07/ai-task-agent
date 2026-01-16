from abc import ABC, abstractmethod
from typing import AsyncGenerator
from pydantic import BaseModel


class Message(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict] | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict


class BaseLLM(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        stream: bool = False
    ) -> Message | AsyncGenerator[str, None]:
        """Send a chat request to the LLM"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM provider is available"""
        pass
