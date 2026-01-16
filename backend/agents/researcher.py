import json
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, AgentResult, ThoughtStep, AgentState
from llm.base import Message, ToolDefinition


class ResearcherAgent(BaseAgent):
    """
    The Researcher Agent specializes in information gathering.
    It can search the web, read websites, and synthesize information.
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.RESEARCHER

    @property
    def system_prompt(self) -> str:
        return f"""You are a Researcher Agent - an expert at finding and synthesizing information.

## Your Capabilities
1. **web_search** - Search the internet using DuckDuckGo
2. **web_browser** - Fetch and read content from web pages
3. **pdf_reader** - Extract text from PDF documents

## How to Work (ReAct Pattern)
For each step:
1. **Thought**: Analyze what information is needed
2. **Action**: Choose and use a tool
3. **Observation**: Process the tool's output
4. **Reflection**: Evaluate if more research is needed

## Response Format
Always respond with JSON:
```json
{{
  "thought": "What I'm thinking about the task",
  "action": "tool_name or final_answer",
  "action_input": {{"param": "value"}},
  "confidence": 0.0-1.0
}}
```

When you have enough information:
```json
{{
  "thought": "I have gathered sufficient information",
  "action": "final_answer",
  "action_input": {{"answer": "Your comprehensive answer"}},
  "confidence": 0.95
}}
```

## Guidelines
- Always verify information from multiple sources when possible
- Cite your sources
- If information is uncertain, indicate the confidence level
- Summarize key findings clearly
- Look for the most recent and authoritative sources

Current date: {datetime.now().strftime("%Y-%m-%d")}
"""

    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None,
        max_steps: int = 8
    ) -> AgentResult:
        """Execute a research task"""
        start_time = datetime.now()
        self.state = AgentState.THINKING
        self.thoughts = []
        context = context or {}

        self.emit_event("researcher_start", {"task": task})

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=f"Research Task: {task}\n\nContext: {json.dumps(context) if context else 'None'}")
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
                    action_data = {"action": "final_answer", "action_input": {"answer": content}}
            except json.JSONDecodeError:
                action_data = {"action": "final_answer", "action_input": {"answer": content}}

            thought = action_data.get("thought", "")
            action = action_data.get("action", "")
            action_input = action_data.get("action_input", {})

            self.emit_event("researcher_thought", {
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
                final_answer = action_input.get("answer", content)
                thought_step.observation = "Task completed"
                self.thoughts.append(thought_step)
                break

            # Execute tool
            self.state = AgentState.EXECUTING
            if action in self.tools:
                try:
                    tool = self.tools[action]
                    result = await tool.execute(**action_input)
                    observation = result.output if result.success else f"Error: {result.error}"

                    self.emit_event("researcher_tool_result", {
                        "tool": action,
                        "success": result.success,
                        "output_preview": observation[:300]
                    })
                except Exception as e:
                    observation = f"Tool error: {str(e)}"
            else:
                observation = f"Unknown tool: {action}"

            thought_step.observation = observation
            self.thoughts.append(thought_step)

            # Add observation to messages
            messages.append(Message(role="assistant", content=content))
            messages.append(Message(role="user", content=f"Observation: {observation}\n\nContinue with your research."))

        execution_time = (datetime.now() - start_time).total_seconds()
        self.state = AgentState.COMPLETED

        self.emit_event("researcher_complete", {
            "steps": step,
            "execution_time": execution_time
        })

        return AgentResult(
            success=True,
            output=final_answer,
            thoughts=self.thoughts,
            execution_time=execution_time
        )
