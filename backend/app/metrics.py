import logging
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

logger = logging.getLogger("rag")

# Defined once per process: Prometheus metrics cannot be registered twice.
REQUESTS = Counter("http_requests_total", "HTTP requests handled", ["method", "path", "status"])
LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

# Probes and scrapes would drown out the real traffic in the metrics.
UNTRACKED_PATHS = {"/metrics", "/health"}


def instrument(app: FastAPI) -> None:
    """Count requests, record their latency, log them, and expose GET /metrics."""

    @app.middleware("http")
    async def record(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path = route.path if route is not None else "unmatched"
        if path not in UNTRACKED_PATHS:
            elapsed = time.perf_counter() - start
            REQUESTS.labels(request.method, path, str(response.status_code)).inc()
            LATENCY.labels(request.method, path).observe(elapsed)
            logger.info(
                "%s %s -> %d in %.0f ms",
                request.method,
                path,
                response.status_code,
                elapsed * 1000,
            )
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
