import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid

from .workflow_engine import Workflow, WorkflowStep, StepType


class WorkflowManager:
    """
    Manages workflow storage, versioning, and templates.
    Allows creating, saving, loading, and sharing workflows.
    """

    def __init__(self, storage_path: str = "./data/workflows"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.workflows: Dict[str, Workflow] = {}
        self.templates: Dict[str, Workflow] = {}
        self._load_all()
        self._load_templates()

    def _load_all(self):
        """Load all workflows from storage"""
        for file_path in self.storage_path.glob("*.json"):
            if file_path.name.startswith("template_"):
                continue
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    workflow = self._dict_to_workflow(data)
                    self.workflows[workflow.id] = workflow
            except Exception as e:
                print(f"Error loading workflow {file_path}: {e}")

    def _load_templates(self):
        """Load workflow templates"""
        for file_path in self.storage_path.glob("template_*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    workflow = self._dict_to_workflow(data)
                    self.templates[workflow.id] = workflow
            except Exception as e:
                print(f"Error loading template {file_path}: {e}")

        # Add built-in templates
        self._add_builtin_templates()

    def _add_builtin_templates(self):
        """Add built-in workflow templates"""
        # Web Research Template
        self.templates["research_template"] = Workflow(
            id="research_template",
            name="Web Research Workflow",
            description="Search the web, gather information, and create a summary",
            steps=[
                WorkflowStep(
                    id="search",
                    name="Web Search",
                    type=StepType.TOOL,
                    config={"tool": "web_search", "params": {"query": "{query}"}}
                ),
                WorkflowStep(
                    id="browse",
                    name="Read Top Results",
                    type=StepType.LOOP,
                    config={
                        "items": "{search_output.results}",
                        "variable": "url",
                        "body": {"tool": "web_browser", "params": {"url": "{url}"}}
                    }
                ),
                WorkflowStep(
                    id="summarize",
                    name="Create Summary",
                    type=StepType.AGENT,
                    config={"agent": "researcher", "task": "Summarize the gathered information"}
                )
            ],
            tags=["research", "web", "template"]
        )

        # Data Processing Template
        self.templates["data_processing_template"] = Workflow(
            id="data_processing_template",
            name="Data Processing Workflow",
            description="Read data, process it, and generate a report",
            steps=[
                WorkflowStep(
                    id="read_data",
                    name="Read Data File",
                    type=StepType.TOOL,
                    config={"tool": "file_manager", "params": {"action": "read", "path": "{input_file}"}}
                ),
                WorkflowStep(
                    id="analyze",
                    name="Analyze Data",
                    type=StepType.AGENT,
                    config={"agent": "analyst", "task": "Analyze the data and create visualizations"}
                ),
                WorkflowStep(
                    id="save_report",
                    name="Save Report",
                    type=StepType.TOOL,
                    config={"tool": "file_manager", "params": {"action": "write", "path": "report.md", "content": "{analyze_output}"}}
                )
            ],
            tags=["data", "analysis", "template"]
        )

        # Automation Template
        self.templates["automation_template"] = Workflow(
            id="automation_template",
            name="System Automation Workflow",
            description="Execute shell commands and manage files",
            steps=[
                WorkflowStep(
                    id="check_status",
                    name="Check System Status",
                    type=StepType.TOOL,
                    config={"tool": "shell_execute", "params": {"command": "{status_command}"}}
                ),
                WorkflowStep(
                    id="conditional_action",
                    name="Conditional Action",
                    type=StepType.CONDITION,
                    config={
                        "condition": "check_status_output.success",
                        "then": {"tool": "shell_execute", "params": {"command": "{action_command}"}},
                        "else": {"tool": "shell_execute", "params": {"command": "{fallback_command}"}}
                    }
                )
            ],
            tags=["automation", "system", "template"]
        )

    def _workflow_to_dict(self, workflow: Workflow) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "type": step.type.value,
                    "config": step.config,
                    "inputs": step.inputs,
                    "condition": step.condition,
                    "on_error": step.on_error,
                    "max_retries": step.max_retries,
                    "timeout": step.timeout
                }
                for step in workflow.steps
            ],
            "variables": workflow.variables,
            "triggers": workflow.triggers,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            "created_by": workflow.created_by,
            "tags": workflow.tags
        }

    def _dict_to_workflow(self, data: Dict[str, Any]) -> Workflow:
        """Convert dictionary to workflow"""
        steps = []
        for step_data in data.get("steps", []):
            steps.append(WorkflowStep(
                id=step_data["id"],
                name=step_data["name"],
                type=StepType(step_data["type"]),
                config=step_data.get("config", {}),
                inputs=step_data.get("inputs", {}),
                condition=step_data.get("condition"),
                on_error=step_data.get("on_error", "fail"),
                max_retries=step_data.get("max_retries", 3),
                timeout=step_data.get("timeout", 300)
            ))

        return Workflow(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            steps=steps,
            variables=data.get("variables", {}),
            triggers=data.get("triggers", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            created_by=data.get("created_by", ""),
            tags=data.get("tags", [])
        )

    async def create(
        self,
        name: str,
        description: str = "",
        steps: List[Dict[str, Any]] = None,
        variables: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> Workflow:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())[:12]

        parsed_steps = []
        for step_data in (steps or []):
            parsed_steps.append(WorkflowStep(
                id=step_data.get("id", str(uuid.uuid4())[:8]),
                name=step_data["name"],
                type=StepType(step_data["type"]),
                config=step_data.get("config", {}),
                inputs=step_data.get("inputs", {}),
                condition=step_data.get("condition"),
                on_error=step_data.get("on_error", "fail")
            ))

        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            steps=parsed_steps,
            variables=variables or {},
            tags=tags or []
        )

        self.workflows[workflow_id] = workflow
        await self._save(workflow)

        return workflow

    async def _save(self, workflow: Workflow):
        """Save workflow to disk"""
        file_path = self.storage_path / f"{workflow.id}.json"
        with open(file_path, "w") as f:
            json.dump(self._workflow_to_dict(workflow), f, indent=2)

    async def get(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)

    async def update(
        self,
        workflow_id: str,
        name: str = None,
        description: str = None,
        steps: List[Dict[str, Any]] = None,
        variables: Dict[str, Any] = None
    ) -> Optional[Workflow]:
        """Update an existing workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        if name:
            workflow.name = name
        if description:
            workflow.description = description
        if variables:
            workflow.variables = variables
        if steps:
            workflow.steps = [
                WorkflowStep(
                    id=s.get("id", str(uuid.uuid4())[:8]),
                    name=s["name"],
                    type=StepType(s["type"]),
                    config=s.get("config", {}),
                    inputs=s.get("inputs", {})
                )
                for s in steps
            ]

        workflow.updated_at = datetime.now()
        workflow.version = self._increment_version(workflow.version)

        await self._save(workflow)
        return workflow

    def _increment_version(self, version: str) -> str:
        """Increment version number"""
        parts = version.split(".")
        if len(parts) == 2:
            parts[1] = str(int(parts[1]) + 1)
        return ".".join(parts)

    async def delete(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if workflow_id not in self.workflows:
            return False

        del self.workflows[workflow_id]

        file_path = self.storage_path / f"{workflow_id}.json"
        if file_path.exists():
            file_path.unlink()

        return True

    async def list(
        self,
        tags: List[str] = None,
        search: str = None
    ) -> List[Workflow]:
        """List workflows with optional filtering"""
        results = list(self.workflows.values())

        if tags:
            results = [w for w in results if any(t in w.tags for t in tags)]

        if search:
            search_lower = search.lower()
            results = [
                w for w in results
                if search_lower in w.name.lower() or search_lower in w.description.lower()
            ]

        return sorted(results, key=lambda w: w.updated_at or w.created_at, reverse=True)

    async def get_templates(self) -> List[Workflow]:
        """Get all workflow templates"""
        return list(self.templates.values())

    async def create_from_template(
        self,
        template_id: str,
        name: str,
        variables: Dict[str, Any] = None
    ) -> Optional[Workflow]:
        """Create a new workflow from a template"""
        template = self.templates.get(template_id)
        if not template:
            return None

        return await self.create(
            name=name,
            description=template.description,
            steps=[
                {
                    "id": step.id,
                    "name": step.name,
                    "type": step.type.value,
                    "config": step.config,
                    "inputs": step.inputs
                }
                for step in template.steps
            ],
            variables={**template.variables, **(variables or {})},
            tags=template.tags
        )

    async def export(self, workflow_id: str) -> Optional[str]:
        """Export workflow as JSON string"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        return json.dumps(self._workflow_to_dict(workflow), indent=2)

    async def import_workflow(self, json_str: str) -> Workflow:
        """Import workflow from JSON string"""
        data = json.loads(json_str)
        # Generate new ID to avoid conflicts
        data["id"] = str(uuid.uuid4())[:12]
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()

        workflow = self._dict_to_workflow(data)
        self.workflows[workflow.id] = workflow
        await self._save(workflow)

        return workflow
