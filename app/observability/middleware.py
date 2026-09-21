import logging
from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.context import (
    generate_request_id,
    reset_request_id,
    set_request_id,
)
from app.observability.logging import (
    get_logger,
    log_event,
)
from app.observability.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
)


logger = get_logger("aegis.http")


def get_metric_path(request: Request) -> str:
    """
    Return a bounded route template for Prometheus labels.

    Dynamic request paths such as:

        /incidents/abc-123

    become:

        /incidents/{thread_id}

    This prevents high-cardinality metric labels while
    structured logs can still retain the concrete request path.
    """

    route = request.scope.get("route")

    route_path = getattr(
        route,
        "path",
        None,
    )

    if route_path:
        return str(route_path)

    return "unmatched"


class ObservabilityMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        request_id = (
            request.headers.get("X-Request-ID")
            or generate_request_id()
        )

        context_token = set_request_id(
            request_id
        )

        start_time = perf_counter()

        try:
            log_event(
                logger,
                logging.INFO,
                "http_request_started",
                method=request.method,
                path=request.url.path,
            )

            response = await call_next(
                request
            )

            duration_seconds = (
                perf_counter()
                - start_time
            )

            duration_ms = round(
                duration_seconds * 1000,
                2,
            )

            metric_path = get_metric_path(
                request
            )

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                path=metric_path,
                status_code=str(
                    response.status_code
                ),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                path=metric_path,
            ).observe(
                duration_seconds
            )

            log_event(
                logger,
                logging.INFO,
                "http_request_completed",
                method=request.method,
                path=request.url.path,
                route=metric_path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            response.headers[
                "X-Request-ID"
            ] = request_id

            return response

        except Exception:
            duration_seconds = (
                perf_counter()
                - start_time
            )

            duration_ms = round(
                duration_seconds * 1000,
                2,
            )

            metric_path = get_metric_path(
                request
            )

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                path=metric_path,
                status_code="500",
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                path=metric_path,
            ).observe(
                duration_seconds
            )

            logger.exception(
                "http_request_failed",
                extra={
                    "structured_data": {
                        "event": (
                            "http_request_failed"
                        ),
                        "method": request.method,
                        "path": request.url.path,
                        "route": metric_path,
                        "duration_ms": duration_ms,
                    }
                },
            )

            raise

        finally:
            reset_request_id(
                context_token
            )