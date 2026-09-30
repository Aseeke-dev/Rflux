import asyncio
import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from app.core.database import engine
from app.core.base import Base
import app.models


async def init_db():
    async with engine.begin() as conn:
        print("Enabling pgvector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        print("Creating all database tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())