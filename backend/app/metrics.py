import logging
import os
import time

from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, start_http_server

logger = logging.getLogger("rag")

# Defined once per process: Prometheus metrics cannot be registered twice.
REQUESTS = Counter("http_requests_total", "HTTP requests handled", ["method", "path", "status"])
LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

# Probes would drown out the real traffic in the metrics.
UNTRACKED_PATHS = {"/health"}


def record(method: str, path: str, status: int, elapsed: float) -> None:
    REQUESTS.labels(method, path, str(status)).inc()
    LATENCY.labels(method, path).observe(elapsed)
    logger.info("%s %s -> %d in %.0f ms", method, path, status, elapsed * 1000)


def instrument(app: FastAPI) -> None:
    """Count requests, record their latency and log them, including ones that crash."""

    @app.middleware("http")
    async def track(request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            path = route.path if route is not None else "unmatched"
            if path not in UNTRACKED_PATHS:
                record(request.method, path, status, time.perf_counter() - start)


def start_metrics_server() -> None:
    """Serve /metrics on its own port, which only the internal network can reach.

    Keeping it off the API port means no proxy path (for example /api/api/metrics)
    can expose it through Nginx.
    """
    port = os.getenv("METRICS_PORT")
    if port:
        start_http_server(int(port))
        logger.info("metrics served on port %s", port)
