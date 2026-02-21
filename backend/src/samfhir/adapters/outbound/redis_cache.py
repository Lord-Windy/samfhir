from typing import Any

import redis.asyncio as redis

from samfhir.domain.ports.cache_port import CachePort


class RedisCache(CachePort):
    HIT_KEY = "cache:stats:hits"
    MISS_KEY = "cache:stats:misses"

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    @classmethod
    def from_url(cls, url: str) -> "RedisCache":
        client = redis.from_url(url, decode_responses=True)
        return cls(client)

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)
        if value is not None:
            await self._client.incr(self.HIT_KEY)
        else:
            await self._client.incr(self.MISS_KEY)
        return value

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        await self._client.setex(key, ttl, value)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def flush(self) -> None:
        await self._client.flushdb()

    async def stats(self) -> dict[str, Any]:
        hits = await self._client.get(self.HIT_KEY)
        misses = await self._client.get(self.MISS_KEY)
        info = await self._client.info("memory")
        return {
            "hits": int(hits or 0),
            "misses": int(misses or 0),
            "used_memory": info.get("used_memory_human", "unknown"),
        }

    async def health_check(self) -> bool:
        try:
            await self._client.ping()
            return True
        except redis.RedisError:
            return False

    async def close(self) -> None:
        await self._client.aclose()
