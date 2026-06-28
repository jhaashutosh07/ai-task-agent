"""
PostgreSQL-backed RAG store (durable)
=====================================
Render's free tier has an *ephemeral* filesystem, so a local ChromaDB directory
is wiped on every redeploy / cold-start. That makes uploaded documents vanish.

This store persists chunks + embeddings in PostgreSQL instead, so documents
survive restarts. It uses its own table + metadata (create-only, never dropped),
independent of the auth `Base` whose `init_db()` does drop_all/create_all.

Embeddings reuse ChromaDB's default model (all-MiniLM-L6-v2) so no extra model
weight is added. Similarity search is done in NumPy over the stored vectors —
more than adequate for the document volumes of a demo/portfolio deployment.
"""
import json
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, select, delete, func
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

try:
    import numpy as np
    NUMPY = True
except ImportError:
    NUMPY = False

RagBase = declarative_base()


def _utcnow():
    return datetime.now(timezone.utc)


class RagChunkModel(RagBase):
    __tablename__ = "rag_chunks"

    id = Column(String(80), primary_key=True)
    doc_id = Column(String(36), index=True)
    filename = Column(String(512))
    file_type = Column(String(16))
    chunk_index = Column(Integer)
    total_chunks = Column(Integer)
    content = Column(Text)
    embedding = Column(Text)  # JSON-encoded float list
    char_count = Column(Integer)
    ingested_at = Column(DateTime(timezone=True), default=_utcnow)


def _to_asyncpg(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class PgRagStore:
    def __init__(self, database_url: str, embedding_function=None):
        self.engine = create_async_engine(_to_asyncpg(database_url), echo=False, pool_pre_ping=True)
        self.session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        # Reuse a pre-existing embedding function (e.g. ChromaDB's) to avoid
        # loading a second copy of the model — important on memory-limited hosts.
        self._ef = embedding_function

    @property
    def ef(self):
        """Embedding function — reuses the shared model when one was supplied."""
        if self._ef is None:
            from chromadb.utils import embedding_functions
            self._ef = embedding_functions.DefaultEmbeddingFunction()
        return self._ef

    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(RagBase.metadata.create_all)  # create-only, never dropped

    async def _embed(self, texts: List[str]) -> List[List[float]]:
        # Embedding is CPU-bound — run off the event loop.
        def _run():
            return [list(map(float, v)) for v in self.ef(texts)]
        return await asyncio.to_thread(_run)

    async def add_chunks(self, doc_id: str, filename: str, file_type: str, chunks: List[str]) -> int:
        embeddings = await self._embed(chunks)
        now = _utcnow()
        async with self.session() as s:
            for i, (text, emb) in enumerate(zip(chunks, embeddings)):
                s.add(RagChunkModel(
                    id=f"{doc_id}_{i}", doc_id=doc_id, filename=filename, file_type=file_type,
                    chunk_index=i, total_chunks=len(chunks), content=text,
                    embedding=json.dumps(emb), char_count=len(text), ingested_at=now,
                ))
            await s.commit()
        return len(chunks)

    async def query(self, query: str, n_results: int = 5, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        q_emb = (await self._embed([query]))[0]
        async with self.session() as s:
            stmt = select(RagChunkModel)
            if doc_id:
                stmt = stmt.where(RagChunkModel.doc_id == doc_id)
            rows = (await s.execute(stmt)).scalars().all()
        if not rows:
            return []

        scored = []
        if NUMPY:
            qv = np.asarray(q_emb, dtype=np.float32)
            qv = qv / (np.linalg.norm(qv) + 1e-9)
            for r in rows:
                try:
                    v = np.asarray(json.loads(r.embedding), dtype=np.float32)
                except Exception:
                    continue
                sim = float(np.dot(qv, v / (np.linalg.norm(v) + 1e-9)))
                scored.append((sim, r))
        else:
            def dot(a, b):
                return sum(x * y for x, y in zip(a, b))
            def norm(a):
                return sum(x * x for x in a) ** 0.5 + 1e-9
            qn = norm(q_emb)
            for r in rows:
                try:
                    v = json.loads(r.embedding)
                except Exception:
                    continue
                sim = dot(q_emb, v) / (qn * norm(v))
                scored.append((sim, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for sim, r in scored[:n_results]:
            out.append({
                "id": r.id,
                "content": r.content,
                "score": max(0.0, min(1.0, (sim + 1) / 2)),  # map cosine [-1,1] → [0,1]
                "metadata": {
                    "doc_id": r.doc_id,
                    "filename": r.filename,
                    "file_type": r.file_type,
                    "chunk_index": r.chunk_index,
                    "total_chunks": r.total_chunks,
                },
            })
        return out

    async def list_documents(self) -> List[Dict[str, Any]]:
        async with self.session() as s:
            stmt = (
                select(
                    RagChunkModel.doc_id,
                    func.max(RagChunkModel.filename).label("filename"),
                    func.max(RagChunkModel.file_type).label("file_type"),
                    func.count(RagChunkModel.id).label("chunk_count"),
                    func.coalesce(func.sum(RagChunkModel.char_count), 0).label("char_count"),
                    func.min(RagChunkModel.ingested_at).label("ingested_at"),
                )
                .group_by(RagChunkModel.doc_id)
            )
            rows = (await s.execute(stmt)).all()
        docs = []
        for r in rows:
            docs.append({
                "id": r.doc_id,
                "filename": r.filename,
                "file_type": r.file_type,
                "chunk_count": int(r.chunk_count),
                "char_count": int(r.char_count or 0),
                "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
            })
        docs.sort(key=lambda d: d["ingested_at"] or "", reverse=True)
        return docs

    async def delete_document(self, doc_id: str) -> bool:
        async with self.session() as s:
            res = await s.execute(delete(RagChunkModel).where(RagChunkModel.doc_id == doc_id))
            await s.commit()
            return res.rowcount > 0

    async def stats(self) -> Dict[str, int]:
        async with self.session() as s:
            total_chunks = (await s.execute(select(func.count(RagChunkModel.id)))).scalar() or 0
            total_docs = (await s.execute(
                select(func.count(func.distinct(RagChunkModel.doc_id)))
            )).scalar() or 0
        return {"documents": int(total_docs), "total_chunks": int(total_chunks)}
