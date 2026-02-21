from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    redis: str


class ReadinessResponse(BaseModel):
    ready: bool


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> dict[str, Any]:
    try:
        await request.app.state.redis.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    return {"status": "ok", "redis": redis_status}


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(request: Request) -> dict[str, bool]:
    try:
        await request.app.state.redis.ping()
        return {"ready": True}
    except Exception:
        return {"ready": False}
