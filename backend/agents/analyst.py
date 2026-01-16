import json
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, AgentResult, ThoughtStep, AgentState
from llm.base import Message, ToolDefinition


class AnalystAgent(BaseAgent):
    """
    The Analyst Agent specializes in data analysis and visualization.
    It can process data, generate insights, and create charts.
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.ANALYST

    @property
    def system_prompt(self) -> str:
        return f"""You are an Analyst Agent - an expert in data analysis and visualization.

## Your Capabilities
1. **code_executor** - Run Python code for data analysis
2. **file_manager** - Read data files and save results
3. **web_browser** - Fetch data from APIs

## Specializations
- Statistical analysis
- Data cleaning and transformation
- Visualization (matplotlib, seaborn)
- Pattern recognition
- Generating insights and recommendations

## How to Work (ReAct Pattern)
1. **Understand** the data and analysis requirements
2. **Plan** the analysis approach
3. **Execute** using Python with pandas, numpy, matplotlib
4. **Interpret** the results
5. **Visualize** key findings
6. **Summarize** insights

## Response Format
Always respond with JSON:
```json
{{
  "thought": "Analysis plan or insight",
  "action": "code_executor",
  "action_input": {{
    "code": "import pandas as pd\\nimport matplotlib.pyplot as plt\\n...",
    "save_as": "analysis.py"
  }}
}}
```

For final analysis:
```json
{{
  "thought": "Analysis complete",
  "action": "final_answer",
  "action_input": {{
    "summary": "Key findings summary",
    "insights": ["insight1", "insight2"],
    "recommendations": ["recommendation1"],
    "visualizations": ["chart1.png"]
  }}
}}
```

## Analysis Guidelines
- Always validate data quality first
- Use appropriate statistical methods
- Create clear, informative visualizations
- Provide actionable insights
- Save charts to the workspace folder

## Visualization Code Template
```python
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10, 6))
# Your plot code here
plt.title('Title')
plt.tight_layout()
plt.savefig('workspace/chart_name.png', dpi=150)
plt.close()
print("Chart saved to workspace/chart_name.png")
```

Current date: {datetime.now().strftime("%Y-%m-%d")}
"""

    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None,
        max_steps: int = 10
    ) -> AgentResult:
        """Execute an analysis task"""
        start_time = datetime.now()
        self.state = AgentState.THINKING
        self.thoughts = []
        context = context or {}

        self.emit_event("analyst_start", {"task": task})

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=f"Analysis Task: {task}\n\nContext: {json.dumps(context) if context else 'None'}")
        ]

        step = 0
        final_answer = ""
        visualizations = []
        insights = []

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

            self.emit_event("analyst_thought", {
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
                final_answer = action_input.get("summary", "")
                insights = action_input.get("insights", [])
                visualizations = action_input.get("visualizations", [])
                thought_step.observation = "Analysis completed"
                self.thoughts.append(thought_step)
                break

            # Execute tool
            self.state = AgentState.EXECUTING
            observation = ""

            if action in self.tools:
                try:
                    tool = self.tools[action]
                    result = await tool.execute(**action_input)
                    observation = result.output if result.success else f"Error: {result.error}"

                    # Track visualizations created
                    if "savefig" in str(action_input.get("code", "")):
                        self.emit_event("analyst_visualization", {
                            "output": observation[:200]
                        })

                except Exception as e:
                    observation = f"Tool error: {str(e)}"
            else:
                observation = f"Unknown action: {action}"

            thought_step.observation = observation
            self.thoughts.append(thought_step)

            # Add observation to messages
            messages.append(Message(role="assistant", content=content))
            messages.append(Message(role="user", content=f"Observation: {observation}\n\nContinue with the analysis."))

        execution_time = (datetime.now() - start_time).total_seconds()
        self.state = AgentState.COMPLETED

        self.emit_event("analyst_complete", {
            "steps": step,
            "insights_count": len(insights),
            "visualizations_count": len(visualizations),
            "execution_time": execution_time
        })

        return AgentResult(
            success=True,
            output=final_answer,
            thoughts=self.thoughts,
            artifacts={
                "insights": insights,
                "visualizations": visualizations
            },
            execution_time=execution_time
        )
