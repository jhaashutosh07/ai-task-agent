import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, AgentResult, ThoughtStep, AgentState
from llm.base import Message, ToolDefinition


class TaskDecomposition:
    """Represents a decomposed task with subtasks"""
    def __init__(self, original_task: str):
        self.original_task = original_task
        self.subtasks: List[Dict[str, Any]] = []
        self.dependencies: Dict[str, List[str]] = {}
        self.completed: Dict[str, AgentResult] = {}

    def add_subtask(self, task_id: str, description: str, agent: AgentRole, dependencies: List[str] = None):
        self.subtasks.append({
            "id": task_id,
            "description": description,
            "agent": agent,
            "status": "pending"
        })
        self.dependencies[task_id] = dependencies or []

    def get_ready_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks whose dependencies are all completed"""
        ready = []
        for task in self.subtasks:
            if task["status"] != "pending":
                continue
            deps = self.dependencies.get(task["id"], [])
            if all(d in self.completed for d in deps):
                ready.append(task)
        return ready

    def mark_completed(self, task_id: str, result: AgentResult):
        self.completed[task_id] = result
        for task in self.subtasks:
            if task["id"] == task_id:
                task["status"] = "completed" if result.success else "failed"
                break


class OrchestratorAgent(BaseAgent):
    """
    The Orchestrator Agent coordinates multiple specialized agents.
    It decomposes complex tasks, assigns them to appropriate agents,
    and synthesizes the results.
    """

    def __init__(self, llm, agents: Dict[AgentRole, BaseAgent] = None, tools: Dict[str, Any] = None):
        super().__init__(llm, tools)
        self.agents = agents or {}
        self.current_task: TaskDecomposition | None = None

    @property
    def role(self) -> AgentRole:
        return AgentRole.ORCHESTRATOR

    @property
    def system_prompt(self) -> str:
        available_agents = ", ".join([a.value for a in self.agents.keys()])
        return f"""You are an Orchestrator Agent - the central coordinator of a multi-agent AI system.

## Your Role
You decompose complex tasks into subtasks and delegate them to specialized agents:
- **researcher**: Web search, information gathering, reading websites
- **coder**: Writing, executing, and debugging code
- **analyst**: Data analysis, visualization, generating insights
- **executor**: System commands, file operations, automation

## Available Agents
{available_agents}

## How to Work
1. **Analyze** the user's request thoroughly
2. **Decompose** into logical subtasks with clear dependencies
3. **Delegate** each subtask to the most appropriate agent
4. **Coordinate** parallel execution when tasks are independent
5. **Synthesize** results into a coherent response
6. **Reflect** on the process and suggest improvements

## Task Decomposition Format
When decomposing, output JSON:
```json
{{
  "analysis": "Brief analysis of the task",
  "subtasks": [
    {{
      "id": "task_1",
      "description": "Clear description of subtask",
      "agent": "researcher|coder|analyst|executor",
      "dependencies": [],
      "reasoning": "Why this agent and this order"
    }}
  ],
  "execution_strategy": "parallel|sequential|mixed"
}}
```

## Guidelines
- Prefer parallel execution when tasks are independent
- Always validate critical operations with the user
- If a subtask fails, try to recover or find alternatives
- Maintain context between subtasks
- Provide clear progress updates

Current date: {datetime.now().strftime("%Y-%m-%d")}
"""

    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None,
        max_steps: int = 15
    ) -> AgentResult:
        """Execute a complex task by coordinating multiple agents"""
        start_time = datetime.now()
        self.state = AgentState.THINKING
        self.thoughts = []
        context = context or {}

        self.emit_event("orchestrator_start", {
            "task": task,
            "available_agents": [a.value for a in self.agents.keys()]
        })

        try:
            # Step 1: Analyze and decompose the task
            decomposition = await self._decompose_task(task, context)
            self.current_task = decomposition

            self.emit_event("task_decomposed", {
                "subtasks": [
                    {"id": t["id"], "description": t["description"], "agent": t["agent"].value}
                    for t in decomposition.subtasks
                ]
            })

            # Step 2: Execute subtasks
            step = 0
            while step < max_steps:
                ready_tasks = decomposition.get_ready_tasks()

                if not ready_tasks:
                    # Check if all tasks are done
                    if len(decomposition.completed) == len(decomposition.subtasks):
                        break
                    # Some tasks failed and blocked others
                    self.emit_event("execution_blocked", {
                        "completed": len(decomposition.completed),
                        "total": len(decomposition.subtasks)
                    })
                    break

                # Execute ready tasks (potentially in parallel)
                results = await self._execute_subtasks(ready_tasks, context)

                for task_id, result in results.items():
                    decomposition.mark_completed(task_id, result)
                    context[f"result_{task_id}"] = result.output

                step += 1

            # Step 3: Synthesize results
            final_output = await self._synthesize_results(task, decomposition, context)

            execution_time = (datetime.now() - start_time).total_seconds()

            self.emit_event("orchestrator_complete", {
                "success": True,
                "subtasks_completed": len(decomposition.completed),
                "execution_time": execution_time
            })

            return AgentResult(
                success=True,
                output=final_output,
                thoughts=self.thoughts,
                artifacts={"decomposition": decomposition},
                execution_time=execution_time
            )

        except Exception as e:
            self.state = AgentState.FAILED
            self.emit_event("orchestrator_error", {"error": str(e)})
            return AgentResult(
                success=False,
                output="",
                error=str(e),
                thoughts=self.thoughts
            )

    async def _decompose_task(self, task: str, context: Dict[str, Any]) -> TaskDecomposition:
        """Decompose a complex task into subtasks"""
        self.emit_event("decomposing", {"task": task})

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=f"""
Decompose this task into subtasks for the specialized agents:

