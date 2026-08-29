import json
import os
from typing import Any, Optional
import redis.asyncio as aioredis
import socketio

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_socket_manager() -> Optional[socketio.AsyncRedisManager]:
    """
    Initialize and return the Socket.IO AsyncRedisManager for multi-instance scaling.
    Falls back gracefully to None (in-memory manager) if Redis is not configured or fails.
    """
    try:
        if REDIS_URL:
            manager = socketio.AsyncRedisManager(REDIS_URL)
            print(f"📡 [Redis] Socket.IO Redis Manager initialized with {REDIS_URL}")
            return manager
    except Exception as exc:
        print(f"⚠️ [Redis] Socket.IO Redis Manager fallback to memory: {exc}")
    return None


class RedisCacheService:
    """Async Redis caching service with connection pooling, JSON serialization, and TTL support."""

    def __init__(self, url: str = REDIS_URL):
        self.redis_url = url
        self.client: Optional[aioredis.Redis] = None

    async def init(self) -> None:
        """Initialize connection to Redis instance."""
        try:
            self.client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.client.ping()
            print(f"✅ [Redis] Cache connected to {self.redis_url}")
        except Exception as exc:
            print(f"⚠️ [Redis] Cache disabled or offline: {exc}")
            self.client = None

    async def get(self, key: str) -> Optional[str]:
        """Get cached string value by key."""
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception:
            return None

    async def get_json(self, key: str) -> Optional[Any]:
        """Get and parse cached JSON object by key."""
        val = await self.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except Exception:
            return None

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> bool:
        """Set cached string value with TTL in seconds."""
        if not self.client:
            return False
        try:
            await self.client.set(key, value, ex=ttl_seconds)
            return True
        except Exception:
            return False

    async def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Serialize and set cached JSON object with TTL in seconds."""
        try:
            serialized = json.dumps(value, default=str)
            return await self.set(key, serialized, ttl_seconds)
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete a cached key from Redis."""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception:
            return False

    async def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching a wildcard pattern (e.g. 'home:*')."""
        if not self.client:
            return False
        try:
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close connection to Redis."""
        if self.client:
            await self.client.close()


redis_cache = RedisCacheService()
