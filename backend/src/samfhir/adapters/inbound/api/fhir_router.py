from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from samfhir.dependencies import get_cache
from samfhir.domain.ports.cache_port import CachePort

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])


class CacheStatsResponse(BaseModel):
    hits: int
    misses: int


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    cache: CachePort = Depends(get_cache),
) -> dict[str, Any]:
    stats = await cache.stats()
    return {"hits": stats.get("hits", 0), "misses": stats.get("misses", 0)}


@router.delete("")
async def flush_cache(cache: CachePort = Depends(get_cache)) -> dict[str, str]:
    await cache.flush()
    return {"status": "flushed"}
