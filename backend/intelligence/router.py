"""
Intent Router
=============
Classifies an incoming message so the system can pick the cheapest correct path:

- **chat**  → a single conversational LLM call (fast, low cost). Greetings,
              definitions, opinions, follow-ups, "explain X".
- **task**  → the full multi-agent orchestrator (web search, code execution,
              file ops, multi-step reasoning).

Uses a cheap heuristic first (zero cost) and falls back to a tightly-scoped
LLM classification only when the heuristic is unsure.
"""
import re
from enum import Enum
from typing import Optional

from llm.base import Message


class Intent(str, Enum):
    CHAT = "chat"
    TASK = "task"


# Verbs / phrases that strongly imply a multi-step, tool-using task.
_TASK_SIGNALS = re.compile(
    r"\b(search|google|look up|browse|scrape|fetch|download|"
    r"run|execute|compile|debug|write a (script|program|function)|"
    r"create (a )?(file|report|chart|graph|csv|table)|save|generate a file|"
    r"analys|analyz|visuali|plot|scrape|automate|schedule|send (an )?email|"
    r"build|deploy|install|api call|query the|crawl)\b",
    re.IGNORECASE,
)

# Obvious small-talk / conversational openers.
_CHAT_SIGNALS = re.compile(
    r"^\s*(hi|hii+|hey|hello|yo|sup|good (morning|afternoon|evening)|"
    r"thanks?|thank you|thx|ok(ay)?|cool|nice|great|who are you|"
    r"what can you do|how are you|help)\b",
    re.IGNORECASE,
)


class IntentRouter:
    def __init__(self, llm=None):
        self.llm = llm

    def heuristic(self, message: str) -> Optional[Intent]:
        text = message.strip()
        if not text:
            return Intent.CHAT
        # Very short messages are almost always chit-chat.
        words = text.split()
        if _CHAT_SIGNALS.search(text) and len(words) <= 6:
            return Intent.CHAT
        if _TASK_SIGNALS.search(text):
            return Intent.TASK
        if len(words) <= 4 and "?" not in text:
            return Intent.CHAT
        return None  # unsure → let the LLM decide

    async def classify(self, message: str) -> Intent:
        decided = self.heuristic(message)
        if decided is not None:
            return decided
        if not self.llm:
            # Default to chat for ambiguous, single-sentence questions.
            return Intent.TASK if len(message.split()) > 25 else Intent.CHAT

        prompt = (
            "Classify the user's message into exactly one label.\n"
            "- 'task': needs tools or multiple steps (web search, running/writing code, "
            "file creation, data analysis, automation, sending email).\n"
            "- 'chat': can be answered directly in conversation (greetings, explanations, "
            "definitions, opinions, brainstorming, general Q&A).\n\n"
            f"Message: \"{message}\"\n\n"
            "Reply with only one word: task or chat."
        )
        try:
            resp = await self.llm.chat([Message(role="user", content=prompt)])
            answer = (resp.content or "").strip().lower()
            return Intent.TASK if "task" in answer else Intent.CHAT
        except Exception:
            return Intent.CHAT
