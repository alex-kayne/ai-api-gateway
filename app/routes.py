from json import JSONDecodeError

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.dependencies import get_gateway_service, require_current_user
from app.services.gateway import GatewayService


router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    await request.app.state.gateway_service.check_health()
    return {"status": "ok"}


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    _: str = Depends(require_current_user),
    gateway_service: GatewayService = Depends(get_gateway_service),
) -> Response:
    try:
        payload = await request.json()
    except JSONDecodeError as error:
        raise HTTPException(422, "Request body must contain valid JSON") from error
    if not isinstance(payload, dict):
        raise HTTPException(422, "Request body must be a JSON object")
    try:
        upstream = await gateway_service.create_chat_completion(payload)
    except httpx.HTTPError as error:
        # Ошибка сетевого обращения к OpenRouter не должна становиться 500 для клиента.
        raise HTTPException(502, "OpenRouter is unavailable") from error

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.content_type,
    )