Task: {task}

Context: {json.dumps(context) if context else "None"}

Respond with the JSON decomposition.
""")
        ]

        response = await self.llm.chat(messages)

        # Parse the decomposition
        try:
            # Extract JSON from response
            content = response.content
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                decomposition_data = json.loads(content[json_start:json_end])
            else:
                # Simple task - single agent
                decomposition_data = {
                    "subtasks": [{
                        "id": "task_1",
                        "description": task,
                        "agent": "researcher",
                        "dependencies": []
                    }]
                }
        except json.JSONDecodeError:
            decomposition_data = {
                "subtasks": [{
                    "id": "task_1",
                    "description": task,
                    "agent": "researcher",
                    "dependencies": []
                }]
            }

        decomposition = TaskDecomposition(task)

        for subtask in decomposition_data.get("subtasks", []):
            agent_str = subtask.get("agent", "researcher")
            try:
                agent_role = AgentRole(agent_str)
            except ValueError:
                agent_role = AgentRole.RESEARCHER

            decomposition.add_subtask(
                task_id=subtask.get("id", f"task_{len(decomposition.subtasks)}"),
                description=subtask.get("description", task),
                agent=agent_role,
                dependencies=subtask.get("dependencies", [])
            )

        self.thoughts.append(ThoughtStep(
            step_number=len(self.thoughts) + 1,
            thought=f"Decomposed task into {len(decomposition.subtasks)} subtasks",
            action="decompose",
            action_input={"subtasks": len(decomposition.subtasks)}
        ))

        return decomposition

    async def _execute_subtasks(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, AgentResult]:
        """Execute multiple subtasks, potentially in parallel"""
        results = {}

        # Group by whether they can run in parallel
        async def run_task(task: Dict[str, Any]) -> tuple:
            agent_role = task["agent"]
            if agent_role not in self.agents:
                return task["id"], AgentResult(
                    success=False,
                    output="",
                    error=f"No agent available for role: {agent_role}"
                )

            agent = self.agents[agent_role]

            self.emit_event("subtask_start", {
                "task_id": task["id"],
                "description": task["description"],
                "agent": agent_role.value
            })

            try:
                result = await agent.execute(task["description"], context)

                self.emit_event("subtask_complete", {
                    "task_id": task["id"],
                    "success": result.success,
                    "output_preview": result.output[:200] if result.output else ""
                })

                return task["id"], result
            except Exception as e:
                return task["id"], AgentResult(
                    success=False,
                    output="",
                    error=str(e)
                )

        # Run tasks in parallel
        task_results = await asyncio.gather(*[run_task(t) for t in tasks])

        for task_id, result in task_results:
            results[task_id] = result
            self.thoughts.append(ThoughtStep(
                step_number=len(self.thoughts) + 1,
                thought=f"Completed subtask {task_id}",
                action="delegate",
                observation=result.output[:200] if result.output else result.error
            ))

        return results

    async def _synthesize_results(
        self,
        original_task: str,
        decomposition: TaskDecomposition,
        context: Dict[str, Any]
    ) -> str:
        """Synthesize all subtask results into a coherent response"""
        self.emit_event("synthesizing", {"task": original_task})

        # Collect all results
        results_summary = []
        for subtask in decomposition.subtasks:
            if subtask["id"] in decomposition.completed:
                result = decomposition.completed[subtask["id"]]
                results_summary.append({
                    "task": subtask["description"],
                    "agent": subtask["agent"].value,
                    "success": result.success,
                    "output": result.output[:1000] if result.output else result.error
                })

        messages = [
            Message(role="system", content="""You are synthesizing results from multiple AI agents.
Create a coherent, well-structured response that addresses the original task.
Be concise but comprehensive. Use markdown formatting."""),
            Message(role="user", content=f"""
Original Task: {original_task}

Subtask Results:
{json.dumps(results_summary, indent=2)}

Synthesize these results into a clear, actionable response.
""")
        ]

        response = await self.llm.chat(messages)
        return response.content
