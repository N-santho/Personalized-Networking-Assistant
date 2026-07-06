import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables and .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./networking.db"

    @property
    def is_sqlite_in_memory(self) -> bool:
        return self.DATABASE_URL == "sqlite://" or ":memory:" in self.DATABASE_URL

settings = Settings()
