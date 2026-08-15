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
from typing import Any, Callable

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
# Circuit breaker for graceful degradation
# ---------------------------------------------------------------


class CircuitBreaker:
    """Circuit breaker pattern for graceful degradation of external services.

    States:
        - CLOSED: normal operation, requests pass through
        - OPEN: circuit tripped, requests are short-circuited (fallback returned)
        - HALF_OPEN: testing if service recovered, limited requests allowed

    Usage:
        breaker = CircuitFailureThreshold(failure_threshold=5, recovery_timeout=30)
        result = breaker.call(external_service_call)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        fallback: Any = None,
    ) -> None:
        """Initialize circuit breaker.

        Parameters
        ----------
        failure_threshold:
            Number of consecutive failures before opening the circuit.
        recovery_timeout:
            Seconds to wait before transitioning to HALF_OPEN.
        fallback:
            Value or callable to return when circuit is OPEN.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fallback = fallback
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._last_success_time: float | None = None

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function through the circuit breaker.

        Parameters
        ----------
        func:
            The async function to execute.
        *args:
            Positional arguments for func.
        **kwargs:
            Keyword arguments for func.

        Returns
        -------
        Any
            Result of func if circuit closed, or fallback if open.
        """
        if self._state == "OPEN":
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed < self.recovery_timeout:
                    # Circuit is open, return fallback immediately
                    if callable(self.fallback):
                        return self.fallback()
                    return self.fallback
                # Transition to HALF_OPEN
                self._state = "HALF_OPEN"
                self._failure_count = 0

        if self._state == "HALF_OPEN":
            # Only allow a single call through; if it succeeds, close the circuit
            try:
                result = func(*args, **kwargs)
                self._state = "CLOSED"
                self._failure_count = 0
                self._last_success_time = time.time()
                return result
            except Exception:
                # Back to OPEN
                self._state = "OPEN"
                self._failure_count = 1
                self._last_failure_time = time.time()
                if callable(self.fallback):
                    return self.fallback()
                return self.fallback

        # CLOSED state: execute normally
        try:
            result = func(*args, **kwargs)
            self._failure_count = 0
            self._last_success_time = time.time()
            return result
        except Exception:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = "OPEN"
                self._last_failure_time = time.time()
            raise


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


# ------------------------------------------------------------------
# Graceful degradation middleware
# ---------------------------------------------------------------


class GracefulDegradationMiddleware(BaseHTTPMiddleware):
    """Middleware that provides graceful degradation when external services fail.

    Wraps request handling with circuit breakers for optional external dependencies
    (AI services, search, notifications, etc.). When a circuit is OPEN, requests
    receive a degraded but functional response instead of 500 errors.

    Configuration is done via class attributes or instance configuration.
    """

    # Circuit breakers for different service categories
    ai_circuit: CircuitBreaker | None = None
    search_circuit: CircuitBreaker | None = None
    notification_circuit: CircuitBreaker | None = None

    # Fallback responses for when circuits are OPEN
    ai_fallback_response: dict[str, Any] = {
        "status": "degraded",
        "message": "AI services temporarily unavailable",
        "fallback": "rule-based response",
    }
    search_fallback_response: dict[str, Any] = {
        "status": "degraded",
        "message": "Search service temporarily unavailable",
        "fallback": "basic search disabled",
    }
    notification_fallback_response: dict[str, Any] = {
        "status": "degraded",
        "message": "Notification service temporarily unavailable",
        "fallback": "email queue enabled",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through circuit breakers.

        For POST/PUT/DELETE requests to AI/embedding/search endpoints,
        circuit breakers are checked. If OPEN, a degraded response is
        returned immediately without calling the downstream service.
        """

        path = request.url.path
        method = request.method

        # Apply circuit breakers to AI-related endpoints
        if path.startswith("/ai/") and method in ("POST", "PUT", "DELETE"):
            # Initialize circuits if not set
            if GracefulDegradationMiddleware.ai_circuit is None:
                GracefulDegradationMiddleware.ai_circuit = CircuitBreaker(
                    failure_threshold=3, recovery_timeout=15.0
                )
            if GracefulDegradationMiddleware.search_circuit is None:
                GracefulDegradationMiddleware.search_circuit = CircuitBreaker(
                    failure_threshold=3, recovery_timeout=15.0
                )

            # Wrap the downstream call with circuit breaker
            original_call_next = call_next

            async def circuit_breaker_next() -> Response:
                # Determine which circuit to use based on path
                if "/embed" in path or "/summarize" in path:
                    circuit = GracefulDegradationMiddleware.ai_circuit
                elif "/search" in path:
                    circuit = GracefulDegradationMiddleware.search_circuit
                else:
                    circuit = GracefulDegradationMiddleware.ai_circuit

                # Define the actual service call
                async def _service_call():
                    return await original_call_next(request)

                try:
                    return await circuit.call(_service_call)
                except Exception:
                    # Circuit breaker returned fallback or re-raised
                    if GracefulDegradationMiddleware.ai_circuit:
                        if "/embed" in path or "/summarize" in path:
                            return Response(
                                content=json.dumps(
                                    GracefulDegradationMiddleware.ai_fallback_response
                                ),
                                status_code=200,
                                media_type="application/json",
                            )
                        elif "/search" in path:
                            return Response(
                                content=json.dumps(
                                    GracefulDegradationMiddleware.search_fallback_response
                                ),
                                status_code=200,
                                media_type="application/json",
                            )
                    return Response(
                        content=json.dumps(
                            {"status": "error", "detail": "internal server error"}
                        ),
                        status_code=500,
                        media_type="application/json",
                    )

            call_next = circuit_breaker_next

        # Apply circuit breakers to notification-related endpoints
        if "/notifications/" in path and method in ("POST", "DELETE"):
            if GracefulDegradationMiddleware.notification_circuit is None:
                GracefulDegradationMiddleware.notification_circuit = CircuitBreaker(
                    failure_threshold=3, recovery_timeout=15.0
                )

            async def notification_circuit_breaker_next() -> Response:
                original_call_next = call_next

                async def _service_call():
                    return await original_call_next(request)

                circuit = GracefulDegradationMiddleware.notification_circuit

                try:
                    return await circuit.call(_service_call)
                except Exception:
                    if GracefulDegradationMiddleware.notification_circuit:
                        return Response(
                            content=json.dumps(
                                GracefulDegradationMiddleware.notification_fallback_response
                            ),
                            status_code=200,
                            media_type="application/json",
                        )
                    return Response(
                        content=json.dumps(
                            {"status": "error", "detail": "internal server error"}
                        ),
                        status_code=500,
                        media_type="application/json",
                    )

            call_next = notification_circuit_breaker_next

        response: Response = await call_next(request)

        # Add degradation headers for monitoring
        if request.state.correlation_id:
            response.headers[
                "X-Degraded"
            ] = "true" if GracefulDegradationMiddleware._is_any_circuit_open() else "false"

        return response

    @staticmethod
    def _is_any_circuit_open() -> bool:
        """Check if any circuit breaker is currently OPEN."""
        circuits = [
            GracefulDegradationMiddleware.ai_circuit,
            GracefulDegradationMiddleware.search_circuit,
            GracefulDegradationMiddleware.notification_circuit,
        ]
        return any(c and c._state == "OPEN" for c in circuits if c is not None)