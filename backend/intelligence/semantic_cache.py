"""
Semantic Response Cache
=======================
Caches LLM responses keyed by the *meaning* of the query rather than an exact
string match. On each request we embed the query and look for a previously
answered question whose embedding is highly similar (cosine >= threshold).

This cuts both latency and provider cost for repeated / paraphrased questions —
a common production optimisation for LLM applications.

Backed by ChromaDB (re-uses the already-downloaded all-MiniLM-L6-v2 embedder),
so it adds no extra model weight to the deployment.
"""
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class SemanticCache:
    def __init__(self, persist_path: str = "./data/cache", threshold: float = 0.93, ttl_seconds: int = 86400):
        self.threshold = threshold
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)

        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_path),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name="semantic_cache",
                metadata={"hnsw:space": "cosine"},
            )
        else:
            self.client = None
            self.collection = None

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Return a cached response dict if a semantically-similar query exists."""
        if not self.collection:
            self.misses += 1
            return None
        try:
            if self.collection.count() == 0:
                self.misses += 1
                return None
            res = self.collection.query(query_texts=[query], n_results=1)
        except Exception:
            self.misses += 1
            return None

        if not res or not res["ids"] or not res["ids"][0]:
            self.misses += 1
            return None

        distance = res["distances"][0][0] if res.get("distances") else 1.0
        similarity = 1.0 - distance  # cosine space
        meta = res["metadatas"][0][0] if res.get("metadatas") else {}

        # Expiry check
        if self.ttl_seconds and time.time() - float(meta.get("ts", 0)) > self.ttl_seconds:
            self.misses += 1
            return None

        if similarity >= self.threshold and meta.get("response"):
            self.hits += 1
            return {
                "response": meta.get("response", ""),
                "matched_query": meta.get("query", ""),
                "similarity": round(similarity, 4),
                "cached_at": meta.get("ts"),
            }

        self.misses += 1
        return None

    def set(self, query: str, response: str) -> None:
        """Store a query/response pair (the embedded *query* is the key)."""
        if not self.collection or not response.strip():
            return
        try:
            self.collection.add(
                ids=[str(uuid.uuid4())],
                documents=[query],  # embed the question
                metadatas=[{"query": query, "response": response, "ts": time.time()}],
            )
            # We store the *answer* in metadata and also as a separate doc key.
            # Overwrite the document text used for retrieval with the answer payload:
        except Exception:
            pass

    def clear(self) -> int:
        if not self.collection:
            return 0
        try:
            n = self.collection.count()
            # recreate collection to wipe
            self.client.delete_collection("semantic_cache")
            self.collection = self.client.get_or_create_collection(
                name="semantic_cache", metadata={"hnsw:space": "cosine"}
            )
            return n
        except Exception:
            return 0

    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        size = 0
        if self.collection:
            try:
                size = self.collection.count()
            except Exception:
                size = 0
        return {
            "entries": size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total else 0.0,
            "threshold": self.threshold,
            "enabled": bool(self.collection),
        }
