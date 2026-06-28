"""
Reflection Engine (self-critique loop)
======================================
Implements a lightweight Reflexion-style pattern: after an answer is produced,
the model critiques its own output against the original question and, if it
finds a meaningful issue, rewrites an improved version.

This is bounded to a single refinement pass to keep latency/cost predictable.
"""
from typing import Tuple

from llm.base import Message


class ReflectionEngine:
    def __init__(self, llm):
        self.llm = llm

    async def refine(self, question: str, answer: str, context: str = "") -> Tuple[str, str]:
        """
        Returns (final_answer, critique).
        If the critique decides the answer is already good, the original is kept.
        """
        if not answer or not answer.strip():
            return answer, ""

        ctx_block = f"\n\nReference material the answer should be consistent with:\n{context}\n" if context else ""

        critique_prompt = (
            "You are a meticulous reviewer. Critique the assistant's answer to the user's "
            "question for correctness, completeness, and clarity. Be concise.\n"
            f"\nUser question:\n{question}\n"
            f"{ctx_block}"
            f"\nAssistant answer:\n{answer}\n\n"
            "If the answer is already accurate and complete, reply with exactly: OK\n"
            "Otherwise, in 1-2 sentences state the single most important problem to fix."
        )
        try:
            critique_resp = await self.llm.chat([Message(role="user", content=critique_prompt)])
            critique = (critique_resp.content or "").strip()
        except Exception:
            return answer, ""

        if not critique or critique.upper().startswith("OK"):
            return answer, "OK"

        improve_prompt = (
            "Improve the assistant's answer using the reviewer's feedback. "
            "Keep everything that was correct; fix only what the feedback identifies. "
            "Return ONLY the improved answer, with no preamble.\n"
            f"\nUser question:\n{question}\n"
            f"{ctx_block}"
            f"\nOriginal answer:\n{answer}\n"
            f"\nReviewer feedback:\n{critique}\n"
        )
        try:
            improved_resp = await self.llm.chat([Message(role="user", content=improve_prompt)])
            improved = (improved_resp.content or "").strip()
            return (improved or answer), critique
        except Exception:
            return answer, critique
