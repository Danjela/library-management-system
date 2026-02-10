import json
import time
import logging

from django.utils.deprecation import MiddlewareMixin

from config.logging.context import get_request_context

logger = logging.getLogger("request")


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.monotonic()

    def process_response(self, request, response):
        duration_ms = round(
            (time.monotonic() - request._start_time) * 1000,
            2
        )

        context = get_request_context()

        log_data = {
            "service": "library-api",
            "event": "http_request",
            "method": request.method,
            "path": request.get_full_path(),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "ip": self._get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT"),
            **context,
        }

        logger.info(json.dumps(log_data))
        return response

    def process_exception(self, request, exception):
        context = get_request_context()

        logger.exception(json.dumps({
            "service": "library-api",
            "event": "http_exception",
            "path": request.path,
            "error": str(exception),
            **context,
        }))

    def _get_client_ip(self, request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")
