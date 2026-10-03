from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.movies import (
    MovieRecomendationResponse,
    MovieResponse,
    TopRatedMovieResponse,
)
from app.schemas.rating import RatingCreate, RatingResponse
from app.schemas.recommendation import ReccommendationListResponse
from app.services.recommendation import RecommendationService
from app.models.rating import Rating
import redis.asyncio as redis
from app.services.cache import CacheService
from app.core.redis import get_redis


router = APIRouter()


def _coerce_movie_recommendation(movie: Any, score: float) -> MovieRecomendationResponse:
    movie_id = getattr(movie, "id", None)
    title = getattr(movie, "title", "")
    genres = getattr(movie, "genres", "")
    overview = getattr(movie, "overview", None)

    return MovieRecomendationResponse(
        id=int(movie_id) if movie_id is not None else 0,
        title=str(title),
        genres=str(genres),
        overview=None if overview is None else str(overview),
        similarity_score=float(score),
    )


def _coerce_top_rated_movie(movie: Any, avg_rating: float, rating_count: int) -> TopRatedMovieResponse:
    movie_id = getattr(movie, "id", None)
    title = getattr(movie, "title", "")
    genres = getattr(movie, "genres", "")
    overview = getattr(movie, "overview", None)

    return TopRatedMovieResponse(
        id=int(movie_id) if movie_id is not None else 0,
        title=str(title),
        genres=str(genres),
        overview=None if overview is None else str(overview),
        average_rating=float(avg_rating),
        rating_count=int(rating_count),
    )

@router.get('/for-you/{user_id}', response_model=ReccommendationListResponse)
async def get_for_you_recommendations(
    user_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    cache_key = f"rec:for_you:{user_id}"

    cached_response = await CacheService.get_cache(redis_client, cache_key)
    if cached_response:
        cached_response["source"] = "cache"
        return cached_response
    
    service = RecommendationService()
    recommendations = await service.get_for_you_recommendations(db=db, user_id=user_id, limit=limit)
    
    if not recommendations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} has no rating history (rating >= 3.5) to generate recommendations.",
        )

    formatted_recs = [_coerce_movie_recommendation(movie, score) for movie, score in recommendations]
    
    response_payload = {
        "user_id": user_id,
        "feature_type": "for_you",
        "recommendations": formatted_recs,
        "source": "database",
    }
    
    await CacheService.set_cache(redis_client, cache_key, response_payload, ttl=3600)

    return ReccommendationListResponse(
        user_id=user_id,
        feature_type="for_you",
        recommendations=formatted_recs,
        source="database",
    )

# 2. Feature 2: Semantic Search
@router.post("/search", response_model=ReccommendationListResponse)
async def semantic_search(
    query: str = Query(..., min_length=3, description="Natural language search query"),
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    recommendations = await RecommendationService.get_similar_movies_by_text(
        db=db, query_text=query, limit=limit
    )

    formatted_recs = [_coerce_movie_recommendation(movie, score) for movie, score in recommendations]

    return ReccommendationListResponse(
        feature_type="semantic_search",
        recommendations=formatted_recs,
        source="database",
    )


# 3. Feature 3: "People Also Like" (Top Rated Movies)
@router.get("/top-rated", response_model=List[TopRatedMovieResponse])
async def get_top_rated_movies(
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    top_movies = await RecommendationService.get_top_rated_movies(
        db=db, limit=limit
    )

    return [
        _coerce_top_rated_movie(movie, avg_rating, rating_count)
        for movie, avg_rating, rating_count in top_movies
    ]


# 4. Feature 4: Genre Filter
@router.get("/genre/{genre_name}", response_model=List[MovieResponse])
async def get_movies_by_genre(
    genre_name: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    movies = await RecommendationService.get_movies_by_genre(
        db=db, genre_name=genre_name, limit=limit
    )
    return movies


# 5. Rating Submission Endpoint
@router.post("/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    rating_in: RatingCreate,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    rating = Rating(
        user_id=rating_in.user_id,
        movie_id=rating_in.movie_id,
        rating=rating_in.rating,
    )
    db.add(rating)
    await db.commit()
    await db.refresh(rating)
    
    await CacheService.invalidate_user_cache(redis_client, rating_in.user_id)
    
    return rating