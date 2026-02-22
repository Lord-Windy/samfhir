import asyncio

import pytest
import redis.asyncio as aioredis

from samfhir.adapters.outbound.redis_cache import RedisCache


@pytest.fixture
async def redis_cache():
    """RedisCache on db 1 (isolated from dev). Skips if Redis unavailable."""
    client = aioredis.from_url("redis://localhost:6379/1", decode_responses=True)
    try:
        await client.ping()
    except Exception:
        pytest.skip("Redis not available")
    cache = RedisCache(client)
    await cache.flush()
    yield cache
    await cache.flush()
    await client.aclose()


async def test_set_get_roundtrip(redis_cache: RedisCache):
    await redis_cache.set("key1", "value1")
    assert await redis_cache.get("key1") == "value1"


async def test_ttl_expiry(redis_cache: RedisCache):
    await redis_cache.set("key2", "value2", ttl=1)
    assert await redis_cache.get("key2") == "value2"

    await asyncio.sleep(1.1)
    assert await redis_cache.get("key2") is None


async def test_delete_removes_key(redis_cache: RedisCache):
    await redis_cache.set("key3", "value3")
    assert await redis_cache.get("key3") == "value3"

    await redis_cache.delete("key3")
    assert await redis_cache.get("key3") is None


async def test_stats_track_hits_and_misses(redis_cache: RedisCache):
    await redis_cache.set("key4", "value4")
    await redis_cache.get("key4")  # hit
    await redis_cache.get("nonexistent")  # miss

    stats = await redis_cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
