"""Точка входа: ``uvicorn app.main:app --reload``."""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from redis.asyncio import Redis

from app.routes import router
from app.settings import Settings
from app.services.gateway import GatewayService
from app.services.infrastructure import ExternalServices


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.get()
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY must be configured")

    redis = Redis.from_url(
        settings.redis_url, decode_responses=True
    )
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(settings.http_timeout_seconds))
    infrastructure = ExternalServices(
        redis,
        http_client,
        settings.openrouter_api_key,
        settings.openrouter_url,
    )
    app.state.gateway_service = GatewayService(infrastructure)
    yield
    await http_client.aclose()
    await redis.aclose()


app = FastAPI(title="AI API Gateway", lifespan=lifespan)
app.include_router(router)
