import threading

_local = threading.local()


def set_request_context(**kwargs):
    for key, value in kwargs.items():
        setattr(_local, key, value)


def get_request_context():
    return {
        "request_id": getattr(_local, "request_id", None),
        "user_id": getattr(_local, "user_id", None),
        "username": getattr(_local, "username", None),
        "roles": getattr(_local, "roles", None),
    }


def clear_request_context():
    _local.__dict__.clear()
