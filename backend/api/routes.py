from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, List, Dict, Any, Optional
from datetime import datetime

router = APIRouter()

# Global components reference
_components = {}


def set_components(components):
    global _components
    _components = components


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    use_orchestrator: bool = True


class ChatResponse(BaseModel):
    response: str
    events: List[Dict[str, Any]] = []
    execution_time: float = 0.0


class WorkflowCreateRequest(BaseModel):
    name: str
    description: str = ""
    steps: List[Dict[str, Any]]
    variables: Dict[str, Any] = {}
    tags: List[str] = []


class ScheduleRequest(BaseModel):
    workflow_id: str
    name: str
    trigger_type: str  # "cron", "interval", "date"
    trigger_config: Dict[str, Any]
    variables: Dict[str, Any] = {}


class SettingsResponse(BaseModel):
    llm_provider: str
    openai_model: str
    ollama_model: str
    openai_configured: bool
    ollama_available: bool
    tools_count: int
    agents_count: int


# Health & Info
@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/info")
async def get_info():
    return {
        "name": "AI Task Automation Agent",
        "version": "2.0.0",
        "tools": list(_components.get("tools", {}).keys()),
        "agents": ["orchestrator", "researcher", "coder", "analyst", "executor"],
        "features": {
            "multi_agent": True,
            "vector_memory": True,
            "workflows": True,
            "scheduling": True
        }
    }


# Chat
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    orchestrator = _components.get("orchestrator")
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    events = []
    start_time = datetime.now()

    def on_event(event):
        events.append(event.to_dict())

    orchestrator.add_event_handler(on_event)

    try:
        result = await orchestrator.execute(request.message)

        execution_time = (datetime.now() - start_time).total_seconds()

        # Store in memory
        vector_memory = _components.get("vector_memory")
        if vector_memory:
            await vector_memory.add(
                content=f"Task: {request.message}\nResult: {result.output[:500]}",
                memory_type="conversation"
            )

        return ChatResponse(
            response=result.output,
            events=events,
            execution_time=execution_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/clear")
async def clear_chat():
    conv_memory = _components.get("conversation_memory")
    if conv_memory:
        conv_memory.clear()
    return {"status": "ok", "message": "Conversation cleared"}


@router.get("/chat/history")
async def get_history():
    conv_memory = _components.get("conversation_memory")
    if not conv_memory:
        return {"history": []}
    return {"history": conv_memory.get_history()}


# Memory
@router.get("/memory/search")
async def search_memory(query: str, limit: int = 5):
    vector_memory = _components.get("vector_memory")
    if not vector_memory:
        return {"results": []}

    results = await vector_memory.search(query, n_results=limit)
    return {
        "results": [
            {
                "id": r.id,
                "content": r.content,
                "relevance": r.relevance_score,
                "metadata": r.metadata
            }
            for r in results
        ]
    }


@router.get("/memory/stats")
async def get_memory_stats():
    vector_memory = _components.get("vector_memory")
    knowledge_base = _components.get("knowledge_base")

    return {
        "vector_memory": vector_memory.get_stats() if vector_memory else {},
        "knowledge_base": knowledge_base.get_stats() if knowledge_base else {}
    }


# Knowledge Base
@router.post("/knowledge")
async def add_knowledge(
    title: str,
    content: str,
    category: str = "general",
    tags: List[str] = []
):
    kb = _components.get("knowledge_base")
    if not kb:
        raise HTTPException(status_code=500, detail="Knowledge base not initialized")

    entry_id = await kb.add(title, content, category, tags)
    return {"id": entry_id, "status": "created"}


@router.get("/knowledge/search")
async def search_knowledge(query: str, category: str = None, limit: int = 10):
    kb = _components.get("knowledge_base")
    if not kb:
        return {"results": []}

    results = await kb.search(query, category=category, limit=limit)
    return {
        "results": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content[:200],
                "category": r.category,
                "tags": r.tags
            }
            for r in results
        ]
    }


# Workflows
@router.post("/workflows")
async def create_workflow(request: WorkflowCreateRequest):
    manager = _components.get("workflow_manager")
    if not manager:
        raise HTTPException(status_code=500, detail="Workflow manager not initialized")

    workflow = await manager.create(
        name=request.name,
        description=request.description,
        steps=request.steps,
        variables=request.variables,
        tags=request.tags
    )

    return {"id": workflow.id, "name": workflow.name, "status": "created"}


