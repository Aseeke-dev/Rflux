import asyncio
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.movie import Movie
from app.models.rating import Rating

# Load local sentence transformer model for vector generation
model = SentenceTransformer("all-MiniLM-L6-v2")


class RecommendationService:

    @staticmethod
    async def get_similar_movies_by_text(
        db: AsyncSession,
        query_text: str,
        limit: int = 5,
        exclude_user_id: Optional[int] = None,
    ) -> List[Tuple[Movie, float]]:
        """
        Feature 2: Semantic Search
        Generates a 384-d vector from raw text query and executes a pgvector 
        cosine distance query (<=>) in PostgreSQL.
        """
        query_vector = (await asyncio.to_thread(model.encode, query_text)).tolist()
        cosine_distance = Movie.embeddings.cosine_distance(query_vector)

        stmt = (
            select(Movie, cosine_distance.label("distance"))
            .where(Movie.embeddings.is_not(None))
            .order_by(cosine_distance)
            .limit(limit)
        )

        if exclude_user_id is not None:
            stmt = stmt.where(
                ~Movie.id.in_(
                    select(Rating.movie_id).where(Rating.user_id == exclude_user_id)
                )
            )

        result = await db.execute(stmt)
        rows = result.all()

        return [(movie, round(1 - distance, 4)) for movie, distance in rows]

    @staticmethod
    async def get_for_you_recommendations(
        db: AsyncSession, user_id: int, limit: int = 5
    ) -> List[Tuple[Movie, float]]:
        """
        Feature 1: "For You" Personalization
        Aggregates metadata from user's highly rated movies (rating >= 3.5),
        encodes their preference profile into a vector, and queries nearest movies.
        """
        stmt = (
            select(Movie.title, Movie.genres, Movie.overview)
            .join(Rating, Rating.movie_id == Movie.id)
            .where(Rating.user_id == user_id, Rating.rating >= 3.5)
        )
        result = await db.execute(stmt)
        user_ratings = result.all()

        if not user_ratings:
            return []

        # Construct aggregate user preference context
        preference_text = " ".join(
            [f"{title} {genres} {overview or ''}" for title, genres, overview in user_ratings]
        )

        return await RecommendationService.get_similar_movies_by_text(
            db=db,
            query_text=preference_text,
            limit=limit,
            exclude_user_id=user_id,
        )

    @staticmethod
    async def get_top_rated_movies(
        db: AsyncSession, limit: int = 5, min_ratings: int = 1
    ) -> List[Tuple[Movie, float, int]]:
        """
        Feature 3: "People Also Like"
        Calculates top-rated movies across the platform using relational joins.
        """
        stmt = (
            select(
                Movie,
                func.avg(Rating.rating).label("avg_rating"),
                func.count(Rating.id).label("rating_count"),
            )
            .join(Rating, Rating.movie_id == Movie.id)
            .group_by(Movie.id)
            .having(func.count(Rating.id) >= min_ratings)
            .order_by(desc("avg_rating"))
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.all()

        return [(movie, round(float(avg_rating), 2), rating_count) for movie, avg_rating, rating_count in rows]

    @staticmethod
    async def get_movies_by_genre(
        db: AsyncSession, genre_name: str, limit: int = 10
    ) -> List[Movie]:
        """
        Feature 4: Genre Filter
        Filters movies directly by genre match.
        """
        stmt = (
            select(Movie)
            .where(Movie.genres.ilike(f"%{genre_name}%"))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())