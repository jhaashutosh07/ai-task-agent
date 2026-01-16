"""
Cost Tracker - Track LLM usage costs per provider and user
"""
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """Record of a single LLM usage."""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    timestamp: datetime
    user_id: Optional[str] = None
    request_type: str = "chat"  # chat, vision, embedding


@dataclass
class UsageSummary:
    """Summary of usage statistics."""
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    requests_by_provider: dict = field(default_factory=dict)
    costs_by_provider: dict = field(default_factory=dict)
    requests_by_model: dict = field(default_factory=dict)


class CostTracker:
    """
    Tracks LLM usage costs across providers and users.

    Features:
    - Per-request cost calculation
    - Per-user usage tracking
    - Per-provider statistics
    - Time-based summaries
    """

    # Cost per 1K tokens (input, output) for known models
    MODEL_COSTS = {
        # OpenAI
        "gpt-4o": (0.005, 0.015),
        "gpt-4o-mini": (0.00015, 0.0006),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.0005, 0.0015),
        # Anthropic
        "claude-3-5-sonnet-20241022": (0.003, 0.015),
        "claude-3-opus-20240229": (0.015, 0.075),
        "claude-3-haiku-20240307": (0.00025, 0.00125),
        # Google
        "gemini-1.5-pro": (0.00125, 0.005),
        "gemini-1.5-flash": (0.000075, 0.0003),
        "gemini-1.0-pro": (0.0005, 0.0015),
        # Ollama (local, free)
        "llama3.2": (0.0, 0.0),
        "llama3.1": (0.0, 0.0),
        "llama3": (0.0, 0.0),
        "mistral": (0.0, 0.0),
        "codellama": (0.0, 0.0),
    }

    def __init__(self, max_history: int = 10000):
        self.records: list[UsageRecord] = []
        self.max_history = max_history
        self._lock = asyncio.Lock()

        # In-memory aggregates for quick access
        self._user_totals: dict[str, float] = defaultdict(float)
        self._provider_totals: dict[str, float] = defaultdict(float)
        self._daily_totals: dict[str, float] = defaultdict(float)

    def get_model_costs(self, model: str) -> tuple[float, float]:
        """Get cost per 1K tokens for a model."""
        # Try exact match first
        if model in self.MODEL_COSTS:
            return self.MODEL_COSTS[model]

        # Try partial match
        for known_model, costs in self.MODEL_COSTS.items():
            if known_model in model or model in known_model:
                return costs

        # Default to GPT-4o pricing for unknown models
        logger.warning(f"Unknown model '{model}', using default pricing")
        return (0.005, 0.015)

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> tuple[float, float, float]:
        """
        Calculate cost for a request.

        Returns: (input_cost, output_cost, total_cost)
        """
        input_cost_per_1k, output_cost_per_1k = self.get_model_costs(model)
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        return input_cost, output_cost, total_cost

    async def record_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        request_type: str = "chat"
    ) -> UsageRecord:
        """Record a usage event."""
        input_cost, output_cost, total_cost = self.calculate_cost(
            model, input_tokens, output_tokens
        )

        record = UsageRecord(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            request_type=request_type
        )

        async with self._lock:
            self.records.append(record)

            # Update aggregates
            if user_id:
                self._user_totals[user_id] += total_cost
            self._provider_totals[provider] += total_cost

            date_key = record.timestamp.strftime("%Y-%m-%d")
            self._daily_totals[date_key] += total_cost

            # Trim history if needed
            if len(self.records) > self.max_history:
                self.records = self.records[-self.max_history:]

        logger.info(
            f"Recorded usage: {provider}/{model} - "
            f"{input_tokens}in/{output_tokens}out = ${total_cost:.6f}"
        )

        return record

    async def get_user_summary(
        self,
        user_id: str,
        since: Optional[datetime] = None
    ) -> UsageSummary:
        """Get usage summary for a specific user."""
        async with self._lock:
            filtered = [
                r for r in self.records
                if r.user_id == user_id and (since is None or r.timestamp >= since)
            ]

        return self._build_summary(filtered)

    async def get_provider_summary(
        self,
        provider: str,
        since: Optional[datetime] = None
    ) -> UsageSummary:
        """Get usage summary for a specific provider."""
        async with self._lock:
            filtered = [
                r for r in self.records
                if r.provider == provider and (since is None or r.timestamp >= since)
            ]

        return self._build_summary(filtered)

    async def get_total_summary(
        self,
        since: Optional[datetime] = None
    ) -> UsageSummary:
        """Get total usage summary."""
        async with self._lock:
            if since:
                filtered = [r for r in self.records if r.timestamp >= since]
            else:
                filtered = self.records.copy()

        return self._build_summary(filtered)

    def _build_summary(self, records: list[UsageRecord]) -> UsageSummary:
        """Build a summary from a list of records."""
        summary = UsageSummary()

        for record in records:
            summary.total_requests += 1
            summary.total_input_tokens += record.input_tokens
            summary.total_output_tokens += record.output_tokens
            summary.total_cost += record.total_cost

            # By provider
            if record.provider not in summary.requests_by_provider:
                summary.requests_by_provider[record.provider] = 0
                summary.costs_by_provider[record.provider] = 0.0
            summary.requests_by_provider[record.provider] += 1
            summary.costs_by_provider[record.provider] += record.total_cost

            # By model
            if record.model not in summary.requests_by_model:
                summary.requests_by_model[record.model] = 0
            summary.requests_by_model[record.model] += 1

        return summary

    async def get_daily_costs(self, days: int = 30) -> dict[str, float]:
        """Get daily cost totals for the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with self._lock:
            return {
                date: cost
                for date, cost in self._daily_totals.items()
                if datetime.strptime(date, "%Y-%m-%d") >= cutoff
            }

    async def get_user_total(self, user_id: str) -> float:
        """Get total cost for a user."""
        async with self._lock:
            return self._user_totals.get(user_id, 0.0)

    async def get_recent_records(
        self,
        limit: int = 100,
        user_id: Optional[str] = None
    ) -> list[UsageRecord]:
        """Get recent usage records."""
        async with self._lock:
            if user_id:
                filtered = [r for r in self.records if r.user_id == user_id]
            else:
                filtered = self.records.copy()

        return filtered[-limit:]

    def to_dict(self, summary: UsageSummary) -> dict:
        """Convert a summary to a dictionary for JSON serialization."""
        return {
            "total_requests": summary.total_requests,
            "total_input_tokens": summary.total_input_tokens,
            "total_output_tokens": summary.total_output_tokens,
            "total_cost": round(summary.total_cost, 6),
            "requests_by_provider": summary.requests_by_provider,
            "costs_by_provider": {
                k: round(v, 6) for k, v in summary.costs_by_provider.items()
            },
            "requests_by_model": summary.requests_by_model
        }


# Singleton instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def init_cost_tracker(max_history: int = 10000) -> CostTracker:
    """Initialize the global cost tracker."""
    global _cost_tracker
    _cost_tracker = CostTracker(max_history=max_history)
    return _cost_tracker
