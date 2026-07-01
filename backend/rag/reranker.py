"""
Cross-Encoder Reranker
======================
A second-stage reranker that scores each (query, passage) pair jointly with a
cross-encoder transformer — far more accurate than the first-stage bi-encoder /
lexical retrieval, at the cost of running the model per candidate.

The model is loaded lazily on first use and everything degrades gracefully:
if torch / the model is unavailable, callers keep the original (RRF) ordering.
"""
import asyncio
import os
from typing import List, Tuple

_MODEL_NAME = os.environ.get("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")


class CrossEncoderReranker:
    def __init__(self):
        self._model = None
        self._failed = False

    @property
    def available(self) -> bool:
        return not self._failed

    def _load(self):
        if self._model is not None or self._failed:
            return
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(_MODEL_NAME, max_length=512)
            print(f"RAG: cross-encoder reranker loaded ({_MODEL_NAME})", flush=True)
        except Exception as e:
            self._failed = True
            print(f"RAG: cross-encoder unavailable, using RRF only ({type(e).__name__}: {e})", flush=True)

    def _score(self, query: str, passages: List[str]) -> List[float]:
        self._load()
        if self._model is None:
            return []
        pairs = [[query, p] for p in passages]
        scores = self._model.predict(pairs)
        return [float(s) for s in scores]

    async def rerank(self, query: str, items: List, top_k: int = None) -> List:
        """Reorder `items` (objects with a `.content` attribute) by cross-encoder
        relevance to `query`. Returns the original order if the model is
        unavailable. Sets `.rerank_score` on each returned item."""
        if not items or self._failed:
            return items[:top_k] if top_k else items
        passages = [getattr(it, "content", "") for it in items]
        try:
            scores = await asyncio.to_thread(self._score, query, passages)
        except Exception:
            scores = []
        if not scores:
            return items[:top_k] if top_k else items
        for it, s in zip(items, scores):
            setattr(it, "rerank_score", s)
        ranked = [it for _, it in sorted(zip(scores, items), key=lambda x: x[0], reverse=True)]
        return ranked[:top_k] if top_k else ranked


_reranker: CrossEncoderReranker | None = None


def get_reranker() -> CrossEncoderReranker:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker()
    return _reranker
