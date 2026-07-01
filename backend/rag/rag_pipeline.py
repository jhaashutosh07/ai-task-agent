import json
import os
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .document_processor import chunk_text, process_document

_WORD_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "is",
    "are", "was", "were", "be", "with", "as", "by", "at", "this", "that", "it",
    "what", "how", "why", "when", "which", "who", "do", "does", "i", "you",
}


def _tokenize(text: str) -> List[str]:
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS and len(w) > 1]

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class DocumentChunk:
    def __init__(self, id: str, content: str, metadata: Dict[str, Any], score: float = 0.0):
        self.id = id
        self.content = content
        self.metadata = metadata
        self.score = score


class RAGPipeline:
    """RAG pipeline — ingests documents into ChromaDB, retrieves relevant chunks at query time."""

    def __init__(self, persist_path: str = "./data/ragdb"):
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.documents: Dict[str, Dict] = {}
        self.pg_store = None  # durable PostgreSQL store (set via init_store)
        self._load_doc_index()

        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_path),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            # Prefer OpenAI embeddings (fast API call, non-blocking-ish, no heavy
            # local model). Falls back to ChromaDB's default local model only if
            # no OpenAI key is configured.
            ef = None
            openai_key = os.environ.get("OPENAI_API_KEY", "")
            if openai_key:
                try:
                    from chromadb.utils import embedding_functions
                    ef = embedding_functions.OpenAIEmbeddingFunction(
                        api_key=openai_key,
                        model_name=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                    )
                    print("RAG: ChromaDB using OpenAI embeddings")
                except Exception as e:
                    print(f"RAG: OpenAI embedding function unavailable ({e}); using local model")
                    ef = None
            self.collection = self.client.get_or_create_collection(
                name="rag_documents",
                metadata={"hnsw:space": "cosine"},
                embedding_function=ef,
            )
        else:
            self.client = None
            self.collection = None

    async def init_store(self):
        """Enable durable PostgreSQL storage when a DATABASE_URL is configured."""
        import os
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            print("RAG: DATABASE_URL not set → using local ChromaDB (ephemeral)")
            return  # local dev → keep ChromaDB on disk
        try:
            from .pg_store import PgRagStore
            # Reuse ChromaDB's already-loaded embedding model (saves ~90MB RAM).
            ef = getattr(self.collection, "_embedding_function", None) if self.collection else None
            store = PgRagStore(db_url, embedding_function=ef)
            await store.init()
            self.pg_store = store
            # Release the now-unused local ChromaDB RAG collection to free memory.
            self.collection = None
            print("RAG: using durable PostgreSQL store ✓")
        except Exception as e:
            print(f"RAG: PostgreSQL store unavailable, falling back to ChromaDB ({type(e).__name__}: {e})")
            self.pg_store = None

    def _load_doc_index(self):
        f = self.persist_path / "doc_index.json"
        if f.exists():
            try:
                self.documents = json.loads(f.read_text())
            except Exception:
                self.documents = {}

    def _save_doc_index(self):
        (self.persist_path / "doc_index.json").write_text(
            json.dumps(self.documents, indent=2)
        )

    async def ingest(
        self,
        content,
        filename: str,
        file_type: str = None,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        text, detected_type = process_document(content, filename, file_type)
        if not text.strip():
            raise ValueError("No text could be extracted from the document.")
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("Document produced no chunks after processing.")

        # Durable PostgreSQL path (survives restarts on ephemeral hosts).
        if self.pg_store:
            await self.pg_store.add_chunks(doc_id, filename, detected_type, chunks)
            return {"doc_id": doc_id, "filename": filename, "chunks": len(chunks), "characters": len(text)}

        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        chunk_metas = [
            {
                "doc_id": doc_id,
                "filename": filename,
                "file_type": detected_type,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "ingested_at": datetime.now().isoformat(),
                **(metadata or {}),
            }
            for i in range(len(chunks))
        ]

        if CHROMA_AVAILABLE and self.collection:
            for i in range(0, len(chunk_ids), 100):
                self.collection.add(
                    ids=chunk_ids[i : i + 100],
                    documents=chunks[i : i + 100],
                    metadatas=chunk_metas[i : i + 100],
                )

        self.documents[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "file_type": detected_type,
            "chunk_count": len(chunks),
            "char_count": len(text),
            "ingested_at": datetime.now().isoformat(),
            **(metadata or {}),
        }
        self._save_doc_index()
        return {"doc_id": doc_id, "filename": filename, "chunks": len(chunks), "characters": len(text)}

    async def query(
        self, query: str, n_results: int = 5, doc_id: str = None
    ) -> List[DocumentChunk]:
        if self.pg_store:
            rows = await self.pg_store.query(query, n_results=n_results, doc_id=doc_id)
            return [DocumentChunk(id=r["id"], content=r["content"], metadata=r["metadata"], score=r["score"]) for r in rows]
        if not CHROMA_AVAILABLE or not self.collection:
            return []
        try:
            total = self.collection.count()
            if total == 0:
                return []
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, total),
                where={"doc_id": doc_id} if doc_id else None,
            )
        except Exception:
            return []

        out = []
        if results and results["ids"] and results["ids"][0]:
            for i, cid in enumerate(results["ids"][0]):
                dist = results["distances"][0][i] if results.get("distances") else 1.0
                score = max(0.0, 1 - dist / 2)
                out.append(
                    DocumentChunk(
                        id=cid,
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                        score=score,
                    )
                )
        return out

    async def hybrid_query(self, query: str, n_results: int = 5, doc_id: str = None) -> List[DocumentChunk]:
        """
        Hybrid retrieval + reranking.

        1. Pull a larger candidate pool via dense vector search (semantic).
        2. Score the same candidates with a lexical/keyword signal (term coverage).
        3. Fuse the two rankings with Reciprocal Rank Fusion (RRF) so a chunk that
           is strong on *either* signal floats to the top.

        Returns the top `n_results` reranked chunks, each carrying a fused `score`.
        """
        pool = max(n_results * 4, 12)
        candidates = await self.query(query, n_results=pool, doc_id=doc_id)
        if not candidates:
            return []

        q_terms = set(_tokenize(query))

        # Vector ranking (already ordered best-first by Chroma).
        vector_rank = {c.id: i for i, c in enumerate(candidates)}

        # Lexical ranking by term coverage of the query.
        def lexical_score(chunk: DocumentChunk) -> float:
            if not q_terms:
                return 0.0
            c_terms = _tokenize(chunk.content)
            if not c_terms:
                return 0.0
            counts = {}
            for t in c_terms:
                counts[t] = counts.get(t, 0) + 1
            covered = sum(1 for t in q_terms if t in counts)
            freq = sum(counts.get(t, 0) for t in q_terms)
            # coverage dominates, frequency breaks ties (saturating)
            return covered + min(freq, len(q_terms)) / (len(q_terms) + 1)

        lexical_sorted = sorted(candidates, key=lexical_score, reverse=True)
        lexical_rank = {c.id: i for i, c in enumerate(lexical_sorted)}

        # Reciprocal Rank Fusion.
        k = 60
        fused: Dict[str, float] = {}
        for c in candidates:
            rrf = 1.0 / (k + vector_rank.get(c.id, pool)) + 1.0 / (k + lexical_rank.get(c.id, pool))
            fused[c.id] = rrf

        for c in candidates:
            # Blend the human-readable semantic score with the fusion signal.
            c.score = round(0.5 * c.score + 0.5 * (fused[c.id] / (2.0 / (k + 1))), 4)

        reranked = sorted(candidates, key=lambda c: fused[c.id], reverse=True)
        return reranked[:n_results]

    async def retrieve_with_citations(
        self, query: str, n_results: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Returns (context_string, citations).
        The context is annotated with [1], [2]… markers and the model is instructed
        to cite them. `citations` is a list the API/UI can render as sources.
        """
        chunks = await self.hybrid_query(query, n_results=n_results)
        if not chunks:
            return "", []

        parts = [
            "### Context from the user's documents",
            "Use the sources below to answer. Cite them inline with [n] markers.",
            "",
        ]
        citations: List[Dict[str, Any]] = []
        for i, chunk in enumerate(chunks, start=1):
            fname = chunk.metadata.get("filename", "document")
            parts.append(f"[{i}] (source: {fname}) {chunk.content}")
            citations.append({
                "n": i,
                "filename": fname,
                "chunk_index": chunk.metadata.get("chunk_index"),
                "score": round(chunk.score, 4),
                "snippet": chunk.content[:240] + ("…" if len(chunk.content) > 240 else ""),
            })
        parts.append("---")
        return "\n".join(parts), citations

    async def build_context(self, query: str, n_results: int = 5) -> str:
        context, _ = await self.retrieve_with_citations(query, n_results=n_results)
        return context

    async def delete_document(self, doc_id: str) -> bool:
        if self.pg_store:
            return await self.pg_store.delete_document(doc_id)
        if doc_id not in self.documents:
            return False
        if CHROMA_AVAILABLE and self.collection:
            n = self.documents[doc_id]["chunk_count"]
            try:
                self.collection.delete(ids=[f"{doc_id}_{i}" for i in range(n)])
            except Exception:
                pass
        del self.documents[doc_id]
        self._save_doc_index()
        return True

    async def list_documents(self) -> List[Dict]:
        if self.pg_store:
            return await self.pg_store.list_documents()
        return list(self.documents.values())

    async def get_stats(self) -> Dict[str, Any]:
        if self.pg_store:
            stats = await self.pg_store.stats()
            stats["storage"] = "postgresql"
            return stats
        count = 0
        if CHROMA_AVAILABLE and self.collection:
            try:
                count = self.collection.count()
            except Exception:
                pass
        return {
            "documents": len(self.documents),
            "total_chunks": count,
            "storage": "chromadb" if CHROMA_AVAILABLE else "unavailable",
        }