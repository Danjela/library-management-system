import threading
from library.logging import request_id as request_id_context_var
from library.logging import user_id as user_id_context_var

_local = threading.local()


def set_request_context(**kwargs):
    for key, value in kwargs.items():
        setattr(_local, key, value)
    
    # Also set ContextVars for structured logging (works with async)
    request_id_context_var.set(kwargs.get("request_id"))
    user_id_context_var.set(kwargs.get("user_id"))


def get_request_context():
    return {
        "request_id": getattr(_local, "request_id", None),
        "user_id": getattr(_local, "user_id", None),
        "username": getattr(_local, "username", None),
        "roles": getattr(_local, "roles", None),
    }


def clear_request_context():
    _local.__dict__.clear()
    # Reset ContextVars
    request_id_context_var.set(None)
    user_id_context_var.set(None)

