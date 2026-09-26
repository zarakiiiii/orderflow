import time

from fastapi import HTTPException, Request, status

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
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )