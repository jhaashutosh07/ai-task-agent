from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import asyncio
import time


class RateLimiter:
    """
    Sliding window rate limiter.
    Tracks requests per IP and per user (if authenticated).
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,  # Max requests in 1 second
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit

        # Storage: {identifier: [(timestamp, endpoint), ...]}
        self._requests: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        self._lock = asyncio.Lock()

        # Cleanup task
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

    def _get_identifier(self, request: Request, user_id: Optional[str] = None) -> str:
        """Get rate limit identifier (user_id or IP)"""
        if user_id:
            return f"user:{user_id}"
        return f"ip:{request.client.host}"

    async def _cleanup_old_requests(self):
        """Remove requests older than 1 hour"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        async with self._lock:
            cutoff = now - 3600  # 1 hour ago
            for identifier in list(self._requests.keys()):
                self._requests[identifier] = [
                    (ts, ep) for ts, ep in self._requests[identifier]
                    if ts > cutoff
                ]
                if not self._requests[identifier]:
                    del self._requests[identifier]
            self._last_cleanup = now

    async def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[dict]]:
        """
        Check if request is within rate limits.
        Returns (allowed, error_info)
        """
        await self._cleanup_old_requests()

        identifier = self._get_identifier(request, user_id)
        now = time.time()
        endpoint = request.url.path

        async with self._lock:
            requests = self._requests[identifier]

            # Count requests in different windows
            one_second_ago = now - 1
            one_minute_ago = now - 60
            one_hour_ago = now - 3600

            burst_count = sum(1 for ts, _ in requests if ts > one_second_ago)
            minute_count = sum(1 for ts, _ in requests if ts > one_minute_ago)
            hour_count = sum(1 for ts, _ in requests if ts > one_hour_ago)

            # Check limits
            if burst_count >= self.burst_limit:
                return False, {
                    "error": "Rate limit exceeded",
                    "detail": "Too many requests per second",
                    "retry_after": 1,
                    "limit": self.burst_limit,
                    "window": "1s"
                }

            if minute_count >= self.requests_per_minute:
                retry_after = 60 - (now - min(ts for ts, _ in requests if ts > one_minute_ago))
                return False, {
                    "error": "Rate limit exceeded",
                    "detail": "Too many requests per minute",
                    "retry_after": int(retry_after) + 1,
                    "limit": self.requests_per_minute,
                    "window": "1m"
                }

            if hour_count >= self.requests_per_hour:
                retry_after = 3600 - (now - min(ts for ts, _ in requests if ts > one_hour_ago))
                return False, {
                    "error": "Rate limit exceeded",
                    "detail": "Too many requests per hour",
                    "retry_after": int(retry_after) + 1,
                    "limit": self.requests_per_hour,
                    "window": "1h"
                }

            # Record this request
            self._requests[identifier].append((now, endpoint))

            return True, None

    def get_remaining(self, request: Request, user_id: Optional[str] = None) -> dict:
        """Get remaining requests in each window"""
        identifier = self._get_identifier(request, user_id)
        now = time.time()

        requests = self._requests.get(identifier, [])

        one_second_ago = now - 1
        one_minute_ago = now - 60
        one_hour_ago = now - 3600

        burst_count = sum(1 for ts, _ in requests if ts > one_second_ago)
        minute_count = sum(1 for ts, _ in requests if ts > one_minute_ago)
        hour_count = sum(1 for ts, _ in requests if ts > one_hour_ago)

        return {
            "burst_remaining": max(0, self.burst_limit - burst_count),
            "minute_remaining": max(0, self.requests_per_minute - minute_count),
            "hour_remaining": max(0, self.requests_per_hour - hour_count)
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        from config import settings
        _rate_limiter = RateLimiter(
            requests_per_minute=settings.rate_limit_per_minute,
            requests_per_hour=settings.rate_limit_per_hour,
            burst_limit=settings.rate_limit_burst
        )
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(self, app, rate_limiter: RateLimiter = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or get_rate_limiter()

        # Paths to exclude from rate limiting
        self.excluded_paths = {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/health"
        }

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Get user_id if authenticated (check for user in request state)
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.id

        # Check rate limit
        allowed, error_info = await self.rate_limiter.check_rate_limit(request, user_id)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_info,
                headers={
                    "Retry-After": str(error_info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(error_info.get("limit", 60)),
                    "X-RateLimit-Window": error_info.get("window", "1m")
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)

        remaining = self.rate_limiter.get_remaining(request, user_id)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining["minute_remaining"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining["hour_remaining"])

        return response


# Dependency for manual rate limit checking
async def rate_limit_middleware(request: Request):
    """Dependency to check rate limits"""
    rate_limiter = get_rate_limiter()

    user_id = None
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.id

    allowed, error_info = await rate_limiter.check_rate_limit(request, user_id)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_info
        )
