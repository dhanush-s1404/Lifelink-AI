"""Monitoring for LifeLink AI backend.

Provides:
- Structured JSON logging with correlation IDs
- Prometheus-style metrics (counts, histograms, counters)
- OpenTelemetry tracing setup (optional, via env vars)
- Health check endpoints (/health, /ready, /live)
- Request timing and error tracking
"""

from __future__ import annotations

import json
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# ------------------------------------------------------------------
# JSON logger using standard library (no structlog dependency)
# ------------------------------------------------------------------


class JSONFormatter(logging.Formatter):
    """Formatter that outputs log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        record_dict: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
        }
        for key in record.__dict__:
            if key not in (
                "name",
                "msg",
                "args",
                "levelno",
                "levelname",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "stack_trace",
                "lineno",
                "func",
                "operator",
            ):
                record_dict[key] = record.__dict__[key]
        return json.dumps(record_dict, default=str)


# Global logger setup
setup_logger = logging.getLogger("lifelink")
setup_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
setup_logger.addHandler(handler)


class StructuredLogger:
    """Proxy that supports structlog-style ``logger.info("event", key=value)``.

    Keyword arguments are forwarded as structured ``extra`` fields so the
    JSON formatter can serialize them. Values that look sensitive are
    redacted by the formatter callers (see ``app.core.logging``).
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _emit(self, level: str, msg: str, exc_info=None, **kwargs) -> None:
        getattr(self._logger, level)(msg, extra=dict(kwargs) if kwargs else None, exc_info=exc_info)

    def debug(self, msg: str, **kwargs) -> None:
        self._emit("debug", msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        self._emit("info", msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        self._emit("warning", msg, **kwargs)

    def warn(self, msg: str, **kwargs) -> None:
        self._emit("warning", msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self._emit("error", msg, **kwargs)

    def exception(self, msg: str, **kwargs) -> None:
        self._emit("error", msg, exc_info=True, **kwargs)


logger = StructuredLogger(setup_logger)


def configure_logging(level: str = "INFO") -> None:
    """Configure the structured logger level (safe to call more than once)."""
    setup_logger.setLevel(getattr(logging, level.upper(), logging.INFO))


# ------------------------------------------------------------------
# OpenTelemetry setup (lazy imports - opentelemetry optional)
# ------------------------------------------------------------------


def setup_otel(
    service_name: str = "lifelink-backend",
    endpoint: Optional[str] = None,
    enable_metrics: bool = True,
) -> tuple:
    """Initialize OpenTelemetry tracer and meter.

    Returns (tracer, meter, trace_provider) tuple.
    All opentelemetry imports are done lazily inside the function.
    Returns (None, None, None) when OpenTelemetry is not installed, so the
    application can still boot in development.
    """
    try:
        # Lazy imports - opentelemetry is optional
        from opentelemetry import trace
        from opentelemetry.metrics import get_meter_provider
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource as SDKResourceV2
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return None, None, None

    resource = SDKResourceV2.create(
        {SERVICE_NAME: service_name, "host.name": "unknown", "os": "unknown"}
    )

    trace_provider = TracerProvider(resource=resource)

    if endpoint:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter

        jaeger_exporter = JaegerExporter(endpoint=endpoint)
        trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    trace.set_tracer_provider(trace_provider)
    tracer = trace.get_tracer(service_name)

    meter = None
    if enable_metrics:
        from opentelemetry.exporter.prometheus import PrometheusMetricReader
        from opentelemetry import metrics as otel_metrics

        meter = get_meter_provider().get_meter(service_name)
        prom_reader = PrometheusMetricReader()
        meter_provider = otel_metrics.get_meter_provider()
        meter_provider.add_metric_reader(prom_reader)

    return tracer, meter, trace_provider


# ------------------------------------------------------------------
# Correlation ID middleware
# ------------------------------------------------------------------


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Adds and echoes a correlation ID on every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id

        logger.info(
            "request",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            query_string=str(request.url.query),
            client_host=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent", "unknown"),
        )

        return response


# ------------------------------------------------------------------
# Metrics middleware for FastAPI
# ------------------------------------------------------------------


def metrics_middleware(tracer=None, meter=None) -> Callable:
    """FastAPI middleware that instruments metrics and tracing."""

    if meter is None:
        from opentelemetry import metrics as otel_metrics
        meter = otel_metrics.get_meter("lifelink-backend")

    REQUEST_COUNT = meter.create_counter(
        "lifelink_requests_total",
        description="Total number of HTTP requests",
        unit="1",
    ) if meter else None
    REQUEST_DURATION = meter.create_histogram(
        "lifelink_request_duration_seconds",
        description="HTTP request duration in seconds",
        unit="s",
    ) if meter else None
    ERROR_COUNT = meter.create_counter(
        "lifelink_errors_total",
        description="Total number of HTTP errors",
        unit="1",
    ) if meter else None

    # OpenTelemetry tracer (lazy)
    from opentelemetry import trace as _trace

    def middleware(get_response: Callable) -> Callable:
        async def inner(request: Request, **kwargs) -> Response:
            start_time = time.time()
            duration = 0.0
            error_occurred = False

            if tracer:
                with _trace.start_as_current_span(
                    f"HTTP {request.method} {request.url.path}"
                ) as span:
                    span.set_attribute("http.method", request.method)
                    span.set_attribute("http.url", request.url.path)
                    span.set_attribute("http.client_ip", request.client.host if request.client else "unknown")

                    try:
                        response = await get_response(request)
                        span.set_status()
                        if ERROR_COUNT:
                            ERROR_COUNT.add(1)  # will be overridden below
                        return response
                    except Exception as e:
                        error_occurred = True
                        span.record_exception(e)
                        span.set_status()
                        if ERROR_COUNT:
                            ERROR_COUNT.add(1)
                        raise
            else:
                try:
                    response = await get_response(request)
                except Exception:
                    error_occurred = True
                    if ERROR_COUNT:
                        ERROR_COUNT.add(1)
                    raise

            duration = time.time() - start_time
            if REQUEST_COUNT:
                REQUEST_COUNT.add(1)
            if REQUEST_DURATION:
                REQUEST_DURATION.record(duration)

            return response if not error_occurred else None  # type: ignore

        return inner

    return middleware


# ------------------------------------------------------------------
# Health check result and router
# ------------------------------------------------------------------


class HealthCheckResult:
    """Result of a health check."""

    def __init__(
        self,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        self.status = status
        self.details = details or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


def create_health_router(
    checker_funcs: Dict[str, Callable[[], HealthCheckResult]],
) -> APIRouter:
    """Create a FastAPI router with health check endpoints."""

    from fastapi import APIRouter

    router = APIRouter(prefix="/health", tags=["monitoring"])

    @router.get("", include_in_schema=False)
    async def health_check() -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        all_ok = True
        for name, checker in checker_funcs.items():
            result = checker()
            results[name] = result.to_dict()
            if result.status != "healthy":
                all_ok = False
        overall = "healthy" if all_ok else "unhealthy"
        return {"status": overall, "checks": results}

    @router.get("/ready", include_in_schema=False)
    async def readiness_check() -> Dict[str, Any]:
        return await health_check()

    @router.get("/live", include_in_schema=False)
    async def liveness_check() -> Dict[str, Any]:
        return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}

    return router


# ------------------------------------------------------------------
# Convenience helper
# ------------------------------------------------------------------


def get_structured_logger() -> StructuredLogger:
    """Get the application-structured logger."""
    return logger