import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .document_processor import chunk_text, process_document

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
        self._load_doc_index()

        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_path),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name="rag_documents",
                metadata={"hnsw:space": "cosine"},
            )
        else:
            self.client = None
            self.collection = None

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

    async def build_context(self, query: str, n_results: int = 5) -> str:
        chunks = await self.query(query, n_results=n_results)
        if not chunks:
            return ""
        parts = ["### Relevant context from your documents:"]
        for chunk in chunks:
            fname = chunk.metadata.get("filename", "document")
            parts.append(f"\n**[{fname}]** (relevance: {chunk.score:.0%})\n{chunk.content}")
        parts.append("---")
        return "\n".join(parts)

    async def delete_document(self, doc_id: str) -> bool:
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

    def list_documents(self) -> List[Dict]:
        return list(self.documents.values())

    def get_stats(self) -> Dict[str, Any]:
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