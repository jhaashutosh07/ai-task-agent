import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from pydantic import BaseModel
import uuid
from simpleeval import simple_eval, EvalWithCompoundTypes

logger = logging.getLogger(__name__)


class StepType(str, Enum):
    TOOL = "tool"           # Execute a tool
    AGENT = "agent"         # Delegate to an agent
    CONDITION = "condition" # Conditional branching
    LOOP = "loop"           # Loop over items
    PARALLEL = "parallel"   # Parallel execution
    WAIT = "wait"           # Wait for user input or time
    TRANSFORM = "transform" # Transform data


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep(BaseModel):
    """A single step in a workflow"""
    id: str
    name: str
    type: StepType
    config: Dict[str, Any] = {}
    inputs: Dict[str, str] = {}  # Maps input names to source (e.g., "step1.output")
    condition: Optional[str] = None  # Expression for conditional execution
    on_error: str = "fail"  # "fail", "skip", "retry"
    max_retries: int = 3
    timeout: int = 300  # seconds
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Workflow(BaseModel):
    """A complete workflow definition"""
    id: str
    name: str
    description: str = ""
    version: str = "1.0"
    steps: List[WorkflowStep] = []
    variables: Dict[str, Any] = {}  # Global variables
    triggers: List[Dict[str, Any]] = []  # Trigger conditions
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = ""
    tags: List[str] = []

    def __init__(self, **data):
        super().__init__(**data)
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc)


class WorkflowExecution(BaseModel):
    """A single execution of a workflow"""
    id: str
    workflow_id: str
    status: str = "running"  # running, completed, failed, cancelled
    current_step: int = 0
    started_at: datetime = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = {}  # Runtime context/variables
    step_results: Dict[str, Any] = {}
    error: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc)


