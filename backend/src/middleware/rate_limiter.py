import time
from typing import Dict, List
from fastapi import Request, HTTPException, status  # type: ignore


class SlidingWindowRateLimiter:
    def __init__(self):
        # Maps key (IP / client_id) -> list of timestamp floats
        self._history: Dict[str, List[float]] = {}

    def is_allowed(self, client_key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds

        if client_key not in self._history:
            self._history[client_key] = []

        # Filter out timestamps older than the window
        timestamps = [ts for ts in self._history[client_key] if ts > cutoff]
        self._history[client_key] = timestamps

        if len(timestamps) >= max_requests:
            oldest_ts = timestamps[0]
            retry_after = int(oldest_ts + window_seconds - now) + 1
            return False, max(1, retry_after)

        self._history[client_key].append(now)
        return True, 0


from src.config.settings import settings

# Global singleton instance
rate_limiter = SlidingWindowRateLimiter()


def rate_limit(max_requests: int = 30, window_seconds: int = 60):
    """FastAPI dependency factory enforcing rate limits per client IP."""
    async def _rate_limit_dependency(request: Request):
        if settings.ENVIRONMENT == "testing":
            return

        client_ip = request.client.host if request.client else "127.0.0.1"
        # Combine IP and endpoint path for granular per-route rate limiting
        key = f"{client_ip}:{request.url.path}"

        allowed, retry_after = rate_limiter.is_allowed(key, max_requests, window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds}s allowed. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

    return _rate_limit_dependency

