import sys
import os
import zipfile
import urllib.request
import pandas as pd
import asyncio
from pathlib import Path

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sentence_transformers import SentenceTransformer
from app.core.database import SessionLocal
from app.models.movie import Movie
from app.models.user import User
from app.models.rating import Rating

DATASET_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
ZIP_PATH = "ml-latest-small.zip"
EXTRACT_DIR = "data"

print("Loading sentence-transformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")


def download_and_extract():
    """Download and extract MovieLens 100k dataset if not present."""
    if not os.path.exists(EXTRACT_DIR):
        print("Downloading MovieLens 100k dataset...")
        urllib.request.urlretrieve(DATASET_URL, ZIP_PATH)
        print("Extracting dataset...")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)
        os.remove(ZIP_PATH)
        print("Dataset ready!")


async def seed_massive_data():
    download_and_extract()
    
    movies_df = pd.read_csv(f"{EXTRACT_DIR}/ml-latest-small/movies.csv")
    ratings_df = pd.read_csv(f"{EXTRACT_DIR}/ml-latest-small/ratings.csv")

    async with SessionLocal() as db:
        try:
            print("1. Seeding Users...")
            unique_user_ids = ratings_df["userId"].unique()[:50]  # Seed first 50 active users
            for uid in unique_user_ids:
                uid = int(uid)
                stmt = select(User).where(User.id == uid)
                res = await db.execute(stmt)
                if not res.scalar_one_or_none():
                    db.add(User(id=uid, username=f"user_{uid}", email=f"user_{uid}@example.com"))
            await db.commit()

            print("2. Generating Embeddings & Seeding Movies in Batches...")
            # Limit to 500 movies for rapid batch seeding (remove [:500] to load all 9,000+ movies)
            movies_subset = movies_df.head(500)
            
            # Prepare textual content for batch encoding
            descriptions = [
                f"{row['title']}. Genres: {row['genres'].replace('|', ', ')}"
                for _, row in movies_subset.iterrows()
            ]
            
            print("Encoding vector embeddings in batch...")
            embeddings = model.encode(descriptions, batch_size=64, show_progress_bar=True).tolist()

            for idx, (_, row) in enumerate(movies_subset.iterrows()):
                movie_id = int(row["movieId"])
                stmt = select(Movie).where(Movie.id == movie_id)
                res = await db.execute(stmt)
                if not res.scalar_one_or_none():
                    db.add(
                        Movie(
                            id=movie_id,
                            title=row["title"],
                            genres=row["genres"],
                            overview=f"A popular movie titled {row['title']} covering genres: {row['genres']}.",
                            embeddings=embeddings[idx],
                        )
                    )
            await db.commit()

            print("3. Seeding User Ratings...")
            # Seed ratings belonging to seeded users and movies
            valid_ratings = ratings_df[
                (ratings_df["userId"].isin(unique_user_ids)) & 
                (ratings_df["movieId"].isin(movies_subset["movieId"]))
            ]

            for _, row in valid_ratings.iterrows():
                u_id, m_id, score = int(row["userId"]), int(row["movieId"]), float(row["rating"])
                stmt = select(Rating).where(Rating.user_id == u_id, Rating.movie_id == m_id)
                res = await db.execute(stmt)
                if not res.scalar_one_or_none():
                    db.add(Rating(user_id=u_id, movie_id=m_id, rating=score))

            await db.commit()
            print("Massive data ingestion completed successfully!")

        except Exception as e:
            print(f"Error during massive ingestion: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(seed_massive_data())
