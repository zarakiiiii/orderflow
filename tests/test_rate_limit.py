
from fastapi import Request

import app.core.rate_limit as rate_limit
from app.core.redis import redis_client


def create_request(ip="127.0.0.1"):
    scope = {
        "type": "http",
        "client": (ip, 12345),
    }

    return Request(scope)


def test_rate_limit_allows_requests(monkeypatch):
    monkeypatch.setattr(
        rate_limit,
        "RATE_LIMIT",
        3,
    )

    monkeypatch.setattr(
        rate_limit.time,
        "time",
        lambda: 1000,
    )

    redis_client.delete("rate_limit:127.0.0.1:16")

    request = create_request()

    assert rate_limit.check_rate_limit(request) is None
    assert rate_limit.check_rate_limit(request) is None
    assert rate_limit.check_rate_limit(request) is None

    redis_client.delete("rate_limit:127.0.0.1:16")


def test_rate_limit_blocks_excess_requests(monkeypatch):
    monkeypatch.setattr(
        rate_limit,
        "RATE_LIMIT",
        3,
    )

    monkeypatch.setattr(
        rate_limit.time,
        "time",
        lambda: 1000,
    )

    redis_client.delete("rate_limit:127.0.0.1:16")

    request = create_request()

    rate_limit.check_rate_limit(request)
    rate_limit.check_rate_limit(request)
    rate_limit.check_rate_limit(request)

    response = rate_limit.check_rate_limit(request)

    assert response is not None
    assert response.status_code == 429

    redis_client.delete("rate_limit:127.0.0.1:16")

