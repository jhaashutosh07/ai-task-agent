from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Literal, List, Dict, Any, Optional
from datetime import datetime

from .pipeline import run_chat, stream_chat

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
    citations: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {}
    execution_time: float = 0.0



class RAGQueryRequest(BaseModel):
    query: str
    n_results: int = 5

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


# Chat — unified intelligent pipeline (cache → route → RAG → agents → reflect)
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await run_chat(_components, request.message)
    return ChatResponse(
        response=result["response"],
        events=result.get("events", []),
        citations=result.get("citations", []),
        meta=result.get("meta", {}),
        execution_time=result.get("execution_time", 0.0),
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Server-Sent Events stream: emits meta, stage, step, token, citations, done."""
    return StreamingResponse(
        stream_chat(_components, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class CompareRequest(BaseModel):
    message: str
    providers: List[str] = []


@router.post("/compare")
async def compare_providers(request: CompareRequest):
    """Run the same prompt across multiple LLM providers concurrently and compare
    response, speed and (approx) cost — powers the model comparison playground."""
    import asyncio, time
    from llm.base import Message as LMessage

    pm = _components.get("provider_manager")
    if not pm:
        raise HTTPException(status_code=500, detail="Provider manager not initialized")

    names = [n for n in (request.providers or pm.list_providers()) if n in pm.list_providers()]

    async def run(name: str):
        t0 = time.time()
        try:
            p = pm.get_provider(name)
            # Local models on CPU (Ollama) are slower — give them more headroom.
            tmo = 85 if name == "ollama" else 45
            resp = await asyncio.wait_for(
                p.chat([LMessage(role="user", content=request.message)]), timeout=tmo
            )
            cost = getattr(p, "cost_per_1k_tokens", (0.0, 0.0)) or (0.0, 0.0)
            return {
                "provider": name,
                "model": getattr(p, "model", ""),
                "response": (resp.content or "").strip(),
                "latency_ms": round((time.time() - t0) * 1000),
                "cost_per_1k": {"input": cost[0], "output": cost[1]},
                "error": None,
            }
        except Exception as e:
            return {
                "provider": name, "model": getattr(pm.get_provider(name), "model", "") if name in pm.list_providers() else "",
                "response": "", "latency_ms": round((time.time() - t0) * 1000),
                "cost_per_1k": {"input": 0.0, "output": 0.0},
                "error": f"{type(e).__name__}: {e}"[:200],
            }

    results = await asyncio.gather(*[run(n) for n in names])
    results.sort(key=lambda r: (r["error"] is not None, r["latency_ms"]))
    return {"message": request.message, "results": results}


# ─── Vision (multimodal) ─────────────────────────────────────────────────────

@router.post("/vision")
async def vision_chat(
    prompt: str = Form("Describe this image in detail. Note any text, objects, and context."),
    file: UploadFile = File(...),
):
    """Analyse an uploaded image with a vision-capable model (GPT-4o)."""
    import base64
    pm = _components.get("provider_manager")
    if not pm or "openai" not in pm.list_providers():
        raise HTTPException(status_code=400, detail="Vision requires an OpenAI provider to be configured.")
    provider = pm.get_provider("openai")
    model = provider.model if getattr(provider, "supports_vision", False) else "gpt-4o-mini"
    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large (max 8MB).")
    b64 = base64.b64encode(content).decode()
    mime = file.content_type or "image/jpeg"
    try:
        resp = await provider.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ]}],
            max_tokens=900,
        )
        return {"response": resp.choices[0].message.content or "", "model": model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision request failed: {type(e).__name__}: {e}")


# ─── Knowledge Graph ─────────────────────────────────────────────────────────

@router.post("/knowledge-graph")
async def knowledge_graph(request: RAGQueryRequest = None):
    """Extract an entity–relationship knowledge graph from ingested documents."""
    import json as _json
    rag = _components.get("rag_pipeline")
    llm = _components.get("llm")
    if not rag or not llm:
        raise HTTPException(status_code=500, detail="RAG or LLM not initialised")

    query = (request.query if request else None) or "main topics, entities, people, and concepts"
    chunks = await rag.query(query, n_results=8)
    if not chunks:
        return {"nodes": [], "edges": [], "note": "No documents ingested yet."}

    text = "\n\n".join(c.content for c in chunks)[:6000]
    from llm.base import Message
    prompt = (
        "Extract a knowledge graph from the text below. Identify the key entities "
        "(people, organisations, concepts, technologies, places) and the relationships "
        "between them. Respond with ONLY valid JSON of the form:\n"
        '{"nodes":[{"id":"n1","label":"Name","type":"concept|person|org|tech|place"}],'
        '"edges":[{"source":"n1","target":"n2","label":"relationship"}]}\n'
        "Keep it to the 12 most important entities.\n\nText:\n" + text
    )
    try:
        resp = await llm.chat([Message(role="user", content=prompt)])
        raw = resp.content or ""
        s, e = raw.find("{"), raw.rfind("}") + 1
        data = _json.loads(raw[s:e]) if s >= 0 and e > s else {"nodes": [], "edges": []}
        return {
            "nodes": data.get("nodes", [])[:20],
            "edges": data.get("edges", [])[:40],
            "sources": len(chunks),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph extraction failed: {e}")


# ─── Smart Auto-Routing ──────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    message: str


@router.post("/route/preview")
async def route_preview(request: RouteRequest):
    """Classify a prompt's difficulty and pick the optimal model (cost-aware)."""
    from llm.base import Message
    llm = _components.get("llm")
    pm = _components.get("provider_manager")
    available = pm.list_providers() if pm else []

    complexity = "moderate"
    try:
        if llm:
            r = await llm.chat([Message(role="user", content=(
                "Classify the difficulty of answering this request as exactly one word: "
                "'simple' (greeting/definition/short factual), 'moderate' (explanation/short code), "
                "or 'complex' (multi-step reasoning, research, long code, analysis).\n\n"
                f"Request: {request.message}\n\nAnswer with one word only."
            ))])
            w = (r.content or "").strip().lower()
            complexity = "simple" if "simple" in w else "complex" if "complex" in w else "moderate"
    except Exception:
        pass

    # Preference order per tier (first available wins)
    tiers = {
        "simple":   ["groq", "cerebras", "gemini", "openai", "openrouter"],
        "moderate": ["openai", "groq", "gemini", "anthropic", "cerebras"],
        "complex":  ["anthropic", "openai", "openrouter", "gemini", "groq"],
    }
    chosen = next((p for p in tiers[complexity] if p in available), (available[0] if available else "openai"))
    model = getattr(pm.get_provider(chosen), "model", "") if pm and chosen in available else ""
    cost = getattr(pm.get_provider(chosen), "cost_per_1k_tokens", (0.0, 0.0)) if pm and chosen in available else (0.0, 0.0)
    reason = {
        "simple": "Lightweight query → routed to the fastest / cheapest capable model.",
        "moderate": "Standard query → balanced model for quality and cost.",
        "complex": "Hard multi-step task → routed to the strongest reasoning model.",
    }[complexity]
    return {
        "complexity": complexity,
        "chosen_provider": chosen,
        "chosen_model": model,
        "cost_per_1k": {"input": cost[0], "output": cost[1]},
        "is_free": chosen in {"groq", "openrouter", "cerebras", "gemini", "ollama"},
        "reason": reason,
    }


# ─── Answer Evaluation + Guardrails ──────────────────────────────────────────

class EvaluateRequest(BaseModel):
    question: str
    answer: str
    context: str = ""


_PII_PATTERNS = {
    "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "phone": r"\b(?:\+?\d[\d -]{8,}\d)\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
}
_JAILBREAK = [
    "ignore previous instructions", "ignore all previous", "disregard the above",
    "you are now", "developer mode", "jailbreak", "do anything now", "dan mode",
    "bypass your", "without any restrictions",
]


@router.post("/guardrails/check")
async def guardrails_check(request: RouteRequest):
    """Scan input text for PII and prompt-injection / jailbreak attempts."""
    import re as _re
    text = request.message or ""
    low = text.lower()
    pii = [name for name, pat in _PII_PATTERNS.items() if _re.search(pat, text)]
    jb = [p for p in _JAILBREAK if p in low]
    return {
        "safe": not jb,
        "pii_detected": pii,
        "jailbreak_flags": jb,
        "risk": "high" if jb else ("medium" if pii else "low"),
    }


@router.post("/evaluate")
async def evaluate_answer(request: EvaluateRequest):
    """LLM-as-judge: score an answer for faithfulness, relevance and completeness."""
    import json as _json
    from llm.base import Message
    llm = _components.get("llm")
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not initialised")
    ctx = f"\nReference context:\n{request.context}\n" if request.context else ""
    prompt = (
        "You are a strict evaluator. Score the assistant's answer on three axes from 1-5 "
        "(5 = excellent). Respond with ONLY JSON: "
        '{"faithfulness":n,"relevance":n,"completeness":n,"verdict":"one short sentence"}.\n'
        "faithfulness = supported by context / not hallucinated; relevance = answers the question; "
        "completeness = thorough.\n"
        f"\nQuestion:\n{request.question}\n{ctx}\nAnswer:\n{request.answer}\n"
    )
    try:
        r = await llm.chat([Message(role="user", content=prompt)])
        raw = r.content or ""
        s, e = raw.find("{"), raw.rfind("}") + 1
        data = _json.loads(raw[s:e]) if s >= 0 and e > s else {}
        scores = {k: float(data.get(k, 0)) for k in ("faithfulness", "relevance", "completeness")}
        overall = round(sum(scores.values()) / 3, 2) if scores else 0.0
        return {"scores": scores, "overall": overall, "verdict": data.get("verdict", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")


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

    try:
        health = await provider_manager.health_check()
    except Exception:
        health = {}

    providers = []
    for name in provider_manager.list_providers():
        p = provider_manager.get_provider(name)
        cost = getattr(p, "cost_per_1k_tokens", (0.0, 0.0)) or (0.0, 0.0)
        providers.append({
            "name": name,
            "available": True,
            "healthy": bool(health.get(name, False)),
            "supports_vision": bool(getattr(p, "supports_vision", False)),
            "cost_per_1k": {"input": cost[0], "output": cost[1]},
        })

    return {
        "providers": providers,
        "default": settings.llm_provider,
        "fallback_chain": settings.fallback_chain,
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

# ─── Observability & Cache ───────────────────────────────────────────────────

@router.get("/observability/traces")
async def get_traces(limit: int = 50):
    """Recent request traces (route, cache hit, RAG, latency, pipeline stages)."""
    tracer = _components.get("tracer")
    if not tracer:
        return {"traces": []}
    return {"traces": tracer.recent(limit=limit)}


@router.get("/observability/metrics")
async def get_obs_metrics():
    """Aggregate pipeline metrics for the observability dashboard."""
    tracer = _components.get("tracer")
    cache = _components.get("semantic_cache")
    metrics = tracer.metrics() if tracer else {}
    metrics["cache"] = cache.stats() if cache else {}
    return metrics


@router.get("/cache/stats")
async def cache_stats():
    cache = _components.get("semantic_cache")
    return cache.stats() if cache else {"enabled": False}


@router.post("/cache/clear")
async def cache_clear():
    cache = _components.get("semantic_cache")
    if not cache:
        return {"cleared": 0}
    return {"cleared": cache.clear()}


# ─── RAG Endpoints ────────────────────────────────────────────────────────────

@router.post("/rag/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """Upload a document (PDF, TXT, MD) and store it in the RAG vector DB."""
    rag = _components.get("rag_pipeline")
    if not rag:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    allowed = {".pdf", ".txt", ".md", ".html"}
    from pathlib import Path as _P
    if _P(file.filename).suffix.lower() not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed}")
    content = await file.read()
    try:
        result = await rag.ingest(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import traceback
        print("[RAG] ingest failed:\n" + traceback.format_exc(), flush=True)
        raise HTTPException(status_code=500, detail=f"Ingest failed: {type(e).__name__}: {e}")
    return result


@router.get("/rag/documents")
async def list_rag_documents():
    rag = _components.get("rag_pipeline")
    if not rag:
        return {"documents": []}
    return {"documents": await rag.list_documents()}


@router.delete("/rag/documents/{doc_id}")
async def delete_rag_document(doc_id: str):
    rag = _components.get("rag_pipeline")
    if not rag:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    ok = await rag.delete_document(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "doc_id": doc_id}


@router.post("/rag/query")
async def query_rag(request: RAGQueryRequest):
    rag = _components.get("rag_pipeline")
    if not rag:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    chunks = await rag.query(request.query, n_results=request.n_results)
    return {
        "query": request.query,
        "results": [
            {"id": c.id, "content": c.content, "score": round(c.score, 4),
             "filename": c.metadata.get("filename"), "chunk_index": c.metadata.get("chunk_index")}
            for c in chunks
        ]
    }


@router.get("/rag/stats")
async def get_rag_stats():
    rag = _components.get("rag_pipeline")
    if not rag:
        return {"documents": 0, "total_chunks": 0, "storage": "unavailable"}
    return await rag.get_stats()