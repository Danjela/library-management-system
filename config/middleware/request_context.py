import uuid
from django.utils.deprecation import MiddlewareMixin

from config.logging.context import (
    set_request_context,
    clear_request_context,
)


class RequestContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request_id = str(uuid.uuid4())
        user = getattr(request, "user", None)

        context = {"request_id": request_id}

        if user and user.is_authenticated:
            context.update({
                "user_id": user.id,
                "username": user.username,
                "roles": list(
                    user.groups.values_list("name", flat=True)
                ),
            })

        set_request_context(**context)
        request.request_id = request_id

    def process_response(self, request, response):
        clear_request_context()
        return response

    def process_exception(self, request, exception):
        clear_request_context()
