"""Бизнес-правила API Gateway."""

from app.services.infrastructure import ExternalServices, UpstreamResponse


# Лимит одного пользователя: не более пяти запросов за одну минуту.
REQUESTS_PER_MINUTE = 5
WINDOW_SECONDS = 60
DEFAULT_MODEL = "openrouter/free"


class InvalidApiKeyError(Exception):
    pass


class RateLimitExceededError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


class GatewayService:
    def __init__(self, infrastructure: ExternalServices):
        self._infrastructure = infrastructure

    async def check_health(self) -> None:
        await self._infrastructure.check_redis()

    async def authorize(self, api_key: str) -> str:
        user_id = await self._infrastructure.get_user_id_by_api_key(api_key)
        if not user_id:
            raise InvalidApiKeyError

        count, ttl = await self._infrastructure.increment_request_count(
            user_id, WINDOW_SECONDS
        )
        if count > REQUESTS_PER_MINUTE:
            raise RateLimitExceededError(max(ttl, 1))
        return user_id

    async def create_chat_completion(self, payload: dict) -> UpstreamResponse:
        payload.setdefault("model", DEFAULT_MODEL)
        return await self._infrastructure.request_chat_completion(payload)
