from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any


class ToolResult(BaseModel):
    success: bool
    output: str
    error: str | None = None


class BaseTool(ABC):
    """Abstract base class for all tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for the tool"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema for the tool parameters"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass

    def to_definition(self) -> dict:
        """Convert tool to LLM-compatible definition"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