class WorkflowEngine:
    """
    Engine for executing workflows.
    Supports sequential, parallel, conditional, and loop-based execution.
    """

    def __init__(self, tools: Dict[str, Any] = None, agents: Dict[str, Any] = None):
        self.tools = tools or {}
        self.agents = agents or {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.event_handlers: List[Callable] = []

    def add_event_handler(self, handler: Callable):
        self.event_handlers.append(handler)

    def emit_event(self, event_type: str, data: Dict[str, Any]):
        for handler in self.event_handlers:
            try:
                handler({"type": event_type, "data": data})
            except Exception as e:
                logger.warning(f"Event handler failed for '{event_type}': {e}")

    async def execute(
        self,
        workflow: Workflow,
        initial_context: Dict[str, Any] = None
    ) -> WorkflowExecution:
        """Execute a workflow"""
        execution = WorkflowExecution(
            id=str(uuid.uuid4())[:12],
            workflow_id=workflow.id,
            context={**workflow.variables, **(initial_context or {})}
        )
        self.executions[execution.id] = execution

        self.emit_event("workflow_started", {
            "execution_id": execution.id,
            "workflow_id": workflow.id,
            "workflow_name": workflow.name
        })

        try:
            for i, step in enumerate(workflow.steps):
                execution.current_step = i

                # Check condition
                if step.condition and not self._evaluate_condition(step.condition, execution.context):
                    step.status = StepStatus.SKIPPED
                    self.emit_event("step_skipped", {
                        "step_id": step.id,
                        "reason": "condition_not_met"
                    })
                    continue

                # Execute step
                step.status = StepStatus.RUNNING
                step.started_at = datetime.now(timezone.utc)

                self.emit_event("step_started", {
                    "step_id": step.id,
                    "step_name": step.name,
                    "step_type": step.type
                })

                try:
                    result = await self._execute_step(step, execution)
                    step.status = StepStatus.COMPLETED
                    step.result = result
                    execution.step_results[step.id] = result

                    # Update context with step output
                    if result:
                        execution.context[f"{step.id}_output"] = result

                    self.emit_event("step_completed", {
                        "step_id": step.id,
                        "result_preview": str(result)[:200] if result else None
                    })

                except Exception as e:
                    step.error = str(e)

                    if step.on_error == "skip":
                        step.status = StepStatus.SKIPPED
                        self.emit_event("step_skipped", {
                            "step_id": step.id,
                            "reason": str(e)
                        })
                    elif step.on_error == "retry" and step.max_retries > 0:
                        # Retry logic with exponential backoff
                        for retry in range(step.max_retries):
                            try:
                                await asyncio.sleep(2 ** retry)  # Exponential backoff
                                result = await self._execute_step(step, execution)
                                step.status = StepStatus.COMPLETED
                                step.result = result
                                break
                            except Exception as retry_error:
                                logger.warning(f"Step {step.id} retry {retry + 1}/{step.max_retries} failed: {retry_error}")
                                if retry == step.max_retries - 1:
                                    raise
                    else:
                        step.status = StepStatus.FAILED
                        raise

                step.completed_at = datetime.now(timezone.utc)

            execution.status = "completed"
            execution.completed_at = datetime.now(timezone.utc)

            self.emit_event("workflow_completed", {
                "execution_id": execution.id,
                "duration": (execution.completed_at - execution.started_at).total_seconds()
            })

        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.now(timezone.utc)

            self.emit_event("workflow_failed", {
                "execution_id": execution.id,
                "error": str(e)
            })

        return execution

    async def _execute_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""
        # Resolve inputs
        resolved_inputs = {}
        for input_name, source in step.inputs.items():
            resolved_inputs[input_name] = self._resolve_reference(source, execution.context)

        # Merge with config
        step_config = {**step.config, **resolved_inputs}

        if step.type == StepType.TOOL:
            return await self._execute_tool_step(step_config, execution)

        elif step.type == StepType.AGENT:
            return await self._execute_agent_step(step_config, execution)

        elif step.type == StepType.PARALLEL:
            return await self._execute_parallel_step(step_config, execution)

        elif step.type == StepType.LOOP:
            return await self._execute_loop_step(step_config, execution)

        elif step.type == StepType.CONDITION:
            return await self._execute_condition_step(step_config, execution)

        elif step.type == StepType.TRANSFORM:
            return await self._execute_transform_step(step_config, execution)

        elif step.type == StepType.WAIT:
            return await self._execute_wait_step(step_config, execution)

        else:
            raise ValueError(f"Unknown step type: {step.type}")

    async def _execute_tool_step(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute a tool"""
        tool_name = config.get("tool")
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool = self.tools[tool_name]
        params = config.get("params", {})

        result = await tool.execute(**params)

        return {
            "success": result.success,
            "output": result.output,
            "error": result.error
        }

    async def _execute_agent_step(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute an agent"""
        agent_name = config.get("agent")
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent = self.agents[agent_name]
        task = config.get("task", "")

        result = await agent.execute(task, context=execution.context)

        return {
            "success": result.success,
            "output": result.output,
            "artifacts": result.artifacts
        }

    async def _execute_parallel_step(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute multiple operations in parallel"""
        tasks = config.get("tasks", [])

        async def run_task(task_config):
            if task_config.get("type") == "tool":
                return await self._execute_tool_step(task_config, execution)
            elif task_config.get("type") == "agent":
                return await self._execute_agent_step(task_config, execution)
            return {"error": "Unknown task type"}

        results = await asyncio.gather(*[run_task(t) for t in tasks])

        return {"results": results}

    async def _execute_loop_step(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute a loop over items"""
        items = config.get("items", [])
        loop_var = config.get("variable", "item")
        loop_body = config.get("body", {})

        results = []
        for item in items:
            execution.context[loop_var] = item
            result = await self._execute_tool_step(loop_body, execution)
            results.append(result)

        return {"results": results}

    async def _execute_condition_step(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute conditional logic"""
        condition = config.get("condition", "")
        then_branch = config.get("then", {})
        else_branch = config.get("else", {})

        if self._evaluate_condition(condition, execution.context):
            return await self._execute_tool_step(then_branch, execution)
        elif else_branch:
            return await self._execute_tool_step(else_branch, execution)

        return {"skipped": True}

    async def _execute_transform_step(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Transform data"""
        transform_type = config.get("transform", "")
        input_data = config.get("input")

        if transform_type == "json_parse":
            return {"result": json.loads(input_data)}
        elif transform_type == "json_stringify":
            return {"result": json.dumps(input_data)}
        elif transform_type == "extract":
            key = config.get("key", "")
            if isinstance(input_data, dict):
                return {"result": input_data.get(key)}
        elif transform_type == "template":
            template = config.get("template", "")
            return {"result": template.format(**execution.context)}

        return {"result": input_data}

    async def _execute_wait_step(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Wait for a specified time or condition"""
        wait_type = config.get("type", "time")

        if wait_type == "time":
            seconds = config.get("seconds", 1)
            await asyncio.sleep(seconds)
            return {"waited": seconds}

        elif wait_type == "condition":
            condition = config.get("condition", "")
            timeout = config.get("timeout", 60)
            interval = config.get("interval", 1)

            elapsed = 0
            while elapsed < timeout:
                if self._evaluate_condition(condition, execution.context):
                    return {"condition_met": True, "elapsed": elapsed}
                await asyncio.sleep(interval)
                elapsed += interval

            return {"condition_met": False, "timeout": True}

        return {}

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate a condition expression using simpleeval"""
        try:
            # Use simpleeval for safe expression evaluation
            # Supports: comparisons, boolean ops, arithmetic, attribute access
            evaluator = EvalWithCompoundTypes(names=context)
            result = evaluator.eval(condition)
            return bool(result)
        except (ValueError, TypeError, SyntaxError, KeyError) as e:
            logger.warning(f"Condition evaluation failed for '{condition}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error evaluating condition '{condition}': {e}")
            return False

    def _resolve_reference(self, reference: str, context: Dict[str, Any]) -> Any:
        """Resolve a reference like 'step1.output.data' from context"""
        parts = reference.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID"""
        return self.executions.get(execution_id)

    async def cancel(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        execution = self.executions.get(execution_id)
        if execution and execution.status == "running":
            execution.status = "cancelled"
            execution.completed_at = datetime.now(timezone.utc)
            return True
        return False
