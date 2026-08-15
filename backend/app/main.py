"""Application entrypoint."""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config.settings import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.monitoring import (
    setup_otel,
    correlation_id_middleware,
    metrics_middleware,
    create_health_router,
    get_structured_logger,
    HealthCheckResult,
    GracefulDegradationMiddleware,
)

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
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        env=settings.environment,
        otel_endpoint=settings.opentelemetry_endpoint,
    )

    yield

    # Log application stop
    logger.info("application_stopping")

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

# Correlation ID middleware (adds X-Correlation-ID to requests/responses)
app.add_middleware(correlation_id_middleware)

# Metrics middleware (counters, histograms, error counts)
app.add_middleware(metrics_middleware(tracer, meter))

# Graceful degradation middleware (circuit breakers for external services)
app.add_middleware(GracefulDegradationMiddleware)

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


checker_funcs: Dict[str, Callable[[], HealthCheckResult]] = {
    "database": db_health_check,
    "cache": redis_health_check,
}

health_router = create_health_router(checker_funcs)
app.include_router(health_router)

# ------------------------------------------------------------------
# API router
# ------------------------------------------------------------------

app.include_router(api_router)

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
    overall = "healthy" if all_ok else "unhealthy"
    return JSONResponse({"status": overall, "checks": results})


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