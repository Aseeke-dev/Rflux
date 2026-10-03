import json
from typing import Optional, Any

from pydantic import BaseModel
import redis.asyncio as redis


class CacheService:
    DEFAULT_TTL = 3600  # Cache TTL set to 1 hour (3600 seconds)

    @staticmethod
    def _to_jsonable(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            return {key: CacheService._to_jsonable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [CacheService._to_jsonable(item) for item in value]
        if isinstance(value, tuple):
            return [CacheService._to_jsonable(item) for item in value]
        if isinstance(value, set):
            return [CacheService._to_jsonable(item) for item in value]
        return value

    @staticmethod
    async def get_cache(redis_client: redis.Redis, key: str) -> Optional[Any]:
        """Fetch cached data by key and parse from JSON."""
        cached_data = await redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None

    @staticmethod
    async def set_cache(
        redis_client: redis.Redis, key: str, value: Any, ttl: int = DEFAULT_TTL
    ) -> None:
        """Store data as JSON with a Time-To-Live (TTL)."""
        json_safe_value = CacheService._to_jsonable(value)
        await redis_client.set(key, json.dumps(json_safe_value), ex=ttl)

    @staticmethod
    async def invalidate_user_cache(redis_client: redis.Redis, user_id: int) -> None:
        """Invalidate personalized recommendations when a user submits a new rating."""
        cache_key = f"rec:for_you:{user_id}"
        await redis_client.delete(cache_key)