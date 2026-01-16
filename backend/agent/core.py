import json
from typing import AsyncGenerator, Callable, Any
from llm.base import BaseLLM, Message, ToolDefinition
from tools.base import BaseTool, ToolResult
from .memory import ConversationMemory
from .planner import TaskPlanner


class AgentEvent:
    """Event emitted during agent execution"""
    def __init__(self, event_type: str, data: dict):
        self.type = event_type
        self.data = data

    def to_dict(self) -> dict:
        return {"type": self.type, "data": self.data}


class Agent:
    """Main AI Agent that orchestrates LLM and tools"""

    def __init__(
        self,
        llm: BaseLLM,
        tools: list[BaseTool],
        max_iterations: int = 10
    ):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.memory = ConversationMemory()
        self.planner = TaskPlanner()
        self.max_iterations = max_iterations

    def _get_tool_definitions(self) -> list[ToolDefinition]:
        """Convert tools to LLM-compatible definitions"""
        return [
            ToolDefinition(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters
            )
            for tool in self.tools.values()
        ]

    async def run(
        self,
        user_message: str,
        on_event: Callable[[AgentEvent], Any] | None = None
    ) -> str:
        """Run the agent with a user message"""

        # Add user message to memory
        self.memory.add_message(Message(role="user", content=user_message))

        # Emit thinking event
        if on_event:
            on_event(AgentEvent("thinking", {"message": "Processing your request..."}))

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1

            # Get LLM response
            messages = self.memory.get_messages()
            tools = self._get_tool_definitions()

            response = await self.llm.chat(messages, tools=tools)

            # Check if LLM wants to use tools
            if response.tool_calls:
                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])

                    # Emit tool call event
                    if on_event:
                        on_event(AgentEvent("tool_call", {
                            "tool": tool_name,
                            "args": tool_args
                        }))

                    # Execute tool
                    result = await self._execute_tool(tool_name, tool_args)

                    # Emit tool result event
                    if on_event:
                        on_event(AgentEvent("tool_result", {
                            "tool": tool_name,
                            "success": result.success,
                            "output": result.output[:500] if result.output else "",
                            "error": result.error
                        }))

                    # Add assistant message with tool call
                    self.memory.add_message(Message(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls
                    ))

                    # Add tool result to memory
                    tool_result_content = result.output if result.success else f"Error: {result.error}"
                    self.memory.add_message(Message(
                        role="tool",
                        content=tool_result_content,
                        tool_call_id=tool_call["id"]
                    ))

            else:
                # No tool calls - this is the final response
                self.memory.add_message(response)

                if on_event:
                    on_event(AgentEvent("complete", {"message": response.content}))

                return response.content

        # Max iterations reached
        final_message = "I've reached the maximum number of steps. Here's what I've accomplished so far based on our conversation."
        if on_event:
            on_event(AgentEvent("max_iterations", {"message": final_message}))

        return final_message

    async def _execute_tool(self, tool_name: str, args: dict) -> ToolResult:
        """Execute a tool by name"""
        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}"
            )

        tool = self.tools[tool_name]
        try:
            return await tool.execute(**args)
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool execution failed: {str(e)}"
            )

    async def stream(
        self,
        user_message: str,
        on_event: Callable[[AgentEvent], Any] | None = None
    ) -> AsyncGenerator[str, None]:
        """Stream the agent response"""
        # For streaming, we do a simplified single-turn response
        self.memory.add_message(Message(role="user", content=user_message))

        messages = self.memory.get_messages()
        tools = self._get_tool_definitions()

        async for chunk in await self.llm.chat(messages, tools=tools, stream=True):
            yield chunk

    def clear_memory(self) -> None:
        """Clear conversation memory"""
        self.memory.clear()
        self.planner.clear()

    def get_conversation_history(self) -> list[dict]:
        """Get the conversation history"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.memory.messages
        ]
