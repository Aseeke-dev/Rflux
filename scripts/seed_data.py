import sys
from pathlib import Path
import asyncio

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sentence_transformers import SentenceTransformer
from app.core.database import SessionLocal
from app.models.movie import Movie
from app.models.user import User
from sqlalchemy import select

print("Loading sentence-transformer model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

SAMPLE_MOVIES = [
    {
        "id": 1,
        "title": "Inception",
        "genres": "Action|Sci-Fi|Thriller",
        "overview": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
    },
    {
        "id": 2,
        "title": "Interstellar",
        "genres": "Adventure|Drama|Sci-Fi",
        "overview": "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft, along with a team of researchers, to find a new planet for humans.",
    },
    {
        "id": 3,
        "title": "The Dark Knight",
        "genres": "Action|Crime|Drama",
        "overview": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
    },
    {
        "id": 4,
        "title": "The Godfather",
        "genres": "Crime|Drama",
        "overview": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
    },
    {
        "id": 5,
        "title": "Pulp Fiction",
        "genres": "Crime|Drama",
        "overview": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
    },
    {
        "id": 6,
        "title": "The Matrix",
        "genres": "Action|Sci-Fi",
        "overview": "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth - the life he knows is the elaborate deception of an evil cyber-intelligence.",
    },
]

SAMPLE_USERS = [
    {"id": 1, "username": "alice", "email": "alice@example.com"},
    {"id": 2, "username": "bob", "email": "bob@example.com"},
]


async def seed_database():
    db = SessionLocal()
    try:
        print("Seeding initial users...")
        for u_data in SAMPLE_USERS:
            query = select(User).where(User.id==u_data["id"])
            result = await db.execute(query)
            existing_user = result.scalar_one_or_none()
            if not existing_user:
                user = User(**u_data)
                db.add(user)

        print("Generating embeddings and seeding movies...")
        for m_data in SAMPLE_MOVIES:
            query = select(Movie).where(Movie.id==m_data["id"])
            result = await db.execute(query)
            existing_movie = result.scalar_one_or_none()
            if not existing_movie:
                text_to_embed = f"{m_data['title']}. Genres: {m_data['genres']}. Overview: {m_data['overview']}"
                
                embedding_vector = model.encode(text_to_embed).tolist()

                movie = Movie(
                    id=m_data["id"],
                    title=m_data["title"],
                    genres=m_data["genres"],
                    overview=m_data["overview"],
                    embeddings=embedding_vector,
                )
                
                db.add(movie)

        await db.commit()
        print("Data ingestion and embedding generation completed successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        await db.rollback()
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
