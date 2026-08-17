"""FastAPI-зависимости для доступа к сервисам и авторизации запроса."""

from fastapi import HTTPException, Request

from app.services.gateway import (
    GatewayService,
    InvalidApiKeyError,
    RateLimitExceededError,
)


def get_gateway_service(request: Request) -> GatewayService:
    return request.app.state.gateway_service


def get_bearer_token(request: Request) -> str:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Authorization: Bearer <API key> is required")
    return token


async def require_current_user(request: Request) -> str:
    """Проверяет API-ключ и лимит до обработки endpoint-а."""
    try:
        return await get_gateway_service(request).authorize(get_bearer_token(request))
    except InvalidApiKeyError as error:
        raise HTTPException(401, "Invalid API key") from error
    except RateLimitExceededError as error:
        raise HTTPException(
            429,
            "Rate limit exceeded. Try again later.",
            headers={"Retry-After": str(error.retry_after)},
        ) from error
