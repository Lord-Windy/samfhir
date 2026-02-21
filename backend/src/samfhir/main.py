from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from samfhir.config import Settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield
    finally:
        await app.state.redis.aclose()


def create_app() -> FastAPI:
    settings = Settings()
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.state.settings = settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health")
    async def health():
        try:
            await application.state.redis.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "disconnected"
        return {"status": "ok", "redis": redis_status}

    @application.get("/health/ready")
    async def readiness():
        try:
            await application.state.redis.ping()
            return {"ready": True}
        except Exception:
            return {"ready": False}

    return application


app = create_app()
