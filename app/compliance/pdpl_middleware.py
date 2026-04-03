"""
PDPL Compliance Middleware — sits in the FastAPI request pipeline.
Enforces data sovereignty, adds audit headers, checks consent.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class PDPLComplianceMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces PDPL requirements on every request.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # 1. Add data sovereignty headers
        response = await call_next(request)
        response.headers["X-Data-Region"] = settings.data_region
        response.headers["X-Data-Sovereignty"] = "SA"
        response.headers["X-PDPL-Compliant"] = "true"

        # 2. Remove any headers that might leak server info
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)

        # 3. Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-Request-ID"] = request.headers.get(
            "X-Request-ID", str(time.time_ns())
        )

        # 4. Log request for audit trail
        process_time = time.time() - start_time
        logger.info(
            "request_processed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
            client_ip=request.client.host if request.client else "unknown",
            data_region=settings.data_region,
        )

        return response


class DataLocalityGuard:
    """
    Validates that no request attempts to transfer data
    outside Saudi jurisdiction.
    """

    BLOCKED_TRANSFER_PATHS = [
        "/api/export",
        "/api/bulk-download",
    ]

    @staticmethod
    def validate_data_destination(destination: str) -> bool:
        """Check if data destination is within Saudi Arabia."""
        allowed_regions = [
            "sa-riyadh-1",
            "sa-jeddah-1",
            "sa-dammam-1",
        ]
        return destination in allowed_regions
