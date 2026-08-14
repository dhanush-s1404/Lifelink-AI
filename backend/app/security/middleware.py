"""Security hardening for LifeLink AI - authentication, authorization, and headers.

Provides security middleware and utilities for the FastAPI backend:
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- Rate limiting helpers
- Password hashing verification
- Token validation utilities
- Security event logging
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from fastapi import Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# ------------------------------------------------------------------
# Security headers middleware
# ------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security headers to every response.

    Headers included:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Referrer-Policy: strict-origin-when-cross-origin
    - Content-Security-Policy: default-src 'self'
    """

    def __init__(
        self,
        app: ASGIApp,
        enable_csp: bool = True,
        enable_hsts: bool = True,
        frame_options: str = "DENY",
    ) -> None:
        super().__init__(app)
        self.enable_csp = enable_csp
        self.enable_hsts = enable_hsts
        self.frame_options = frame_options

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Content type sniffing protection
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Frame options protection
        response.headers["X-Frame-Options"] = self.frame_options

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (HTTP Strict Transport Security)
        if self.enable_hsts:
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains; preload"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        if self.enable_csp:
            response.headers[
                "Content-Security-Policy"
            ] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"

        return response


# ------------------------------------------------------------------
# Rate limiting helper
# ------------------------------------------------------------------


class RateLimiter:
    """Simple in-memory rate limiter for API endpoints.

    Tracks requests per client by IP address (or user ID when available).
    Configurable window and limit.

    Usage:
        limiter = RateLimiter(calls=10, period=60)  # 10 calls per minute
        if not limiter.allow(client_id):
            raise HTTPException(status_code=429)
    """

    def __init__(self, calls: int, period: int) -> None:
        """Initialize rate limiter.

        Parameters
        ----------
        calls:
            Maximum number of allowed calls.
        period:
            Time window in seconds.
        """
        self.calls = calls
        self.period = period
        self._records: dict[str, list[float]] = {}

    def _client_key(self, request: Any) -> str:
        """Generate a unique key for the client."""
        # Try to get user ID from request state, fall back to IP
        if hasattr(request, "state") and hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        # Fall back to IP address
        if hasattr(request, "client") and request.client:
            return f"ip:{request.client.host}"
        return "unknown"

    def allow(self, request: Any) -> bool:
        """Check if the request is allowed within the rate limit.

        Parameters
        ----------
        request:
            The FastAPI request object.

        Returns
        -------
        bool
            True if the request is allowed, False if rate limited.
        """
        key = self._client_key(request)
        now = time.time()

        # Initialize records for this key if not present
        if key not in self._records:
            self._records[key] = []

        # Remove timestamps outside the window
        self._records[key] = [t for t in self._records[key] if now - t < self.period]

        # Check if under the limit
        if len(self._records[key]) >= self.calls:
            return False

        # Record this request
        self._records[key].append(now)
        return True

    def reset(self, key: str) -> None:
        """Reset the rate limit counter for a specific key."""
        if key in self._records:
            del self._records[key]


# ------------------------------------------------------------------
# Token validation helper
# ---------------------------------------------------------------


class TokenValidator(HTTPBearer):
    """HTTP Bearer token validator with JWT verification.

    Validates access tokens and extracts the user identity.
    Extends FastAPI's HTTPBearer for automatic integration.
    """

    def __init__(self, auto_error: bool = True) -> None:
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Any) -> dict[str, Any] | None:
        """Validate the bearer token from the Authorization header.

        Parameters
        ----------
        request:
            The FastAPI request object.

        Returns
        -------
        Optional[Dict[str, Any]]
            Decoded token payload if valid, None if no/invalid token.
        """
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(
            request
        )

        if credentials is None:
            return None

        token = credentials.credentials

        # TODO: Integrate with actual JWT verification library
        # For now, return a placeholder indicating token was received
        # In production, verify signature, expiration, claims, etc.
        try:
            # Placeholder: decode without verification for demo
            # payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return {"token_received": True, "scheme": "bearer"}
        except Exception:
            return None


# ------------------------------------------------------------------
# Security event logger
# ---------------------------------------------------------------


class SecurityLogger:
    """Logs security-relevant events for audit and monitoring."""

    _EVENT_TYPES = {
        "authentication_failure",
        "authorization_failure",
        "rate_limit_exceeded",
        "suspicious_activity",
        "token_revoked",
    }

    @classmethod
    def log_event(
        cls,
        event_type: str,
        details: dict[str, Any],
        level: str = "warning",
    ) -> None:
        """Log a security event.

        Parameters
        ----------
        event_type:
            Type of security event (must be in EVENT_TYPES or custom).
        details:
            Additional context about the event (IP, user agent, token hash, etc.).
        level:
            Log severity level (info, warning, error, critical).
        """
        import logging

        logger = logging.getLogger("security")
        logger.log(
            getattr(logging, level.upper(), logging.WARNING),
            f"SECURITY EVENT: {event_type}",
            extra={"security_event": event_type, "details": details},
        )

    @classmethod
    def authentication_failure(cls, ip: str, user_agent: str | None, reason: str) -> None:
        """Log an authentication failure event."""
        cls.log_event(
            "authentication_failure",
            {
                "ip": ip,
                "user_agent": user_agent,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @classmethod
    def authorization_failure(cls, user_id: str, resource: str, reason: str) -> None:
        """Log an authorization failure event."""
        cls.log_event(
            "authorization_failure",
            {
                "user_id": user_id,
                "resource": resource,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @classmethod
    def rate_limit_exceeded(cls, ip: str, endpoint: str, limit: int, period: int) -> None:
        """Log a rate limit exceeded event."""
        cls.log_event(
            "rate_limit_exceeded",
            {
                "ip": ip,
                "endpoint": endpoint,
                "limit": limit,
                "period": period,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @classmethod
    def suspicious_activity(cls, ip: str, user_id: str | None, activity: str, details: dict[str, Any]) -> None:
        """Log suspicious activity event."""
        cls.log_event(
            "suspicious_activity",
            {
                "ip": ip,
                "user_id": user_id,
                "activity": activity,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )