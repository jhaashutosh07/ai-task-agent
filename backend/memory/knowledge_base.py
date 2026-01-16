import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid


class KnowledgeEntry(BaseModel):
    """A single knowledge base entry"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str] = []
    source: str = ""
    created_at: datetime = None
    updated_at: datetime = None
    usage_count: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()


class KnowledgeBase:
    """
    Persistent knowledge base for storing learned information,
    code snippets, solutions, and reusable patterns.
    """

    def __init__(self, storage_path: str = "./data/knowledge"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.categories: Dict[str, List[str]] = {}  # category -> entry_ids
        self._load()

    def _load(self):
        """Load knowledge base from disk"""
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    data = json.load(f)
                    for entry_data in data.get("entries", []):
                        entry = KnowledgeEntry(**entry_data)
                        self.entries[entry.id] = entry
                        self._index_entry(entry)
            except Exception as e:
                print(f"Error loading knowledge base: {e}")

    def _save(self):
        """Save knowledge base to disk"""
        index_file = self.storage_path / "index.json"
        data = {
            "entries": [
                {
                    "id": e.id,
                    "title": e.title,
                    "content": e.content,
                    "category": e.category,
                    "tags": e.tags,
                    "source": e.source,
                    "created_at": e.created_at.isoformat(),
                    "updated_at": e.updated_at.isoformat(),
                    "usage_count": e.usage_count
                }
                for e in self.entries.values()
            ]
        }
        with open(index_file, "w") as f:
            json.dump(data, f, indent=2)

    def _index_entry(self, entry: KnowledgeEntry):
        """Add entry to category index"""
        if entry.category not in self.categories:
            self.categories[entry.category] = []
        if entry.id not in self.categories[entry.category]:
            self.categories[entry.category].append(entry.id)

    async def add(
        self,
        title: str,
        content: str,
        category: str = "general",
        tags: List[str] = None,
        source: str = ""
    ) -> str:
        """Add new knowledge entry"""
        entry_id = str(uuid.uuid4())[:12]

        entry = KnowledgeEntry(
            id=entry_id,
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            source=source
        )

        self.entries[entry_id] = entry
        self._index_entry(entry)
        self._save()

        return entry_id

    async def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get entry by ID and increment usage count"""
        entry = self.entries.get(entry_id)
        if entry:
            entry.usage_count += 1
            self._save()
        return entry

    async def search(
        self,
        query: str,
        category: str = None,
        tags: List[str] = None,
        limit: int = 10
    ) -> List[KnowledgeEntry]:
        """Search knowledge base"""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for entry in self.entries.values():
            # Filter by category
            if category and entry.category != category:
                continue

            # Filter by tags
            if tags and not any(t in entry.tags for t in tags):
                continue

            # Score by relevance
            score = 0

            # Title match
            title_lower = entry.title.lower()
            if query_lower in title_lower:
                score += 10
            score += len(query_words & set(title_lower.split())) * 3

            # Content match
            content_lower = entry.content.lower()
            if query_lower in content_lower:
                score += 5
            score += len(query_words & set(content_lower.split()))

            # Tag match
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 3

            # Usage boost
            score += min(entry.usage_count * 0.1, 2)

            if score > 0:
                results.append((entry, score))

        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)

        return [entry for entry, score in results[:limit]]

    async def update(
        self,
        entry_id: str,
        title: str = None,
        content: str = None,
        tags: List[str] = None
    ) -> bool:
        """Update an existing entry"""
        entry = self.entries.get(entry_id)
        if not entry:
            return False

        if title:
            entry.title = title
        if content:
            entry.content = content
        if tags is not None:
            entry.tags = tags

        entry.updated_at = datetime.now()
        self._save()
        return True

    async def delete(self, entry_id: str) -> bool:
        """Delete an entry"""
        if entry_id not in self.entries:
            return False

        entry = self.entries[entry_id]
        if entry.category in self.categories:
            self.categories[entry.category] = [
                id for id in self.categories[entry.category] if id != entry_id
            ]

        del self.entries[entry_id]
        self._save()
        return True

    async def get_by_category(self, category: str) -> List[KnowledgeEntry]:
        """Get all entries in a category"""
        entry_ids = self.categories.get(category, [])
        return [self.entries[id] for id in entry_ids if id in self.entries]

    async def get_categories(self) -> Dict[str, int]:
        """Get all categories with entry counts"""
        return {cat: len(ids) for cat, ids in self.categories.items()}

    async def get_popular(self, limit: int = 10) -> List[KnowledgeEntry]:
        """Get most used entries"""
        sorted_entries = sorted(
            self.entries.values(),
            key=lambda e: e.usage_count,
            reverse=True
        )
        return sorted_entries[:limit]

    async def learn_from_interaction(
        self,
        task: str,
        solution: str,
        category: str = "learned"
    ) -> str:
        """Automatically learn from successful task completions"""
        # Check if similar knowledge exists
        existing = await self.search(task, category=category, limit=1)
        if existing and task.lower() in existing[0].title.lower():
            # Update existing
            await self.update(
                existing[0].id,
                content=solution
            )
            return existing[0].id

        # Create new entry
        return await self.add(
            title=f"Solution: {task[:100]}",
            content=solution,
            category=category,
            source="learned_from_interaction"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "total_entries": len(self.entries),
            "categories": len(self.categories),
            "category_breakdown": {cat: len(ids) for cat, ids in self.categories.items()},
            "total_usage": sum(e.usage_count for e in self.entries.values())
        }
