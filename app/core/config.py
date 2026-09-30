from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "rflux API"
    DATABASE_URL: str
    REDIS_URL: str

settings = Settings() # pyright: ignore[reportCallIssue]