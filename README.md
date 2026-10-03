# Rflux

Rflux is a movie discovery and recommendation API built with FastAPI. It supports
personalized recommendations, natural-language movie search using vector
embeddings, top-rated movies, genre filtering, and rating submission.

The API is served under `/api/v1`. Interactive API documentation is available at
`/docs` when the application is running.

## Requirements

- Python 3.13 or newer for running the API directly
- Docker Engine and Docker Compose v2 for the containerized setup
- Internet access on first startup to download the
  `all-MiniLM-L6-v2` sentence-transformer model

The Docker Compose setup runs the API, PostgreSQL with the `pgvector` extension,
and Redis.

## First-time setup

Clone the repository and change into its root directory:

```bash
git clone https://github.com/Aseeke-dev/Rflux.git
cd Rflux
```

### Run with Docker Compose

Build the API image and start the services:

```bash
docker compose up --build -d
docker compose ps
```

The Compose configuration publishes these ports on the host:

| Service | Host address | Container port |
| --- | --- | --- |
| API | `http://localhost:8000` | `8000` |
| PostgreSQL | `localhost:5433` | `5432` |
| Redis | `localhost:6380` | `6379` |

The API connects to PostgreSQL and Redis using the Compose service names
`db` and `redis`; use the host addresses above only when connecting from outside
the Compose network.

Create the database extension and application tables, then add the sample movies,
users, and ratings:

```bash
docker compose exec web python scripts/init_db.py
docker compose exec web python scripts/seed_data.py
docker compose exec web python scripts/seed_ratings.py
```

The sample seed data is intended for development. The optional
`scripts/seed_massive_data.py` script downloads MovieLens data and generates
embeddings for a larger sample.

Open the API documentation at <http://localhost:8000/docs>.

To follow the application logs or stop the services:

```bash
docker compose logs -f web
docker compose down
```

`docker compose down` preserves the named database and Redis volumes. To remove
those volumes and their data as well, run `docker compose down --volumes`.

### Run locally without Docker

Start PostgreSQL with the `pgvector` extension and Redis, then install the
project dependencies. For example, with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --locked
```

Set the connection settings for your local services before starting the API:

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgrespassword@localhost:5433/rflux_db"
export REDIS_URL="redis://localhost:6380/0"
```

Initialize and seed the database, then start the development server:

```bash
uv run python scripts/init_db.py
uv run python scripts/seed_data.py
uv run python scripts/seed_ratings.py
uv run uvicorn app.main:app --reload
```

The API documentation is available at <http://localhost:8000/docs>.

## Configuration

The application reads `DATABASE_URL` and `REDIS_URL` from the environment or
from a local `.env` file. In Docker Compose, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, and `POSTGRES_DB` configure the database. Their defaults
are `postgres`, `postgrespassword`, and `rflux_db`; set your own values in
`.env` for local development as needed.

Do not commit `.env` or use the default development credentials in a shared or
production environment.

## API endpoints

All application endpoints are prefixed with `/api/v1/movies`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/for-you/{user_id}` | Recommend movies based on a user's highly rated movies |
| `POST` | `/search?query=...` | Search for movies using a natural-language query |
| `GET` | `/top-rated` | List the highest-rated movies |
| `GET` | `/genre/{genre_name}` | Find movies by genre |
| `POST` | `/ratings` | Submit a user's rating for a movie |

Query parameters such as recommendation limits and response schemas are
documented in Swagger UI at `/docs`.

## Tests

Run the test suite with:

```bash
uv run pytest
```