@router.get("/workflows")
async def list_workflows(tags: str = None, search: str = None):
    manager = _components.get("workflow_manager")
    if not manager:
        return {"workflows": []}

    tag_list = tags.split(",") if tags else None
    workflows = await manager.list(tags=tag_list, search=search)

    return {
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "steps_count": len(w.steps),
                "tags": w.tags,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None
            }
            for w in workflows
        ]
    }


@router.get("/workflows/templates")
async def get_templates():
    manager = _components.get("workflow_manager")
    if not manager:
        return {"templates": []}

    templates = await manager.get_templates()
    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "steps_count": len(t.steps),
                "tags": t.tags
            }
            for t in templates
        ]
    }


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    manager = _components.get("workflow_manager")
    if not manager:
        raise HTTPException(status_code=500, detail="Workflow manager not initialized")

    workflow = await manager.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "version": workflow.version,
        "steps": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type.value,
                "config": s.config
            }
            for s in workflow.steps
        ],
        "variables": workflow.variables,
        "tags": workflow.tags
    }


@router.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str, variables: Dict[str, Any] = {}):
    manager = _components.get("workflow_manager")
    engine = _components.get("workflow_engine")

    if not manager or not engine:
        raise HTTPException(status_code=500, detail="Workflow system not initialized")

    workflow = await manager.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    execution = await engine.execute(workflow, initial_context=variables)

    return {
        "execution_id": execution.id,
        "status": execution.status,
        "steps_completed": len(execution.step_results)
    }


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    manager = _components.get("workflow_manager")
    if not manager:
        raise HTTPException(status_code=500, detail="Workflow manager not initialized")

    success = await manager.delete(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"status": "deleted"}


# Scheduling
@router.post("/schedule")
async def schedule_workflow(request: ScheduleRequest):
    scheduler = _components.get("scheduler")
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    task = await scheduler.schedule(
        workflow_id=request.workflow_id,
        name=request.name,
        trigger_type=request.trigger_type,
        trigger_config=request.trigger_config,
        variables=request.variables
    )

    if not task:
        raise HTTPException(status_code=400, detail="Failed to schedule workflow")

    return {
        "task_id": task.id,
        "next_run": task.next_run.isoformat() if task.next_run else None
    }


@router.get("/schedule")
async def list_scheduled_tasks():
    scheduler = _components.get("scheduler")
    if not scheduler:
        return {"tasks": []}

    tasks = await scheduler.list_tasks()
    return {
        "tasks": [
            {
                "id": t.id,
                "workflow_id": t.workflow_id,
                "name": t.name,
                "enabled": t.enabled,
                "last_run": t.last_run.isoformat() if t.last_run else None,
                "next_run": t.next_run.isoformat() if t.next_run else None,
                "run_count": t.run_count
            }
            for t in tasks
        ],
        "stats": scheduler.get_stats()
    }


@router.post("/schedule/{task_id}/pause")
async def pause_task(task_id: str):
    scheduler = _components.get("scheduler")
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    success = await scheduler.pause(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"status": "paused"}


@router.post("/schedule/{task_id}/resume")
async def resume_task(task_id: str):
    scheduler = _components.get("scheduler")
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    success = await scheduler.resume(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"status": "resumed"}


@router.delete("/schedule/{task_id}")
async def cancel_task(task_id: str):
    scheduler = _components.get("scheduler")
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    success = await scheduler.cancel(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"status": "cancelled"}


# Tools
@router.get("/tools")
async def list_tools():
    tools = _components.get("tools", {})
    return {
        "tools": [
            {
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for name, tool in tools.items()
        ]
    }


@router.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, params: Dict[str, Any] = {}):
    tools = _components.get("tools", {})
    if tool_name not in tools:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    tool = tools[tool_name]
    result = await tool.execute(**params)

    return {
        "success": result.success,
        "output": result.output,
        "error": result.error
    }


# Settings
@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    from config import settings

    ollama_available = False
    if settings.llm_provider == "ollama":
        ollama_available = True

    return SettingsResponse(
        llm_provider=settings.llm_provider,
        openai_model=settings.openai_model,
        ollama_model=settings.ollama_model,
        openai_configured=bool(settings.openai_api_key),
        ollama_available=ollama_available,
        tools_count=len(_components.get("tools", {})),
        agents_count=len(_components.get("agents", {}))
    )


