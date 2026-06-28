"""
Unified Chat Pipeline
=====================
A single intelligent path used by both `/chat` (JSON) and `/chat/stream` (SSE):

    semantic cache → intent routing → RAG retrieval (hybrid + citations)
        → conversational fast-path OR multi-agent orchestration
        → self-reflection → cache write → trace

The streaming variant emits granular SSE events (stage / token / citation /
done) so the UI can show live agent activity and token-by-token output.
"""
import asyncio
import json
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

from llm.base import Message

CONVERSATIONAL_SYSTEM = (
    "You are Nexus AI, a friendly and knowledgeable multi-agent assistant. "
    "Answer conversationally, accurately, and concisely. Use markdown when it helps. "
    "If the user message includes document context with [n] sources, ground your "
    "answer in that context and cite the relevant sources inline using [n] markers."
)

_TOKEN_SPLIT = re.compile(r"(\S+\s*)")


def _chunk_text(text: str) -> List[str]:
    """Split text into word-ish tokens (keeping trailing spaces) for a typing effect."""
    return _TOKEN_SPLIT.findall(text) or [text]


def _friendly_error(error: Optional[str], events: List[Dict[str, Any]]) -> str:
    raw = error or ""
    if not raw:
        for ev in reversed(events):
            if ev.get("type", "").endswith("_error"):
                raw = str(ev.get("data", {}).get("error", ""))
                break
    low = raw.lower()
    if "credit balance is too low" in low or "billing" in low:
        return ("⚠️ **The AI provider account is out of credits.** Add credits or switch "
                "`LLM_PROVIDER` to another configured provider, then try again.")
    if "rate limit" in low or "429" in low:
        return "⚠️ The AI provider is rate-limiting requests right now. Please wait a moment and retry."
    if any(s in low for s in ("authentication", "invalid x-api-key", "401", "api key")):
        return "⚠️ The AI provider rejected the API key. Please check the backend credentials."
    if raw:
        return f"⚠️ The request could not be completed: {raw}"
    return "⚠️ The agent could not produce a response. Please try rephrasing."


async def _conversational_answer(
    components: Dict[str, Any], message: str, context: str, stream: bool
):
    """Return a full string (stream=False) or an async token generator (stream=True)."""
    llm = components["llm"]
    user_content = message
    if context:
        user_content = f"{context}\n\nUser question: {message}"
    messages = [
        Message(role="system", content=CONVERSATIONAL_SYSTEM),
        Message(role="user", content=user_content),
    ]
    if stream:
        return await llm.chat(messages, stream=True)
    resp = await llm.chat(messages)
    return resp.content or ""


