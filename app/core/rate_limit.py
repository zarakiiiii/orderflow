import time

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.redis import redis_client


RATE_LIMIT = 100
WINDOW_SECONDS = 60


def check_rate_limit(request: Request):
    client_ip = request.client.host

    current_window = int(time.time()) // WINDOW_SECONDS

    key = f"rate_limit:{client_ip}:{current_window}"

    request_count = redis_client.incr(key)

    if request_count == 1:
        redis_client.expire(key, WINDOW_SECONDS)

    if request_count > RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
            },
        )

    return None