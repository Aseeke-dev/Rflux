import sys
from pathlib import Path
import asyncio

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.rating import Rating

SAMPLE_RATINGS = [
    {"user_id": 1, "movie_id": 1, "rating": 5.0},
    {"user_id": 1, "movie_id": 2, "rating": 4.5},
    {"user_id": 1, "movie_id": 6, "rating": 4.8},
    {"user_id": 1, "movie_id": 3, "rating": 4.0},

    {"user_id": 2, "movie_id": 4, "rating": 5.0},
    {"user_id": 2, "movie_id": 5, "rating": 4.7},
    {"user_id": 2, "movie_id": 3, "rating": 4.2},
]


async def seed_ratings():
    async with SessionLocal() as db:
        try:
            print("Seeding sample ratings...")
            for r_data in SAMPLE_RATINGS:
                # Check if rating already exists to prevent duplicate entries
                query = select(Rating).where(
                    Rating.user_id == r_data["user_id"],
                    Rating.movie_id == r_data["movie_id"],
                )
                result = await db.execute(query)
                existing_rating = result.scalar_one_or_none()

                if not existing_rating:
                    rating = Rating(**r_data)
                    db.add(rating)

            await db.commit()
            print("Ratings seeded successfully!")

        except Exception as e:
            print(f"Error seeding ratings: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(seed_ratings())