"""Application entrypoint."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config.settings import settings
from app.core.exceptions import register_exception_handlers
from app.monitoring import (
    setup_otel,
    CorrelationIDMiddleware,
    get_structured_logger,
    HealthCheckResult,
    configure_logging,
)
from app.security.middleware import SecurityHeadersMiddleware

# ------------------------------------------------------------------
# OpenTelemetry setup (tracer + meter + Prometheus metrics)
# ------------------------------------------------------------------
tracer, meter, trace_provider = setup_otel(
    service_name=settings.app_name,
    endpoint=settings.opentelemetry_endpoint,
    enable_metrics=settings.enable_metrics,
)

# ------------------------------------------------------------------
# Structured logger
# ------------------------------------------------------------------
log = get_structured_logger()

# ------------------------------------------------------------------
# Lifespan: start up / shut down
# ------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure structured logging
    configure_logging(settings.log_level)

    # Log application start
    log.info(
        "application_starting",
        app_name=settings.app_name,
        env=settings.environment,
        otel_endpoint=settings.opentelemetry_endpoint,
    )

    yield

    # Log application stop
    log.info("application_stopping")

    # Shut down OpenTelemetry
    if trace_provider:
        trace_provider.shutdown()


# ------------------------------------------------------------------
# FastAPI app instance
# ------------------------------------------------------------------


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------

# Correlation ID middleware (adds X-Correlation-ID / X-Request-ID to responses)
app.add_middleware(CorrelationIDMiddleware)

# Security headers (nosniff, frame options, HSTS, CSP)
app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Health check router (using monitoring check functions)
# ------------------------------------------------------------------


def db_health_check() -> HealthCheckResult:
    """Check database connectivity."""
    try:
        # Placeholder: replace with actual DB ping
        return HealthCheckResult(status="healthy", details={"db": "connected"})
    except Exception as e:
        return HealthCheckResult(status="unhealthy", details={"db": str(e)})


def redis_health_check() -> HealthCheckResult:
    """Check Redis connectivity."""
    try:
        # Placeholder: replace with actual Redis ping
        return HealthCheckResult(status="healthy", details={"redis": "connected"})
    except Exception as e:
        return HealthCheckResult(status="unhealthy", details={"redis": str(e)})


app.include_router(api_router)

# NOTE: the standalone /health, /ready, /live endpoints below are the
# canonical health surface; the monitoring health_router is intentionally not
# mounted to avoid shadowing /health.

# ------------------------------------------------------------------
# API router
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# Exception handlers
# ------------------------------------------------------------------

register_exception_handlers(app)


@app.get("/health", tags=["system", "monitoring"])
async def health() -> JSONResponse:
    """Standard health endpoint.

    Returns overall service health status based on registered checkers.
    """
    checker_funcs: Dict[str, Callable[[], HealthCheckResult]] = {
        "database": db_health_check,
        "cache": redis_health_check,
    }
    results: Dict[str, Any] = {}
    all_ok = True
    for name, checker in checker_funcs.items():
        result = checker()
        results[name] = result.to_dict()
        if result.status != "healthy":
            all_ok = False
    overall = "ok" if all_ok else "unhealthy"
    service_name = "LifeLink AI"
    return JSONResponse({"status": overall, "service": service_name, "checks": results})


@app.get("/ready", tags=["system", "monitoring"])
async def ready() -> JSONResponse:
    """Readiness endpoint: service is ready to accept traffic."""
    return JSONResponse({"status": "ready"})


@app.get("/live", tags=["system", "monitoring"])
async def live() -> JSONResponse:
    """Liveness endpoint: process is running."""
    return JSONResponse({"status": "alive"})


# ------------------------------------------------------------------
# Global exception handler for structured error responses
# ------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error(
        "unhandled_exception",
        correlation_id=getattr(request.state, "correlation_id", "unknown"),
        exc_info=exc,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": getattr(request.state, "correlation_id", "unknown"),
        },
    )