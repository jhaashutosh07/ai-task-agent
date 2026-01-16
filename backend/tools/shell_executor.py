import asyncio
import subprocess
import os
from pathlib import Path
from typing import List
from .base import BaseTool, ToolResult


class ShellExecutorTool(BaseTool):
    """Execute shell commands with safety checks"""

    def __init__(
        self,
        workspace_path: str = "./workspace",
        allowed_commands: List[str] = None,
        blocked_commands: List[str] = None,
        timeout: int = 60
    ):
        self.workspace_path = Path(workspace_path).resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

        # Default allowed commands (whitelist approach for safety)
        self.allowed_commands = allowed_commands or [
            "ls", "dir", "pwd", "echo", "cat", "head", "tail", "grep", "find",
            "wc", "sort", "uniq", "curl", "wget", "pip", "python", "node", "npm",
            "git", "docker", "kubectl", "az", "aws", "gcloud",
            "mkdir", "touch", "cp", "mv", "which", "where", "type",
            "date", "whoami", "hostname", "df", "du", "free", "top", "ps",
            "ping", "nslookup", "dig", "traceroute", "netstat", "ifconfig", "ip"
        ]

        # Explicitly blocked dangerous commands
        self.blocked_commands = blocked_commands or [
            "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){", "fork bomb",
            "shutdown", "reboot", "halt", "poweroff", "init 0", "init 6",
            "> /dev/sda", "chmod -R 777 /", "chown -R", "format c:",
            "del /f /s /q c:", "rd /s /q c:",
        ]

    @property
    def name(self) -> str:
        return "shell_execute"

    @property
    def description(self) -> str:
        return """Execute shell/terminal commands. Use for system operations,
running scripts, git commands, package management, and more.
Safety checks are in place to prevent dangerous operations."""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for the command (default: workspace)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 60)",
                    "default": 60
                }
            },
            "required": ["command"]
        }

    def _is_dangerous(self, command: str) -> tuple[bool, str]:
        """Check if command is dangerous"""
        command_lower = command.lower()

        # Check blocked patterns
        for blocked in self.blocked_commands:
            if blocked.lower() in command_lower:
                return True, f"Command contains blocked pattern: {blocked}"

        return False, ""

    def _is_allowed(self, command: str) -> bool:
        """Check if the base command is in allowlist"""
        # Extract the base command
        parts = command.strip().split()
        if not parts:
            return False

        base_cmd = parts[0].split("/")[-1].split("\\")[-1]  # Get just the command name
        return base_cmd in self.allowed_commands

    async def execute(
        self,
        command: str,
        working_dir: str | None = None,
        timeout: int = None
    ) -> ToolResult:
        timeout = timeout or self.timeout

        # Safety checks
        is_dangerous, reason = self._is_dangerous(command)
        if is_dangerous:
            return ToolResult(
                success=False,
                output="",
                error=f"Command blocked for safety: {reason}"
            )

        # Determine working directory
        if working_dir:
            work_path = Path(working_dir).resolve()
        else:
            work_path = self.workspace_path

        # Ensure working directory exists
        work_path.mkdir(parents=True, exist_ok=True)

        try:
            # Determine shell based on OS
            if os.name == 'nt':  # Windows
                shell_cmd = ["cmd", "/c", command]
            else:  # Unix-like
                shell_cmd = ["bash", "-c", command]

            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(work_path)
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command timed out after {timeout} seconds"
                )

            stdout_text = stdout.decode("utf-8", errors="replace").strip()
            stderr_text = stderr.decode("utf-8", errors="replace").strip()

            if process.returncode == 0:
                output = f"**Command:** `{command}`\n**Working Dir:** {work_path}\n\n"
                if stdout_text:
                    output += f"**Output:**\n```\n{stdout_text}\n```"
                else:
                    output += "**Output:** (no output)"

                return ToolResult(success=True, output=output)
            else:
                error_msg = stderr_text or stdout_text or f"Exit code: {process.returncode}"
                return ToolResult(
                    success=False,
                    output=f"**Command:** `{command}`\n**Working Dir:** {work_path}",
                    error=f"Command failed: {error_msg}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to execute command: {str(e)}"
            )
