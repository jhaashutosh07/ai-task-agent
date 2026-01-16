import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class MemoryItem(BaseModel):
    """A single memory item"""
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = None
    relevance_score: float = 0.0

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.now()


class VectorMemory:
    """
    Long-term vector memory using ChromaDB.
    Stores and retrieves relevant context based on semantic similarity.
    """

    def __init__(
        self,
        persist_path: str = "./data/vectordb",
        collection_name: str = "agent_memory"
    ):
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_path),
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "AI Agent Long-term Memory"}
            )
        else:
            self.client = None
            self.collection = None
            # Fallback to simple file storage
            self.fallback_memory: List[Dict] = []
            self._load_fallback()

    def _load_fallback(self):
        """Load fallback memory from file"""
        fallback_file = self.persist_path / "memory.json"
        if fallback_file.exists():
            try:
                with open(fallback_file, "r") as f:
                    self.fallback_memory = json.load(f)
            except:
                self.fallback_memory = []

    def _save_fallback(self):
        """Save fallback memory to file"""
        fallback_file = self.persist_path / "memory.json"
        with open(fallback_file, "w") as f:
            json.dump(self.fallback_memory, f, default=str, indent=2)

    async def add(
        self,
        content: str,
        metadata: Dict[str, Any] = None,
        memory_type: str = "general"
    ) -> str:
        """Add a new memory item"""
        memory_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata["type"] = memory_type
        metadata["timestamp"] = datetime.now().isoformat()

        if CHROMA_AVAILABLE and self.collection:
            self.collection.add(
                ids=[memory_id],
                documents=[content],
                metadatas=[metadata]
            )
        else:
            self.fallback_memory.append({
                "id": memory_id,
                "content": content,
                "metadata": metadata
            })
            self._save_fallback()

        return memory_id

    async def search(
        self,
        query: str,
        n_results: int = 5,
        memory_type: str = None,
        min_relevance: float = 0.0
    ) -> List[MemoryItem]:
        """Search for relevant memories"""
        if CHROMA_AVAILABLE and self.collection:
            where_filter = {"type": memory_type} if memory_type else None

            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )

            items = []
            if results and results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB returns distances, convert to similarity
                    distance = results["distances"][0][i] if results["distances"] else 0
                    relevance = 1 - (distance / 2)  # Normalize to 0-1

                    if relevance >= min_relevance:
                        items.append(MemoryItem(
                            id=doc_id,
                            content=results["documents"][0][i],
                            metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                            relevance_score=relevance
                        ))

            return items

        else:
            # Simple keyword search fallback
            query_lower = query.lower()
            scored = []

            for mem in self.fallback_memory:
                if memory_type and mem.get("metadata", {}).get("type") != memory_type:
                    continue

                content = mem.get("content", "").lower()
                # Simple relevance scoring based on word overlap
                query_words = set(query_lower.split())
                content_words = set(content.split())
                overlap = len(query_words & content_words)
                relevance = overlap / max(len(query_words), 1)

                if relevance >= min_relevance:
                    scored.append((mem, relevance))

            # Sort by relevance
            scored.sort(key=lambda x: x[1], reverse=True)

            return [
                MemoryItem(
                    id=mem["id"],
                    content=mem["content"],
                    metadata=mem.get("metadata", {}),
                    relevance_score=score
                )
                for mem, score in scored[:n_results]
            ]

    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID"""
        if CHROMA_AVAILABLE and self.collection:
            result = self.collection.get(ids=[memory_id])
            if result and result["ids"]:
                return MemoryItem(
                    id=result["ids"][0],
                    content=result["documents"][0],
                    metadata=result["metadatas"][0] if result["metadatas"] else {}
                )
        else:
            for mem in self.fallback_memory:
                if mem["id"] == memory_id:
                    return MemoryItem(
                        id=mem["id"],
                        content=mem["content"],
                        metadata=mem.get("metadata", {})
                    )
        return None

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        if CHROMA_AVAILABLE and self.collection:
            try:
                self.collection.delete(ids=[memory_id])
                return True
            except:
                return False
        else:
            self.fallback_memory = [
                m for m in self.fallback_memory if m["id"] != memory_id
            ]
            self._save_fallback()
            return True

    async def get_context(
        self,
        query: str,
        max_items: int = 5,
        max_chars: int = 2000
    ) -> str:
        """Get relevant context for a query as a formatted string"""
        memories = await self.search(query, n_results=max_items)

        if not memories:
            return ""

        context_parts = ["**Relevant Context from Memory:**"]
        total_chars = 0

        for mem in memories:
            if total_chars + len(mem.content) > max_chars:
                break
            context_parts.append(
                f"- [{mem.metadata.get('type', 'general')}] {mem.content[:500]}"
            )
            total_chars += len(mem.content)

        return "\n".join(context_parts)

    async def summarize_and_store(
        self,
        content: str,
        summary: str,
        memory_type: str = "conversation"
    ) -> str:
        """Store both detailed content and summary"""
        return await self.add(
            content=summary,
            metadata={
                "type": memory_type,
                "full_content": content[:5000]  # Store truncated full content
            }
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        if CHROMA_AVAILABLE and self.collection:
            count = self.collection.count()
        else:
            count = len(self.fallback_memory)

        return {
            "total_memories": count,
            "storage_type": "chromadb" if CHROMA_AVAILABLE else "file",
            "persist_path": str(self.persist_path)
        }
