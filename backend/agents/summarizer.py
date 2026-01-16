"""
Summarizer Agent - Content summarization specialist
"""
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, AgentResult, ThoughtStep, AgentState
from llm.base import Message


class SummarizerAgent(BaseAgent):
    """
    Content summarization specialist.

    Capabilities:
    - Summarize long text content
    - Extract key points and insights
    - Create different summary formats (bullet points, executive summary, etc.)
    - Summarize multiple documents
    - Generate abstracts and TLDRs
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.ANALYST

    @property
    def system_prompt(self) -> str:
        return """You are a Summarization Agent specialized in distilling complex information into clear, concise summaries.

Your expertise includes:
1. Extracting key points from long documents
2. Creating executive summaries
3. Generating bullet-point summaries
4. Identifying main themes and insights
5. Creating TLDRs (Too Long; Didn't Read)

When summarizing content:
1. Identify the main topic and purpose
2. Extract the most important points
3. Maintain factual accuracy
4. Preserve the original tone when appropriate
5. Be concise but comprehensive

Summary Formats:
- TLDR: 1-2 sentences capturing the essence
- Bullet Points: Key points as a list
- Executive Summary: Formal overview for business context
- Abstract: Academic-style summary
- Key Insights: Focus on actionable insights

Always maintain accuracy and avoid adding information not present in the source."""

    async def execute(
        self,
        task: str,
        context: Dict[str, Any] = None,
        max_steps: int = 3
    ) -> AgentResult:
        """
        Summarize content based on the task description.
        """
        start_time = datetime.now()
        self.state = AgentState.THINKING
        self.thoughts = []
        context = context or {}

        self.emit_event("summarizer_start", {"task": task[:100]})

        try:
            messages = [
                Message(role="system", content=self.system_prompt),
                Message(role="user", content=task)
            ]

            if context and "content" in context:
                messages.append(Message(
                    role="user",
                    content=f"Content to summarize:\n\n{context['content']}"
                ))

            self.emit_event("summarizer_thinking", {"action": "summarizing"})

            response = await self.llm.chat(messages)

            # Record thought
            thought_step = ThoughtStep(
                step_number=1,
                thought="Analyzing content and creating summary",
                action="summarize",
                observation=f"Generated summary of length {len(response.content)}"
            )
            self.thoughts.append(thought_step)

            execution_time = (datetime.now() - start_time).total_seconds()
            self.state = AgentState.COMPLETED

            self.emit_event("summarizer_complete", {
                "success": True,
                "response_length": len(response.content),
                "execution_time": execution_time
            })

            return AgentResult(
                success=True,
                output=response.content,
                thoughts=self.thoughts,
                execution_time=execution_time
            )

        except Exception as e:
            self.state = AgentState.FAILED
            execution_time = (datetime.now() - start_time).total_seconds()

            self.emit_event("summarizer_error", {"error": str(e)})

            return AgentResult(
                success=False,
                output=f"Summarization failed: {str(e)}",
                error=str(e),
                thoughts=self.thoughts,
                execution_time=execution_time
            )

    async def summarize(
        self,
        content: str,
        format: str = "bullet_points",
        max_length: Optional[int] = None
    ) -> AgentResult:
        """
        Summarize content in a specific format.

        Args:
            content: The text to summarize
            format: One of "tldr", "bullet_points", "executive", "abstract", "insights"
            max_length: Optional maximum length for the summary
        """
        format_instructions = {
            "tldr": "Create a TLDR (1-2 sentences max) that captures the essence.",
            "bullet_points": "Create a bullet-point summary with key points.",
            "executive": "Create a formal executive summary suitable for business context.",
            "abstract": "Create an academic-style abstract.",
            "insights": "Extract key insights and actionable takeaways."
        }

        instruction = format_instructions.get(format, format_instructions["bullet_points"])

        if max_length:
            instruction += f" Keep it under {max_length} words."

        task = f"""{instruction}

Content:
{content}"""

        return await self.execute(task)

    async def summarize_multiple(
        self,
        documents: List[Dict[str, str]],
        combined: bool = True
    ) -> AgentResult:
        """
        Summarize multiple documents.

        Args:
            documents: List of {"title": str, "content": str}
            combined: If True, create one combined summary. If False, summarize each separately.
        """
        if combined:
            combined_content = "\n\n---\n\n".join([
                f"Document: {doc.get('title', 'Untitled')}\n{doc['content']}"
                for doc in documents
            ])

            task = f"""Summarize the following {len(documents)} documents into a unified summary that captures the main points from all of them:

{combined_content}"""

            return await self.execute(task)
        else:
            summaries = []
            for doc in documents:
                result = await self.summarize(
                    doc["content"],
                    format="bullet_points"
                )
                summaries.append({
                    "title": doc.get("title", "Untitled"),
                    "summary": result.output
                })

            return AgentResult(
                success=True,
                output=json.dumps(summaries, indent=2),
                artifacts={"summaries": summaries},
                thoughts=self.thoughts,
                execution_time=0.0
            )

    async def extract_key_points(
        self,
        content: str,
        num_points: int = 5
    ) -> AgentResult:
        """
        Extract a specific number of key points from content.
        """
        task = f"""Extract exactly {num_points} key points from the following content.
Format each point as a single, clear sentence.

Content:
{content}"""

        return await self.execute(task)

    async def compare_and_summarize(
        self,
        content1: str,
        content2: str,
        labels: tuple = ("Document 1", "Document 2")
    ) -> AgentResult:
        """
        Compare two pieces of content and summarize similarities and differences.
        """
        task = f"""Compare and summarize the following two documents:

{labels[0]}:
{content1}

{labels[1]}:
{content2}

Provide:
1. A brief summary of each document
2. Key similarities between them
3. Key differences between them
4. Overall conclusion"""

        return await self.execute(task)
