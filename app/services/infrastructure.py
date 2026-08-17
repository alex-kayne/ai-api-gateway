"""Адаптеры внешних систем: Redis и OpenRouter."""

from dataclasses import dataclass

import httpx
from redis.asyncio import Redis


_INCREMENT_WITH_TTL = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return {current, redis.call('TTL', KEYS[1])}
"""


@dataclass(frozen=True)
class UpstreamResponse:
    status_code: int
    content: bytes
    content_type: str


class ExternalServices:
    def __init__(
        self,
        redis: Redis,
        http_client: httpx.AsyncClient,
        openrouter_api_key: str,
        openrouter_url: str,
    ):
        self._redis = redis
        self._http_client = http_client
        self._openrouter_api_key = openrouter_api_key
        self._openrouter_url = openrouter_url

    async def get_user_id_by_api_key(self, api_key: str) -> str | None:
        return await self._redis.get(f"api_key:{api_key}")

    async def increment_request_count(self, user_id: str, window_seconds: int) -> tuple[int, int]:
        count, ttl = await self._redis.eval(
            _INCREMENT_WITH_TTL, 1, f"rate_limit:{user_id}", window_seconds
        )
        return int(count), int(ttl)

    async def check_redis(self) -> None:
        await self._redis.ping()

    async def request_chat_completion(self, payload: dict) -> UpstreamResponse:
        response = await self._http_client.post(
            self._openrouter_url,
            json=payload,
            headers={"Authorization": f"Bearer {self._openrouter_api_key}"},
        )
        return UpstreamResponse(
            status_code=response.status_code,
            content=response.content,
            content_type=response.headers.get("content-type", "application/json"),
        )
