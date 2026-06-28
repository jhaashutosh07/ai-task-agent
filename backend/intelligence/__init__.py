"""
Advanced intelligence layer:
- SemanticCache: embedding-similarity response cache (cuts cost + latency)
- IntentRouter: classifies messages as conversational chat vs. multi-step task
- ReflectionEngine: self-critique loop that reviews and improves answers
"""
from .semantic_cache import SemanticCache
from .router import IntentRouter, Intent
from .reflection import ReflectionEngine

__all__ = ["SemanticCache", "IntentRouter", "Intent", "ReflectionEngine"]
