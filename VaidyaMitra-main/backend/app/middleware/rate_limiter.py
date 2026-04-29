"""
Rate Limiter Middleware

Token-bucket rate limiting with per-IP tracking.
Ready for API Gateway integration in production.
"""

import logging
import time
from collections import defaultdict
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiter with per-IP tracking."""

    def __init__(self, app):
        super().__init__(app)
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE
        self.burst = settings.RATE_LIMIT_BURST
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (self.burst, time.time())
        )

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check
        if request.url.path in ["/", "/api/v1/health"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        tokens, last_time = self._buckets[client_ip]

        now = time.time()
        elapsed = now - last_time
        # Refill tokens
        tokens = min(self.burst, tokens + elapsed * (self.rate_limit / 60.0))

        if tokens < 1:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 60,
                    }
                },
                headers={"Retry-After": "60"},
            )

        tokens -= 1
        self._buckets[client_ip] = (tokens, now)
        return await call_next(request)
