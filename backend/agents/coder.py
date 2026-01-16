import json
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, AgentResult, ThoughtStep, AgentState
from llm.base import Message, ToolDefinition


class CoderAgent(BaseAgent):
    """
    The Coder Agent specializes in code generation, execution, and debugging.
    It can write Python code, execute it, and fix errors iteratively.
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.CODER

    @property
    def system_prompt(self) -> str:
        return f"""You are a Coder Agent - an expert programmer and debugger.

## Your Capabilities
1. **code_executor** - Write and execute Python code
2. **file_manager** - Read and write code files
3. **shell_execute** - Run shell commands (with user confirmation)

## How to Work (ReAct Pattern)
For each step:
1. **Thought**: Plan what code to write or debug
2. **Action**: Write and execute code
3. **Observation**: Check the output or errors
4. **Reflection**: If errors, debug and retry

## Response Format
Always respond with JSON:
```json
{{
  "thought": "What I'm planning to code",
  "action": "code_executor",
  "action_input": {{
    "code": "your_python_code_here",
    "save_as": "optional_filename.py"
  }}
}}
```

When the task is complete:
```json
{{
  "thought": "Code executed successfully",
  "action": "final_answer",
  "action_input": {{
    "answer": "Summary of what was done",
    "code": "final_code",
    "output": "execution_output"
  }}
}}
```

## Guidelines
- Write clean, well-documented code
- Handle errors gracefully
- If code fails, analyze the error and fix it
- Use appropriate libraries for the task
- Test your code before finalizing
- Max 3 retry attempts for debugging

## Available Python Libraries
- pandas, numpy for data processing
- matplotlib, seaborn for visualization
- requests for HTTP requests
- beautifulsoup4 for HTML parsing
- json, csv, os, sys for utilities

Current date: {datetime.now().strftime("%Y-%m-%d")}
"""

    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None,
        max_steps: int = 10
    ) -> AgentResult:
        """Execute a coding task"""
        start_time = datetime.now()
        self.state = AgentState.THINKING
        self.thoughts = []
        context = context or {}
        retry_count = 0
        max_retries = 3

        self.emit_event("coder_start", {"task": task})

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=f"Coding Task: {task}\n\nContext: {json.dumps(context) if context else 'None'}")
        ]

        step = 0
        final_answer = ""
        final_code = ""
        last_error = ""

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
                    action_data = {"action": "final_answer", "action_input": {"answer": content}}
            except json.JSONDecodeError:
                action_data = {"action": "final_answer", "action_input": {"answer": content}}

            thought = action_data.get("thought", "")
            action = action_data.get("action", "")
            action_input = action_data.get("action_input", {})

            self.emit_event("coder_thought", {
                "step": step,
                "thought": thought,
                "action": action
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
                final_answer = action_input.get("answer", "")
                final_code = action_input.get("code", "")
                thought_step.observation = "Task completed"
                self.thoughts.append(thought_step)
                break

            # Execute tool
            self.state = AgentState.EXECUTING
            observation = ""

            if action == "code_executor" and "code_executor" in self.tools:
                code = action_input.get("code", "")
                save_as = action_input.get("save_as")

                self.emit_event("coder_executing", {
                    "code_preview": code[:200] + "..." if len(code) > 200 else code,
                    "save_as": save_as
                })

                try:
                    tool = self.tools["code_executor"]
                    result = await tool.execute(code=code, save_as=save_as)

                    if result.success:
                        observation = result.output
                        last_error = ""
                        final_code = code

                        self.emit_event("coder_success", {
                            "output_preview": observation[:300]
                        })
                    else:
                        observation = f"Error: {result.error}"
                        last_error = result.error
                        retry_count += 1

                        self.emit_event("coder_error", {
                            "error": result.error,
                            "retry_count": retry_count
                        })

                        if retry_count >= max_retries:
                            observation += f"\nMax retries ({max_retries}) reached."

                except Exception as e:
                    observation = f"Execution failed: {str(e)}"
                    last_error = str(e)
                    retry_count += 1

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

            if last_error and retry_count < max_retries:
                messages.append(Message(role="user", content=f"""
Observation: {observation}

The code had an error. Please analyze and fix it.
Error: {last_error}

Debug and provide corrected code.
"""))
            else:
                messages.append(Message(role="user", content=f"Observation: {observation}\n\nContinue with the task."))

        execution_time = (datetime.now() - start_time).total_seconds()
        self.state = AgentState.COMPLETED

        self.emit_event("coder_complete", {
            "steps": step,
            "retries": retry_count,
            "execution_time": execution_time
        })

        return AgentResult(
            success=not bool(last_error),
            output=final_answer or f"Code executed. Final output:\n{self.thoughts[-1].observation if self.thoughts else ''}",
            thoughts=self.thoughts,
            artifacts={"code": final_code},
            error=last_error if last_error else None,
            execution_time=execution_time
        )
