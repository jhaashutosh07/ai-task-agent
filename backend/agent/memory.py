from pydantic import BaseModel
from typing import List
from datetime import datetime
from llm.base import Message


class ConversationMemory:
    """Manages conversation history and context"""

    def __init__(self, max_messages: int = 50):
        self.messages: List[Message] = []
        self.max_messages = max_messages
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        return """You are an AI Task Automation Agent. You help users accomplish complex tasks by breaking them down into steps and using available tools.

## Your Capabilities:
1. **web_search** - Search the internet for information
2. **web_browser** - Read and extract content from web pages
3. **code_executor** - Write and execute Python code
4. **file_manager** - Read, write, and manage files

## How to Work:
1. Understand the user's request
2. Break complex tasks into smaller steps
3. Use tools to gather information or perform actions
4. Provide clear, helpful responses
5. If you need more information, ask the user

## Guidelines:
- Always explain what you're doing and why
- If a tool fails, try an alternative approach
- Be concise but thorough
- If you're unsure, ask for clarification

Current date: """ + datetime.now().strftime("%Y-%m-%d")

    def add_message(self, message: Message) -> None:
        """Add a message to history"""
        self.messages.append(message)

        # Trim if too long (keep system prompt intact)
        if len(self.messages) > self.max_messages:
            # Keep first few and last messages
            self.messages = self.messages[-self.max_messages:]

    def get_messages(self) -> List[Message]:
        """Get all messages including system prompt"""
        system_msg = Message(role="system", content=self.system_prompt)
        return [system_msg] + self.messages

    def clear(self) -> None:
        """Clear conversation history"""
        self.messages = []

    def get_context_summary(self) -> str:
        """Get a summary of the conversation context"""
        if not self.messages:
            return "No conversation history"

        user_msgs = [m for m in self.messages if m.role == "user"]
        return f"Conversation with {len(self.messages)} messages, {len(user_msgs)} from user"
