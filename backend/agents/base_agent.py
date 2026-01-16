from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, List, Dict
from pydantic import BaseModel
from datetime import datetime
import uuid


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"  # Coordinates other agents
    RESEARCHER = "researcher"       # Web search and information gathering
    CODER = "coder"                # Code generation and execution
    ANALYST = "analyst"            # Data analysis and visualization
    EXECUTOR = "executor"          # System commands and automation


class AgentState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentEvent(BaseModel):
    """Event emitted during agent execution"""
    id: str = ""
    timestamp: datetime = None
    agent_role: AgentRole = AgentRole.ORCHESTRATOR
    event_type: str = ""
    data: Dict[str, Any] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "agent": self.agent_role.value,
            "type": self.event_type,
            "data": self.data
        }


class ThoughtStep(BaseModel):
    """A single step in the agent's reasoning"""
    step_number: int
    thought: str
    action: str | None = None
    action_input: Dict[str, Any] | None = None
    observation: str | None = None
    reflection: str | None = None


class AgentResult(BaseModel):
    """Result from an agent execution"""
    success: bool
    output: str
    thoughts: List[ThoughtStep] = []
    artifacts: Dict[str, Any] = {}  # Files, data, etc.
    error: str | None = None
    execution_time: float = 0.0


class BaseAgent(ABC):
    """Abstract base class for all specialized agents"""

    def __init__(self, llm, tools: Dict[str, Any] = None):
        self.llm = llm
        self.tools = tools or {}
        self.state = AgentState.IDLE
        self.thoughts: List[ThoughtStep] = []
        self.event_handlers: List[Callable[[AgentEvent], Any]] = []

    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """The role of this agent"""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining agent behavior"""
        pass

    @property
    def available_tools(self) -> List[str]:
        """Tools this agent can use"""
        return list(self.tools.keys())

    def add_event_handler(self, handler: Callable[[AgentEvent], Any]):
        """Add an event handler"""
        self.event_handlers.append(handler)

    def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all handlers"""
        event = AgentEvent(
            agent_role=self.role,
            event_type=event_type,
            data=data
        )
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception:
                pass
        return event

    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None,
        max_steps: int = 10
    ) -> AgentResult:
        """Execute a task and return the result"""
        pass

    async def reflect(self, task: str, result: AgentResult) -> str:
        """Reflect on the execution and suggest improvements"""
        if not result.thoughts:
            return ""

        reflection_prompt = f"""
Analyze the execution of this task and provide insights:

Task: {task}
Success: {result.success}
Output: {result.output[:500]}

Thought Process:
{self._format_thoughts(result.thoughts)}

Provide a brief reflection on:
1. What went well
2. What could be improved
3. Key learnings for similar future tasks
"""
        # This would call the LLM for reflection
        return ""

    def _format_thoughts(self, thoughts: List[ThoughtStep]) -> str:
        """Format thoughts for display"""
        lines = []
        for t in thoughts:
            lines.append(f"Step {t.step_number}: {t.thought}")
            if t.action:
                lines.append(f"  Action: {t.action}")
            if t.observation:
                lines.append(f"  Observation: {t.observation[:200]}...")
        return "\n".join(lines)
