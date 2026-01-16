import asyncio
import subprocess
import tempfile
import os
from pathlib import Path
from .base import BaseTool, ToolResult


class CodeExecutorTool(BaseTool):
    def __init__(self, workspace_path: str = "./workspace"):
        self.workspace_path = Path(workspace_path).resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return "Execute Python code and return the output. Use this to run calculations, data processing, or test code snippets."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute"
                },
                "save_as": {
                    "type": "string",
                    "description": "Optional filename to save the code (e.g., 'script.py')"
                }
            },
            "required": ["code"]
        }

    async def execute(self, code: str, save_as: str | None = None) -> ToolResult:
        try:
            # Save code to file
            if save_as:
                file_path = self.workspace_path / save_as
            else:
                # Use temp file
                fd, temp_path = tempfile.mkstemp(suffix=".py", dir=self.workspace_path)
                os.close(fd)
                file_path = Path(temp_path)

            file_path.write_text(code, encoding="utf-8")

            # Execute the code with timeout
            process = await asyncio.create_subprocess_exec(
                "python",
                str(file_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.workspace_path)
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    output="",
                    error="Code execution timed out after 30 seconds"
                )

            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Clean up temp file if not saved
            if not save_as and file_path.exists():
                file_path.unlink()

            if process.returncode == 0:
                output = f"**Execution successful:**\n```\n{stdout_text}\n```"
                if save_as:
                    output += f"\n\nCode saved to: {file_path}"
                return ToolResult(success=True, output=output)
            else:
                error_output = stderr_text or stdout_text
                return ToolResult(
                    success=False,
                    output=f"**Code:**\n```python\n{code}\n```",
                    error=f"Execution failed with exit code {process.returncode}:\n{error_output}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to execute code: {str(e)}"
            )
