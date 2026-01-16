"""
Git Operations Tool - Read-only Git repository operations
"""
import asyncio
import os
from typing import Optional
from .base import BaseTool, ToolResult


class GitOperationsTool(BaseTool):
    """
    Git repository information tool (read-only operations only).

    This tool provides safe, read-only access to Git repositories for:
    - Viewing repository status
    - Checking commit history
    - Viewing diffs
    - Listing branches
    - Viewing file blame

    Security: Only read-only operations are allowed. No commits, pushes,
    or modifications to the repository are permitted.
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

    @property
    def name(self) -> str:
        return "git_operations"

    @property
    def description(self) -> str:
        return """Read-only Git repository operations. Can view status, history, diffs, branches, and blame information.
Available operations:
- status: Show working tree status
- log: Show commit history
- diff: Show changes
- branches: List branches
- blame: Show file blame
- show: Show commit details
- remote: List remotes"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Git operation to perform",
                    "enum": ["status", "log", "diff", "branches", "blame", "show", "remote"]
                },
                "path": {
                    "type": "string",
                    "description": "Repository path (relative to workspace)"
                },
                "file": {
                    "type": "string",
                    "description": "File path for blame/diff operations"
                },
                "commit": {
                    "type": "string",
                    "description": "Commit hash for show operation"
                },
                "limit": {
                    "type": "integer",
                    "description": "Limit for log entries (default: 10)"
                }
            },
            "required": ["operation"]
        }

    async def execute(
        self,
        operation: str,
        path: str = ".",
        file: Optional[str] = None,
        commit: Optional[str] = None,
        limit: int = 10
    ) -> ToolResult:
        """Execute a read-only Git operation."""

        # Validate and resolve path
        repo_path = os.path.join(self.workspace_path, path)
        repo_path = os.path.abspath(repo_path)

        # Security check: ensure path is within workspace
        if not repo_path.startswith(os.path.abspath(self.workspace_path)):
            return ToolResult(
                success=False,
                output="",
                error="Path is outside workspace"
            )

        # Check if directory exists
        if not os.path.isdir(repo_path):
            return ToolResult(
                success=False,
                output="",
                error=f"Directory not found: {path}"
            )

        # Check if it's a Git repository
        git_dir = os.path.join(repo_path, ".git")
        if not os.path.isdir(git_dir):
            return ToolResult(
                success=False,
                output="",
                error=f"Not a Git repository: {path}"
            )

        try:
            if operation == "status":
                result = await self._run_git(repo_path, ["status", "--porcelain", "-b"])

            elif operation == "log":
                result = await self._run_git(
                    repo_path,
                    ["log", f"-{limit}", "--oneline", "--decorate"]
                )

            elif operation == "diff":
                cmd = ["diff"]
                if file:
                    cmd.append(file)
                result = await self._run_git(repo_path, cmd)

            elif operation == "branches":
                result = await self._run_git(repo_path, ["branch", "-a", "-v"])

            elif operation == "blame":
                if not file:
                    return ToolResult(
                        success=False,
                        output="",
                        error="File path required for blame operation"
                    )
                result = await self._run_git(repo_path, ["blame", file])

            elif operation == "show":
                if not commit:
                    commit = "HEAD"
                result = await self._run_git(
                    repo_path,
                    ["show", commit, "--stat", "--format=fuller"]
                )

            elif operation == "remote":
                result = await self._run_git(repo_path, ["remote", "-v"])

            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown operation: {operation}"
                )

            return result

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Git operation failed: {str(e)}"
            )

    async def _run_git(self, cwd: str, args: list) -> ToolResult:
        """Run a Git command and return the result."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", *args,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30  # 30 second timeout
            )

            if process.returncode == 0:
                return ToolResult(
                    success=True,
                    output=stdout.decode("utf-8", errors="replace")
                )
            else:
                return ToolResult(
                    success=False,
                    output=stdout.decode("utf-8", errors="replace"),
                    error=stderr.decode("utf-8", errors="replace")
                )

        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output="",
                error="Git command timed out"
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                output="",
                error="Git is not installed or not in PATH"
            )

    async def get_repo_info(self, path: str = ".") -> dict:
        """Get comprehensive repository information."""
        repo_path = os.path.join(self.workspace_path, path)
        repo_path = os.path.abspath(repo_path)

        info = {
            "is_git_repo": False,
            "current_branch": None,
            "status": None,
            "recent_commits": [],
            "remotes": []
        }

        # Check if Git repo
        if not os.path.isdir(os.path.join(repo_path, ".git")):
            return info

        info["is_git_repo"] = True

        # Get current branch
        result = await self._run_git(repo_path, ["branch", "--show-current"])
        if result.success:
            info["current_branch"] = result.output.strip()

        # Get status
        result = await self._run_git(repo_path, ["status", "--porcelain"])
        if result.success:
            info["status"] = {
                "clean": len(result.output.strip()) == 0,
                "changes": result.output.strip().split("\n") if result.output.strip() else []
            }

        # Get recent commits
        result = await self._run_git(repo_path, ["log", "-5", "--oneline"])
        if result.success:
            info["recent_commits"] = [
                line.strip() for line in result.output.strip().split("\n")
                if line.strip()
            ]

        # Get remotes
        result = await self._run_git(repo_path, ["remote", "-v"])
        if result.success:
            remotes = {}
            for line in result.output.strip().split("\n"):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        remotes[parts[0]] = parts[1]
            info["remotes"] = list(remotes.items())

        return info
