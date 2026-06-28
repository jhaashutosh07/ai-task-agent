"""
Lightweight in-process tracer for the chat pipeline.

Each chat request produces a Trace capturing: the route taken (chat/task),
whether the semantic cache was hit, retrieval/citation counts, latency, and
the ordered pipeline stages. A bounded ring buffer keeps the most recent
traces in memory and exposes aggregate metrics for an observability dashboard.

This is intentionally dependency-free (no external APM) so it runs anywhere,
while mirroring the shape of real tracing systems (spans + attributes).
"""
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Deque, Dict, List, Optional


@dataclass
class Trace:
    id: str
    query: str
    started_at: float
    intent: str = "unknown"
    cache_hit: bool = False
    used_rag: bool = False
    citations: int = 0
    reflected: bool = False
    provider: str = ""
    status: str = "ok"
    latency_ms: float = 0.0
    stages: List[Dict[str, Any]] = field(default_factory=list)

    def stage(self, name: str, **attrs: Any) -> None:
        self.stages.append({
            "name": name,
            "t_ms": round((time.time() - self.started_at) * 1000, 1),
            **attrs,
        })

    def finish(self, status: str = "ok") -> None:
        self.status = status
        self.latency_ms = round((time.time() - self.started_at) * 1000, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query[:200],
            "intent": self.intent,
            "cache_hit": self.cache_hit,
            "used_rag": self.used_rag,
            "citations": self.citations,
            "reflected": self.reflected,
            "provider": self.provider,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "stages": self.stages,
            "timestamp": self.started_at,
        }


class Tracer:
    def __init__(self, maxlen: int = 200):
        self._traces: Deque[Trace] = deque(maxlen=maxlen)
        self._lock = Lock()

    def start(self, query: str) -> Trace:
        trace = Trace(id=str(uuid.uuid4())[:8], query=query, started_at=time.time())
        return trace

    def record(self, trace: Trace) -> None:
        with self._lock:
            self._traces.append(trace)

    def recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._traces)[-limit:]
        return [t.to_dict() for t in reversed(items)]

    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            items = list(self._traces)
        if not items:
            return {
                "total_requests": 0, "cache_hits": 0, "cache_hit_rate": 0.0,
                "avg_latency_ms": 0.0, "p95_latency_ms": 0.0,
                "intent_distribution": {}, "rag_requests": 0, "reflected": 0,
                "error_rate": 0.0,
            }
        n = len(items)
        latencies = sorted(t.latency_ms for t in items)
        cache_hits = sum(1 for t in items if t.cache_hit)
        errors = sum(1 for t in items if t.status != "ok")
        intents: Dict[str, int] = {}
        for t in items:
            intents[t.intent] = intents.get(t.intent, 0) + 1
        p95_idx = max(0, int(0.95 * n) - 1)
        return {
            "total_requests": n,
            "cache_hits": cache_hits,
            "cache_hit_rate": round(cache_hits / n, 4),
            "avg_latency_ms": round(sum(latencies) / n, 1),
            "p95_latency_ms": latencies[p95_idx],
            "intent_distribution": intents,
            "rag_requests": sum(1 for t in items if t.used_rag),
            "reflected": sum(1 for t in items if t.reflected),
            "error_rate": round(errors / n, 4),
        }


_tracer: Optional[Tracer] = None


def init_tracer() -> Tracer:
    global _tracer
    _tracer = Tracer()
    return _tracer


def get_tracer() -> Tracer:
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer
