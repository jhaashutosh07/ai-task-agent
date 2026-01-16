import json
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, AgentResult, ThoughtStep, AgentState
from llm.base import Message, ToolDefinition


class ExecutorAgent(BaseAgent):
    """
    The Executor Agent specializes in system operations and automation.
    It can run shell commands, manage files, and perform system tasks.
    """

    def __init__(self, llm, tools: Dict[str, Any] = None, confirm_dangerous: bool = True):
        super().__init__(llm, tools)
        self.confirm_dangerous = confirm_dangerous
        self.dangerous_commands = ["rm", "del", "format", "sudo", "chmod", "kill", "shutdown"]
        self.pending_confirmation = None

    @property
    def role(self) -> AgentRole:
        return AgentRole.EXECUTOR

    @property
    def system_prompt(self) -> str:
        return f"""You are an Executor Agent - an expert in system operations and automation.

## Your Capabilities
1. **shell_execute** - Run shell/terminal commands
2. **file_manager** - Read, write, delete, and organize files
3. **api_caller** - Make HTTP API requests
4. **send_email** - Send emails (requires confirmation)

## How to Work (ReAct Pattern)
1. **Analyze** the system task requirements
2. **Plan** the sequence of operations
3. **Execute** commands carefully
4. **Verify** the results
5. **Report** the outcome

## Response Format
Always respond with JSON:
```json
{{
  "thought": "What system operation I'm planning",
  "action": "shell_execute",
  "action_input": {{
    "command": "the command to run",
    "working_dir": "optional/path"
  }},
  "is_dangerous": false
}}
```

For file operations:
```json
{{
  "thought": "File operation description",
  "action": "file_manager",
  "action_input": {{
    "action": "read|write|delete|list",
    "path": "file/path",
    "content": "for write operations"
  }}
}}
```

For final response:
```json
{{
  "thought": "Task completed",
  "action": "final_answer",
  "action_input": {{
    "summary": "What was accomplished",
    "files_modified": ["list", "of", "files"],
    "commands_executed": ["list", "of", "commands"]
  }}
}}
```

## Safety Guidelines
- NEVER run destructive commands without marking is_dangerous: true
- Destructive commands include: rm, del, format, kill, shutdown
- Always verify paths before file operations
- Check command syntax before executing
- Report any errors immediately

## Dangerous Command Indicators
Set "is_dangerous": true for any command that:
- Deletes files or directories
- Modifies system settings
- Kills processes
- Sends data externally
- Requires elevated privileges

Current date: {datetime.now().strftime("%Y-%m-%d")}
"""

    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None,
        max_steps: int = 10
    ) -> AgentResult:
        """Execute a system task"""
        start_time = datetime.now()
        self.state = AgentState.THINKING
        self.thoughts = []
        context = context or {}
        files_modified = []
        commands_executed = []

        self.emit_event("executor_start", {"task": task})

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=f"System Task: {task}\n\nContext: {json.dumps(context) if context else 'None'}")
        ]

        step = 0
        final_answer = ""

        while step < max_steps:
            step += 1
            self.state = AgentState.THINKING

            # Get LLM response
            response = await self.llm.chat(messages)
            content = response.content

            # Parse the response
            try:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    action_data = json.loads(content[json_start:json_end])
                else:
                    action_data = {"action": "final_answer", "action_input": {"summary": content}}
            except json.JSONDecodeError:
                action_data = {"action": "final_answer", "action_input": {"summary": content}}

            thought = action_data.get("thought", "")
            action = action_data.get("action", "")
            action_input = action_data.get("action_input", {})
            is_dangerous = action_data.get("is_dangerous", False)

            self.emit_event("executor_thought", {
                "step": step,
                "thought": thought,
                "action": action,
                "is_dangerous": is_dangerous
            })

            # Record thought
            thought_step = ThoughtStep(
                step_number=step,
                thought=thought,
                action=action,
                action_input=action_input
            )

            # Check if this is the final answer
            if action == "final_answer":
                final_answer = action_input.get("summary", "")
                thought_step.observation = "Task completed"
                self.thoughts.append(thought_step)
                break

            # Check for dangerous commands
            if self.confirm_dangerous and is_dangerous:
                self.state = AgentState.WAITING_CONFIRMATION
                self.pending_confirmation = {
                    "action": action,
                    "action_input": action_input,
                    "reason": thought
                }

                self.emit_event("executor_confirmation_required", {
                    "action": action,
                    "action_input": action_input,
                    "reason": "This action is marked as potentially dangerous"
                })

                # In a real implementation, you'd wait for user confirmation
                # For now, we'll skip dangerous actions
                observation = "Action skipped - requires user confirmation"
                thought_step.observation = observation
                self.thoughts.append(thought_step)

                messages.append(Message(role="assistant", content=content))
                messages.append(Message(role="user", content=f"Observation: {observation}\n\nFind an alternative approach or skip this action."))
                continue

            # Execute tool
            self.state = AgentState.EXECUTING
            observation = ""

            if action == "shell_execute" and "shell_execute" in self.tools:
                command = action_input.get("command", "")
                commands_executed.append(command)

                self.emit_event("executor_shell", {
                    "command": command
                })

                try:
                    tool = self.tools["shell_execute"]
                    result = await tool.execute(**action_input)
                    observation = result.output if result.success else f"Error: {result.error}"
                except Exception as e:
                    observation = f"Command failed: {str(e)}"

            elif action == "file_manager" and "file_manager" in self.tools:
                file_action = action_input.get("action", "")
                path = action_input.get("path", "")

                if file_action in ["write", "delete"]:
                    files_modified.append(path)

                try:
                    tool = self.tools["file_manager"]
                    result = await tool.execute(**action_input)
                    observation = result.output if result.success else f"Error: {result.error}"
                except Exception as e:
                    observation = f"File operation failed: {str(e)}"

            elif action in self.tools:
                try:
                    tool = self.tools[action]
                    result = await tool.execute(**action_input)
                    observation = result.output if result.success else f"Error: {result.error}"
                except Exception as e:
                    observation = f"Tool error: {str(e)}"
            else:
                observation = f"Unknown action: {action}"

            thought_step.observation = observation
            self.thoughts.append(thought_step)

            # Add observation to messages
            messages.append(Message(role="assistant", content=content))
            messages.append(Message(role="user", content=f"Observation: {observation}\n\nContinue with the task."))

        execution_time = (datetime.now() - start_time).total_seconds()
        self.state = AgentState.COMPLETED

        self.emit_event("executor_complete", {
            "steps": step,
            "commands_executed": len(commands_executed),
            "files_modified": len(files_modified),
            "execution_time": execution_time
        })

        return AgentResult(
            success=True,
            output=final_answer or f"Executed {len(commands_executed)} commands, modified {len(files_modified)} files",
            thoughts=self.thoughts,
            artifacts={
                "commands_executed": commands_executed,
                "files_modified": files_modified
            },
            execution_time=execution_time
        )
