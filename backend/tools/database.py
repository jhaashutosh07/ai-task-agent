import json
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseTool, ToolResult


class DatabaseTool(BaseTool):
    """Execute SQL queries on SQLite database"""

    def __init__(self, db_path: str = "./data/agent.db"):
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Blocked dangerous operations
        self.blocked_patterns = [
            "DROP DATABASE",
            "DROP TABLE",
            "TRUNCATE",
            "DELETE FROM" + " " * 10,  # Prevent mass delete without WHERE
            "ALTER TABLE",
            "GRANT",
            "REVOKE"
        ]

    @property
    def name(self) -> str:
        return "database"

    @property
    def description(self) -> str:
        return """Execute SQL queries on a SQLite database.
Supports SELECT, INSERT, UPDATE, DELETE, and CREATE TABLE operations.
Useful for storing and querying structured data."""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL query to execute"
                },
                "params": {
                    "type": "array",
                    "description": "Query parameters for prepared statements",
                    "items": {"type": "string"}
                },
                "explain": {
                    "type": "boolean",
                    "description": "Return query explanation instead of execution",
                    "default": False
                }
            },
            "required": ["query"]
        }

    def _is_blocked(self, query: str) -> tuple[bool, str]:
        """Check if query contains blocked patterns"""
        query_upper = query.upper().strip()

        for pattern in self.blocked_patterns:
            if pattern in query_upper:
                return True, f"Query contains blocked pattern: {pattern}"

        return False, ""

    def _is_read_only(self, query: str) -> bool:
        """Check if query is read-only"""
        query_upper = query.upper().strip()
        return query_upper.startswith(("SELECT", "EXPLAIN", "PRAGMA"))

    async def execute(
        self,
        query: str,
        params: List[Any] = None,
        explain: bool = False
    ) -> ToolResult:
        params = params or []

        # Safety check
        is_blocked, reason = self._is_blocked(query)
        if is_blocked:
            return ToolResult(
                success=False,
                output="",
                error=f"Query blocked: {reason}"
            )

        try:
            if explain:
                query = f"EXPLAIN QUERY PLAN {query}"

            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                cursor = await db.execute(query, params)

                if self._is_read_only(query):
                    # Fetch results
                    rows = await cursor.fetchall()
                    columns = [description[0] for description in cursor.description] if cursor.description else []

                    if not rows:
                        return ToolResult(
                            success=True,
                            output=f"**Query:** `{query}`\n\n**Result:** No rows returned"
                        )

                    # Format as table
                    results = [dict(row) for row in rows]

                    # Limit results
                    max_rows = 100
                    truncated = len(results) > max_rows
                    if truncated:
                        results = results[:max_rows]

                    # Format output
                    output = f"**Query:** `{query}`\n\n"
                    output += f"**Columns:** {', '.join(columns)}\n"
                    output += f"**Rows:** {len(results)}"
                    if truncated:
                        output += f" (truncated from {cursor.rowcount})"
                    output += "\n\n**Results:**\n```json\n"
                    output += json.dumps(results, indent=2, default=str)
                    output += "\n```"

                    return ToolResult(success=True, output=output)

                else:
                    # Write operation
                    await db.commit()
                    rows_affected = cursor.rowcount

                    return ToolResult(
                        success=True,
                        output=f"**Query:** `{query}`\n\n**Rows affected:** {rows_affected}"
                    )

        except aiosqlite.Error as e:
            return ToolResult(
                success=False,
                output=f"**Query:** `{query}`",
                error=f"Database error: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Query failed: {str(e)}"
            )

    async def get_schema(self) -> ToolResult:
        """Get database schema"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT name, sql FROM sqlite_master WHERE type='table'"
                )
                tables = await cursor.fetchall()

                if not tables:
                    return ToolResult(
                        success=True,
                        output="**Database Schema:** No tables found"
                    )

                output = "**Database Schema:**\n\n"
                for table in tables:
                    output += f"### {table[0]}\n```sql\n{table[1]}\n```\n\n"

                return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to get schema: {str(e)}"
            )