# Files
@router.get("/files")
async def list_files(path: str = "."):
    tools = _components.get("tools", {})
    fm = tools.get("file_manager")
    if not fm:
        raise HTTPException(status_code=500, detail="File manager not initialized")

    result = await fm.execute(action="list", path=path)
    return {"success": result.success, "output": result.output, "error": result.error}


@router.get("/files/read")
async def read_file(path: str):
    tools = _components.get("tools", {})
    fm = tools.get("file_manager")
    if not fm:
        raise HTTPException(status_code=500, detail="File manager not initialized")

    result = await fm.execute(action="read", path=path)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)

    return {"success": True, "content": result.output}


# Analytics Endpoints
@router.get("/analytics/usage")
async def get_usage_analytics(days: int = 30):
    """Get usage statistics over time"""
    cost_tracker = _components.get("cost_tracker")
    if not cost_tracker:
        return {
            "total_requests": 0,
            "total_tokens": {"input": 0, "output": 0},
            "total_cost": 0.0,
            "daily_costs": {},
            "by_provider": {},
            "by_model": {}
        }

    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=days)
    summary = await cost_tracker.get_total_summary(since=since)
    daily_costs = await cost_tracker.get_daily_costs(days=days)

    return {
        "total_requests": summary.total_requests,
        "total_tokens": {
            "input": summary.total_input_tokens,
            "output": summary.total_output_tokens
        },
        "total_cost": round(summary.total_cost, 6),
        "daily_costs": daily_costs,
        "by_provider": {
            k: {
                "requests": summary.requests_by_provider.get(k, 0),
                "cost": round(summary.costs_by_provider.get(k, 0.0), 6)
            }
            for k in set(list(summary.requests_by_provider.keys()) + list(summary.costs_by_provider.keys()))
        },
        "by_model": summary.requests_by_model
    }


@router.get("/analytics/costs")
async def get_cost_analytics():
    """Get cost breakdown by provider"""
    cost_tracker = _components.get("cost_tracker")
    provider_manager = _components.get("provider_manager")

    result = {
        "current_costs_per_1k": {},
        "total_spent": 0.0,
        "by_provider": {}
    }

    if provider_manager:
        result["current_costs_per_1k"] = {
            name: {"input": costs[0], "output": costs[1]}
            for name, costs in provider_manager.get_cost_info().items()
        }

    if cost_tracker:
        summary = await cost_tracker.get_total_summary()
        result["total_spent"] = round(summary.total_cost, 6)
        result["by_provider"] = {
            k: round(v, 6)
            for k, v in summary.costs_by_provider.items()
        }

    return result


@router.get("/analytics/providers")
async def get_provider_status():
    """Get status of all LLM providers"""
    provider_manager = _components.get("provider_manager")
    if not provider_manager:
        return {
            "providers": [],
            "default": None,
            "fallback_chain": []
        }

    from config import settings

    health = await provider_manager.health_check()

    return {
        "providers": [
            {
                "name": name,
                "available": True,
                "healthy": health.get(name, False),
                "supports_vision": provider_manager.get_provider(name).supports_vision,
                "cost_per_1k": {
                    "input": provider_manager.get_provider(name).cost_per_1k_tokens[0],
                    "output": provider_manager.get_provider(name).cost_per_1k_tokens[1]
                }
            }
            for name in provider_manager.list_providers()
        ],
        "default": settings.llm_provider,
        "fallback_chain": settings.fallback_chain
    }


@router.get("/analytics/agent-activity")
async def get_agent_activity(limit: int = 100):
    """Get recent agent activity timeline"""
    cost_tracker = _components.get("cost_tracker")
    if not cost_tracker:
        return {"activities": []}

    records = await cost_tracker.get_recent_records(limit=limit)

    return {
        "activities": [
            {
                "timestamp": r.timestamp.isoformat(),
                "provider": r.provider,
                "model": r.model,
                "type": r.request_type,
                "tokens": {
                    "input": r.input_tokens,
                    "output": r.output_tokens
                },
                "cost": round(r.total_cost, 6)
            }
            for r in records
        ]
    }
