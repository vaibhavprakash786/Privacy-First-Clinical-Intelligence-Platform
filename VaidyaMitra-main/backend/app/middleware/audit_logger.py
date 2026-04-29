"""
Audit Logger Middleware

Structured logging for all API requests — CloudWatch-ready JSON format.
Logs request metadata, response status, duration, and error details.
"""

import json
import logging
import time
import uuid
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("audit")


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """Structured audit logging middleware with CloudWatch-compatible JSON output."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # Attach request ID
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)

            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "status": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", "")[:100],
            }

            if response.status_code >= 400:
                logger.warning(json.dumps(log_entry))
            else:
                logger.info(json.dumps(log_entry))

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"
            return response

        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "status": 500,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "error": str(e),
            }))
            raise
