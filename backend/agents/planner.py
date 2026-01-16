"""
Planner Agent - Task decomposition and planning specialist
"""
from typing import Dict, Any, Optional
import json
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, AgentResult, ThoughtStep, AgentState
from llm.base import Message


class PlannerAgent(BaseAgent):
    """
    Task decomposition and planning specialist.

    Capabilities:
    - Break down complex tasks into actionable steps
    - Identify dependencies between tasks
    - Estimate complexity and suggest approaches
    - Create structured execution plans
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.ORCHESTRATOR

    @property
    def system_prompt(self) -> str:
        return """You are a Planning Agent specialized in task decomposition and strategic planning.

Your expertise includes:
1. Breaking down complex tasks into smaller, manageable steps
2. Identifying dependencies between tasks
3. Estimating task complexity
4. Creating structured execution plans
5. Identifying potential risks and mitigation strategies

When given a task, you should:
1. Analyze the overall objective
2. Identify the main components and sub-tasks
3. Determine the order of execution
4. Identify any dependencies or prerequisites
5. Create a clear, actionable plan

Output Format:
Always structure your plans as JSON with the following format:
{
    "objective": "The main goal",
    "complexity": "low|medium|high",
    "steps": [
        {
            "id": 1,
            "name": "Step name",
            "description": "What to do",
            "agent": "suggested agent (researcher/coder/analyst/executor)",
            "tools": ["suggested tools"],
            "dependencies": [],
            "estimated_effort": "low|medium|high"
        }
    ],
    "risks": ["potential issues"],
    "success_criteria": ["how to verify completion"]
}

Be thorough but practical. Focus on actionable steps that can be executed by the available agents."""

    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None,
        max_steps: int = 5
    ) -> AgentResult:
        """
        Create an execution plan for a given task.
        """
        start_time = datetime.now()
        self.state = AgentState.THINKING
        self.thoughts = []
        context = context or {}

        self.emit_event("planner_start", {"task": task[:100]})

        try:
            # Build the planning prompt
            messages = [
                Message(role="system", content=self.system_prompt),
                Message(role="user", content=f"""Please create a detailed execution plan for the following task:

Task: {task}

{f"Context: {json.dumps(context)}" if context else ""}

Available agents:
- Researcher: Web search, content extraction, PDF reading
- Coder: Code writing, execution, debugging
- Analyst: Data analysis, visualization, reporting
- Executor: System commands, file operations, API calls

Available tools: {list(self.tools.keys())}

Create a structured plan in JSON format.""")
            ]

            self.emit_event("planner_thinking", {"action": "creating_plan"})

            # Get LLM response
            response = await self.llm.chat(messages)

            # Record thought
            thought_step = ThoughtStep(
                step_number=1,
                thought="Analyzing task and creating execution plan",
                action="plan_creation",
                observation=f"Generated plan of length {len(response.content)}"
            )
            self.thoughts.append(thought_step)

            # Try to parse as JSON
            plan = None
            try:
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                plan = json.loads(content.strip())
            except json.JSONDecodeError:
                pass

            execution_time = (datetime.now() - start_time).total_seconds()
            self.state = AgentState.COMPLETED

            self.emit_event("planner_complete", {
                "plan_created": plan is not None,
                "execution_time": execution_time
            })

            return AgentResult(
                success=True,
                output=response.content,
                thoughts=self.thoughts,
                artifacts={"plan": plan} if plan else {},
                execution_time=execution_time
            )

        except Exception as e:
            self.state = AgentState.FAILED
            execution_time = (datetime.now() - start_time).total_seconds()

            self.emit_event("planner_error", {"error": str(e)})

            return AgentResult(
                success=False,
                output=f"Planning failed: {str(e)}",
                error=str(e),
                thoughts=self.thoughts,
                execution_time=execution_time
            )

    async def refine_plan(
        self,
        original_plan: Dict[str, Any],
        feedback: str
    ) -> AgentResult:
        """
        Refine an existing plan based on feedback.
        """
        task = f"""Please refine the following execution plan based on the provided feedback:

Original Plan:
{json.dumps(original_plan, indent=2)}

Feedback:
{feedback}

Update the plan to address the feedback while maintaining the JSON structure."""

        return await self.execute(task)

    async def estimate_complexity(self, task: str) -> Dict[str, Any]:
        """
        Estimate the complexity of a task without creating a full plan.
        """
        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=f"""Quickly estimate the complexity of this task:

Task: {task}

Respond with a brief JSON:
{{
    "complexity": "low|medium|high",
    "estimated_steps": <number>,
    "main_challenges": ["challenge1", "challenge2"],
    "recommended_approach": "brief suggestion"
}}""")
        ]

        response = await self.llm.chat(messages)

        try:
            content = response.content
            if "```" in content:
                content = content.split("```")[1].split("```")[0]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())
        except:
            return {
                "complexity": "unknown",
                "estimated_steps": 0,
                "main_challenges": [],
                "recommended_approach": response.content
            }
