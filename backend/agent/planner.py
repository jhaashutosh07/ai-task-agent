from typing import List, Dict, Any
from pydantic import BaseModel


class TaskStep(BaseModel):
    """Represents a single step in a task plan"""
    step_number: int
    description: str
    tool: str | None = None
    status: str = "pending"  # pending, in_progress, completed, failed
    result: str | None = None


class TaskPlan(BaseModel):
    """Represents a complete task plan"""
    task: str
    steps: List[TaskStep]
    current_step: int = 0
    status: str = "planning"  # planning, executing, completed, failed


class TaskPlanner:
    """Plans and tracks multi-step tasks"""

    def __init__(self):
        self.current_plan: TaskPlan | None = None

    def create_plan(self, task: str, steps: List[Dict[str, Any]]) -> TaskPlan:
        """Create a new task plan"""
        task_steps = [
            TaskStep(
                step_number=i + 1,
                description=step.get("description", ""),
                tool=step.get("tool")
            )
            for i, step in enumerate(steps)
        ]

        self.current_plan = TaskPlan(
            task=task,
            steps=task_steps,
            status="executing"
        )
        return self.current_plan

    def get_current_step(self) -> TaskStep | None:
        """Get the current step being executed"""
        if not self.current_plan:
            return None

        if self.current_plan.current_step >= len(self.current_plan.steps):
            return None

        return self.current_plan.steps[self.current_plan.current_step]

    def advance_step(self, result: str | None = None, success: bool = True) -> TaskStep | None:
        """Mark current step as done and move to next"""
        if not self.current_plan:
            return None

        current = self.get_current_step()
        if current:
            current.status = "completed" if success else "failed"
            current.result = result
            self.current_plan.current_step += 1

        # Check if plan is complete
        if self.current_plan.current_step >= len(self.current_plan.steps):
            self.current_plan.status = "completed"
            return None

        # Return next step
        next_step = self.get_current_step()
        if next_step:
            next_step.status = "in_progress"
        return next_step

    def get_plan_summary(self) -> Dict[str, Any]:
        """Get a summary of the current plan"""
        if not self.current_plan:
            return {"status": "no_plan"}

        completed = sum(1 for s in self.current_plan.steps if s.status == "completed")
        return {
            "task": self.current_plan.task,
            "status": self.current_plan.status,
            "total_steps": len(self.current_plan.steps),
            "completed_steps": completed,
            "current_step": self.current_plan.current_step + 1,
            "steps": [
                {
                    "number": s.step_number,
                    "description": s.description,
                    "status": s.status,
                    "tool": s.tool
                }
                for s in self.current_plan.steps
            ]
        }

    def clear(self) -> None:
        """Clear the current plan"""
        self.current_plan = None
