import asyncio

from app.schemas.movies import MovieRecomendationResponse
from app.services.cache import CacheService


class FakeRedis:
    def __init__(self):
        self.store = {}

    async def set(self, key, value, ex=None):
        self.store[key] = value
        return True


def test_cache_service_serializes_pydantic_models():
    redis_client = FakeRedis()
    payload = {
        "user_id": 1,
        "feature_type": "for_you",
        "recommendations": [
            MovieRecomendationResponse(
                id=1,
                title="Inception",
                genres="Sci-Fi",
                overview="Mind-bending thriller",
                similarity_score=0.91,
            )
        ],
        "source": "database",
    }

    asyncio.run(CacheService.set_cache(redis_client, "rec:for_you:1", payload, ttl=3600))

    cached_value = redis_client.store["rec:for_you:1"]
    assert '"similarity_score": 0.91' in cached_value
    assert '"title": "Inception"' in cached_value