# ─────────────────────────────────────────────────────────────────────────────
# Non-streaming pipeline (JSON)
# ─────────────────────────────────────────────────────────────────────────────
async def run_chat(components: Dict[str, Any], message: str) -> Dict[str, Any]:
    from config import settings

    tracer = components.get("tracer")
    trace = tracer.start(message) if tracer else None

    cache = components.get("semantic_cache")
    router = components.get("intent_router")
    rag = components.get("rag_pipeline")
    reflector = components.get("reflection_engine")

    events: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []

    # 1) Semantic cache
    if cache:
        hit = cache.get(message)
        if hit:
            if trace:
                trace.intent = "cache"
                trace.cache_hit = True
                trace.stage("cache_hit", similarity=hit["similarity"])
                trace.finish("ok")
                tracer.record(trace)
            return {
                "response": hit["response"],
                "events": [], "citations": [],
                "meta": {"cache_hit": True, "similarity": hit["similarity"], "intent": "cache",
                         "trace_id": trace.id if trace else None},
                "execution_time": trace.latency_ms / 1000 if trace else 0.0,
            }

    # 2) Intent routing
    intent = await router.classify(message) if router else None
    intent_val = intent.value if intent else "task"
    if trace:
        trace.intent = intent_val
        trace.stage("classified", intent=intent_val)

    # 3) RAG retrieval (hybrid + citations)
    context = ""
    if rag:
        context, citations = await rag.retrieve_with_citations(message)
        if trace and citations:
            trace.used_rag = True
            trace.citations = len(citations)
            trace.stage("retrieved", sources=len(citations))

    reflected = False
    try:
        if intent_val == "chat":
            if trace:
                trace.stage("generating")
            answer = await _conversational_answer(components, message, context, stream=False)
            answer = (answer or "").strip()
        else:
            orchestrator = components.get("orchestrator")
            if not orchestrator:
                answer = _friendly_error("Orchestrator not initialized", events)
            else:
                def on_event(ev):
                    events.append(ev.to_dict())
                orchestrator.event_handlers = [on_event]
                if trace:
                    trace.stage("orchestrating")
                augmented = f"{context}\n\nUser question: {message}" if context else message
                result = await orchestrator.execute(augmented)
                answer = (result.output or "").strip() or _friendly_error(
                    getattr(result, "error", None), events)

        # 4) Self-reflection (bounded single pass)
        if reflector and getattr(settings, "enable_reflection", True) and answer and not answer.startswith("⚠️") and len(answer) > 40:
            if trace:
                trace.stage("reflecting")
            answer, critique = await reflector.refine(message, answer, context)
            reflected = critique not in ("", "OK")
            if trace:
                trace.reflected = reflected

        # 5) Cache write (skip errors)
        if cache and answer and not answer.startswith("⚠️"):
            cache.set(message, answer)

        # Memory
        vm = components.get("vector_memory")
        if vm and answer and not answer.startswith("⚠️"):
            try:
                await vm.add(content=f"Task: {message}\nResult: {answer[:500]}", memory_type="conversation")
            except Exception:
                pass

        if trace:
            trace.provider = settings.llm_provider
            trace.finish("ok")
            tracer.record(trace)

        return {
            "response": answer,
            "events": events,
            "citations": citations,
            "meta": {"cache_hit": False, "intent": intent_val, "reflected": reflected,
                     "used_rag": bool(citations), "trace_id": trace.id if trace else None},
            "execution_time": trace.latency_ms / 1000 if trace else 0.0,
        }
    except Exception as e:
        if trace:
            trace.finish("error")
            tracer.record(trace)
        return {
            "response": _friendly_error(str(e), events),
            "events": events, "citations": citations,
            "meta": {"cache_hit": False, "intent": intent_val, "trace_id": trace.id if trace else None},
            "execution_time": 0.0,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Streaming pipeline (SSE)
# ─────────────────────────────────────────────────────────────────────────────
def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_chat(components: Dict[str, Any], message: str) -> AsyncGenerator[str, None]:
    from config import settings

    tracer = components.get("tracer")
    trace = tracer.start(message) if tracer else None
    cache = components.get("semantic_cache")
    router = components.get("intent_router")
    rag = components.get("rag_pipeline")

    full_answer = ""
    citations: List[Dict[str, Any]] = []

    try:
        # 1) Cache
        if cache:
            hit = cache.get(message)
            if hit:
                if trace:
                    trace.intent = "cache"; trace.cache_hit = True
                    trace.finish("ok"); tracer.record(trace)
                yield _sse("meta", {"cache_hit": True, "similarity": hit["similarity"],
                                    "intent": "cache", "trace_id": trace.id if trace else None})
                yield _sse("stage", {"name": "cache_hit"})
                for tok in _chunk_text(hit["response"]):
                    yield _sse("token", {"text": tok})
                    await asyncio.sleep(0)
                yield _sse("done", {"response": hit["response"], "citations": [],
                                    "latency_ms": trace.latency_ms if trace else 0})
                return

        # 2) Routing
        intent = await router.classify(message) if router else None
        intent_val = intent.value if intent else "task"
        if trace:
            trace.intent = intent_val
        yield _sse("meta", {"cache_hit": False, "intent": intent_val,
                            "trace_id": trace.id if trace else None})
        yield _sse("stage", {"name": "classified", "intent": intent_val})

        # 3) RAG
        context = ""
        if rag:
            context, citations = await rag.retrieve_with_citations(message)
            if citations:
                if trace:
                    trace.used_rag = True; trace.citations = len(citations)
                yield _sse("stage", {"name": "retrieved", "sources": len(citations)})
                yield _sse("citations", {"citations": citations})

        # 4a) Conversational fast-path → real token streaming
        if intent_val == "chat":
            yield _sse("stage", {"name": "generating"})
            token_stream = await _conversational_answer(components, message, context, stream=True)
            async for token in token_stream:
                full_answer += token
                yield _sse("token", {"text": token})

        # 4b) Task path → live agent steps, then stream the synthesised answer
        else:
            orchestrator = components.get("orchestrator")
            queue: asyncio.Queue = asyncio.Queue()

            def on_event(ev):
                try:
                    queue.put_nowait(ev.to_dict())
                except Exception:
                    pass

            orchestrator.event_handlers = [on_event]
            yield _sse("stage", {"name": "orchestrating"})

            augmented = f"{context}\n\nUser question: {message}" if context else message
            task = asyncio.create_task(orchestrator.execute(augmented))

            # Drain agent events live until execution completes.
            while not task.done() or not queue.empty():
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=0.3)
                    yield _sse("step", ev)
                except asyncio.TimeoutError:
                    pass

            result = await task
            answer = (result.output or "").strip() or _friendly_error(
                getattr(result, "error", None), [])
            yield _sse("stage", {"name": "responding"})
            for tok in _chunk_text(answer):
                full_answer += tok
                yield _sse("token", {"text": tok})
                await asyncio.sleep(0)

        # 5) finalize: cache + memory + trace
        full_answer = full_answer.strip()
        if cache and full_answer and not full_answer.startswith("⚠️"):
            cache.set(message, full_answer)
        vm = components.get("vector_memory")
        if vm and full_answer and not full_answer.startswith("⚠️"):
            try:
                await vm.add(content=f"Task: {message}\nResult: {full_answer[:500]}", memory_type="conversation")
            except Exception:
                pass
        if trace:
            trace.provider = settings.llm_provider
            trace.finish("ok"); tracer.record(trace)

        yield _sse("done", {"response": full_answer, "citations": citations,
                            "latency_ms": trace.latency_ms if trace else 0})

    except Exception as e:
        if trace:
            trace.finish("error"); tracer.record(trace)
        yield _sse("error", {"message": _friendly_error(str(e), [])})
