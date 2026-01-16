import os
import aiofiles
from pathlib import Path
from .base import BaseTool, ToolResult


class FileManagerTool(BaseTool):
    def __init__(self, workspace_path: str = "./workspace"):
        self.workspace_path = Path(workspace_path).resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "file_manager"

    @property
    def description(self) -> str:
        return "Manage files in the workspace. Can read, write, list, and delete files."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "list", "delete"],
                    "description": "The action to perform"
                },
                "path": {
                    "type": "string",
                    "description": "The file path (relative to workspace)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (required for 'write' action)"
                }
            },
            "required": ["action", "path"]
        }

    def _resolve_path(self, path: str) -> Path:
        """Resolve path and ensure it's within workspace"""
        resolved = (self.workspace_path / path).resolve()
        if not str(resolved).startswith(str(self.workspace_path)):
            raise ValueError("Path must be within workspace")
        return resolved

    async def execute(
        self,
        action: str,
        path: str,
        content: str | None = None
    ) -> ToolResult:
        try:
            if action == "list":
                return await self._list_files(path)
            elif action == "read":
                return await self._read_file(path)
            elif action == "write":
                if content is None:
                    return ToolResult(
                        success=False,
                        output="",
                        error="Content is required for write action"
                    )
                return await self._write_file(path, content)
            elif action == "delete":
                return await self._delete_file(path)
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown action: {action}"
                )
        except ValueError as e:
            return ToolResult(success=False, output="", error=str(e))
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"File operation failed: {str(e)}"
            )

    async def _list_files(self, path: str) -> ToolResult:
        target = self._resolve_path(path)
        if not target.exists():
            return ToolResult(
                success=False,
                output="",
                error=f"Path does not exist: {path}"
            )

        if target.is_file():
            stat = target.stat()
            return ToolResult(
                success=True,
                output=f"**File:** {path}\n**Size:** {stat.st_size} bytes"
            )

        # List directory contents
        items = []
        for item in sorted(target.iterdir()):
            rel_path = item.relative_to(self.workspace_path)
            if item.is_dir():
                items.append(f"  [DIR]  {rel_path}/")
            else:
                size = item.stat().st_size
                items.append(f"  [FILE] {rel_path} ({size} bytes)")

        if not items:
            return ToolResult(success=True, output=f"**{path}** is empty")

        return ToolResult(
            success=True,
            output=f"**Contents of {path}:**\n" + "\n".join(items)
        )

    async def _read_file(self, path: str) -> ToolResult:
        target = self._resolve_path(path)
        if not target.exists():
            return ToolResult(
                success=False,
                output="",
                error=f"File not found: {path}"
            )

        if target.is_dir():
            return ToolResult(
                success=False,
                output="",
                error=f"Cannot read a directory: {path}"
            )

        async with aiofiles.open(target, "r", encoding="utf-8") as f:
            content = await f.read()

        # Truncate if too long
        max_chars = 10000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[Content truncated...]"

        return ToolResult(
            success=True,
            output=f"**Contents of {path}:**\n```\n{content}\n```"
        )

    async def _write_file(self, path: str, content: str) -> ToolResult:
        target = self._resolve_path(path)

        # Create parent directories if needed
        target.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(target, "w", encoding="utf-8") as f:
            await f.write(content)

        return ToolResult(
            success=True,
            output=f"**Successfully wrote to {path}** ({len(content)} characters)"
        )

    async def _delete_file(self, path: str) -> ToolResult:
        target = self._resolve_path(path)
        if not target.exists():
            return ToolResult(
                success=False,
                output="",
                error=f"File not found: {path}"
            )

        if target.is_dir():
            return ToolResult(
                success=False,
                output="",
                error="Cannot delete directories with this tool"
            )

        target.unlink()
        return ToolResult(
            success=True,
            output=f"**Successfully deleted {path}**"
        )
