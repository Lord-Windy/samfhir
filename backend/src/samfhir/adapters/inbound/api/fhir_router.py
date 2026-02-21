from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from samfhir.domain.ports.cache_port import CachePort

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])


class CacheStatsResponse(BaseModel):
    hits: int
    misses: int


def get_cache_port(request: Request) -> CachePort:
    return request.app.state.cache_port


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    cache: CachePort = Depends(get_cache_port),
) -> dict[str, Any]:
    stats = await cache.stats()
    return {"hits": stats.get("hits", 0), "misses": stats.get("misses", 0)}


@router.delete("")
async def flush_cache(cache: CachePort = Depends(get_cache_port)) -> dict[str, str]:
    await cache.flush()
    return {"status": "flushed"}
