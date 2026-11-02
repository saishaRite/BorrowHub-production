import time
from collections import defaultdict
from fastapi import HTTPException, status, Request
from backend.app.core.config import settings

# In-memory sliding window rate limiter
_request_records = defaultdict(list)


def check_rate_limit(key: str, max_requests: int = 30, window_seconds: int = 60):
    """
    Check if a key (e.g. IP address or email) has exceeded max_requests in window_seconds.
    Raises HTTPException(429) if exceeded.
    """
    if settings.ENVIRONMENT == "test":
        return

    now = time.time()
    records = _request_records[key]
    _request_records[key] = [t for t in records if now - t < window_seconds]
    if len(_request_records[key]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down and try again later.",
        )
    _request_records[key].append(now)


async def rate_limit_auth(request: Request):
    """Rate limit dependency for sensitive auth endpoints."""
    if settings.ENVIRONMENT == "test":
        return
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"auth:{client_ip}", max_requests=100, window_seconds=60)
