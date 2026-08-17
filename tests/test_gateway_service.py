import asyncio

import pytest

from app.services.gateway import (
    DEFAULT_MODEL,
    REQUESTS_PER_MINUTE,
    WINDOW_SECONDS,
    GatewayService,
    InvalidApiKeyError,
    RateLimitExceededError,
)
from app.services.infrastructure import UpstreamResponse


class InfrastructureStub:
    def __init__(self, user_id="user-1", count: int = 1, ttl: int = 60):
        self.user_id = user_id
        self.count = count
        self.ttl = ttl
        self.window_seconds = None

    async def get_user_id_by_api_key(self, _: str):
        return self.user_id

    async def increment_request_count(self, _: str, window_seconds: int):
        self.window_seconds = window_seconds
        return self.count, self.ttl

    async def request_chat_completion(self, payload: dict):
        self.payload = payload
        return UpstreamResponse(200, b"{}", "application/json")


def test_rate_limit_is_five_requests_per_minute():
    assert REQUESTS_PER_MINUTE == 5
    assert WINDOW_SECONDS == 60


def test_allows_fifth_request_and_uses_free_model_by_default():
    infrastructure = InfrastructureStub(count=5)
    service = GatewayService(infrastructure)
    assert asyncio.run(service.authorize("key")) == "user-1"
    response = asyncio.run(service.create_chat_completion({"messages": []}))
    assert response.status_code == 200
    assert infrastructure.window_seconds == WINDOW_SECONDS
    assert infrastructure.payload["model"] == DEFAULT_MODEL


def test_rejects_sixth_request_and_returns_ttl():
    with pytest.raises(RateLimitExceededError) as error:
        asyncio.run(
            GatewayService(InfrastructureStub(count=6, ttl=42)).authorize("key")
        )
    assert error.value.retry_after == 42


def test_rejects_unknown_api_key():
    with pytest.raises(InvalidApiKeyError):
        asyncio.run(
            GatewayService(InfrastructureStub(user_id=None)).authorize("key")
        )
