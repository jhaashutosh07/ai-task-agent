from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import json


class Message(BaseModel):
    """A single message in the conversation"""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    timestamp: datetime = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    metadata: Dict[str, Any] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.now()


class ConversationSummary(BaseModel):
    """Summary of a conversation segment"""
    content: str
    message_count: int
    start_time: datetime
    end_time: datetime
    topics: List[str] = []


class ConversationMemory:
    """
    Advanced conversation memory with summarization and context management.
    Automatically summarizes old messages to maintain context within token limits.
    """

    def __init__(
        self,
        max_messages: int = 50,
        max_tokens_estimate: int = 8000,
        summarize_threshold: int = 30
    ):
        self.messages: List[Message] = []
        self.summaries: List[ConversationSummary] = []
        self.max_messages = max_messages
        self.max_tokens_estimate = max_tokens_estimate
        self.summarize_threshold = summarize_threshold
        self.system_prompt = self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        return f"""You are an advanced AI Task Automation Agent with multiple specialized capabilities.

## Multi-Agent System
You coordinate specialized agents:
- **Researcher**: Web search, information gathering
- **Coder**: Code generation and execution
- **Analyst**: Data analysis and visualization
- **Executor**: System operations and automation

## Available Tools
1. **web_search** - Search the internet
2. **web_browser** - Read web pages
3. **code_executor** - Run Python code
4. **file_manager** - Manage files
5. **shell_execute** - Run shell commands
6. **api_caller** - Make HTTP requests
7. **pdf_reader** - Extract PDF content
8. **screenshot** - Capture web pages
9. **database** - Execute SQL queries
10. **send_email** - Send emails

## Workflow Capabilities
- Save and replay automation workflows
- Schedule recurring tasks
- Chain multiple operations

## Guidelines
- Break complex tasks into steps
- Use parallel execution when possible
- Confirm dangerous operations with user
- Learn from past interactions
- Provide clear progress updates

Current date: {datetime.now().strftime("%Y-%m-%d")}
"""

    def add_message(self, message: Message) -> None:
        """Add a message and manage memory size"""
        self.messages.append(message)

        # Check if we need to summarize
        if len(self.messages) > self.summarize_threshold:
            self._summarize_old_messages()

        # Hard limit on messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def _summarize_old_messages(self) -> None:
        """Summarize older messages to save context space"""
        if len(self.messages) < self.summarize_threshold:
            return

        # Take first half of messages to summarize
        split_point = len(self.messages) // 2
        to_summarize = self.messages[:split_point]
        self.messages = self.messages[split_point:]

        # Create summary
        if to_summarize:
            topics = self._extract_topics(to_summarize)
            summary_content = self._create_summary(to_summarize)

            self.summaries.append(ConversationSummary(
                content=summary_content,
                message_count=len(to_summarize),
                start_time=to_summarize[0].timestamp,
                end_time=to_summarize[-1].timestamp,
                topics=topics
            ))

    def _extract_topics(self, messages: List[Message]) -> List[str]:
        """Extract main topics from messages"""
        topics = set()
        keywords = ["search", "code", "file", "analyze", "create", "fix", "update", "delete"]

        for msg in messages:
            if msg.role == "user":
                content_lower = msg.content.lower()
                for kw in keywords:
                    if kw in content_lower:
                        topics.add(kw)

        return list(topics)[:5]

    def _create_summary(self, messages: List[Message]) -> str:
        """Create a text summary of messages"""
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]

        summary = f"Previous conversation ({len(messages)} messages): "
        summary += f"User made {len(user_messages)} requests. "

        if user_messages:
            first_request = user_messages[0].content[:100]
            summary += f"Started with: '{first_request}...'. "

        if assistant_messages:
            summary += f"Assistant provided {len(assistant_messages)} responses."

        return summary

    def get_messages(self, include_summaries: bool = True) -> List[Message]:
        """Get all messages including system prompt and summaries"""
        result = [Message(role="system", content=self.system_prompt)]

        # Add summaries as context
        if include_summaries and self.summaries:
            summary_content = "**Previous Conversation Context:**\n"
            for s in self.summaries[-3:]:  # Last 3 summaries
                summary_content += f"- {s.content}\n"
            result.append(Message(role="system", content=summary_content))

        result.extend(self.messages)
        return result

    def get_context_window(self, max_messages: int = 20) -> List[Message]:
        """Get recent messages within context window"""
        messages = self.get_messages()
        if len(messages) > max_messages:
            # Keep system messages and recent messages
            system_msgs = [m for m in messages if m.role == "system"]
            other_msgs = [m for m in messages if m.role != "system"]
            return system_msgs + other_msgs[-(max_messages - len(system_msgs)):]
        return messages

    def clear(self) -> None:
        """Clear conversation but keep summaries"""
        self.messages = []

    def clear_all(self) -> None:
        """Clear everything including summaries"""
        self.messages = []
        self.summaries = []

    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history as dicts"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            }
            for msg in self.messages
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        user_count = sum(1 for m in self.messages if m.role == "user")
        assistant_count = sum(1 for m in self.messages if m.role == "assistant")
        tool_count = sum(1 for m in self.messages if m.role == "tool")

        return {
            "total_messages": len(self.messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "tool_messages": tool_count,
            "summaries": len(self.summaries),
            "estimated_tokens": self._estimate_tokens()
        }

    def _estimate_tokens(self) -> int:
        """Rough estimate of token count"""
        total_chars = sum(len(m.content) for m in self.messages)
        total_chars += len(self.system_prompt)
        for s in self.summaries:
            total_chars += len(s.content)
        return total_chars // 4  # Rough estimate: 4 chars per token

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps({
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "metadata": m.metadata
                }
                for m in self.messages
            ],
            "summaries": [
                {
                    "content": s.content,
                    "message_count": s.message_count,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "topics": s.topics
                }
                for s in self.summaries
            ]
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ConversationMemory":
        """Deserialize from JSON"""
        data = json.loads(json_str)
        memory = cls()

        for msg_data in data.get("messages", []):
            memory.messages.append(Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]) if msg_data.get("timestamp") else None,
                metadata=msg_data.get("metadata", {})
            ))

        for sum_data in data.get("summaries", []):
            memory.summaries.append(ConversationSummary(
                content=sum_data["content"],
                message_count=sum_data["message_count"],
                start_time=datetime.fromisoformat(sum_data["start_time"]),
                end_time=datetime.fromisoformat(sum_data["end_time"]),
                topics=sum_data.get("topics", [])
            ))

        return memory
