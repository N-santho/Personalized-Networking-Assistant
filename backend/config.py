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
    FORCE_FALLBACK: bool = False

    def __init__(self, **values):
        super().__init__(**values)
        # Ensure OS environment variables take absolute precedence over any .env file
        if "HOST" in os.environ:
            self.HOST = os.environ["HOST"]
        if "PORT" in os.environ:
            try:
                self.PORT = int(os.environ["PORT"])
            except ValueError:
                pass
        if "LOG_LEVEL" in os.environ:
            self.LOG_LEVEL = os.environ["LOG_LEVEL"]
        if "DATABASE_URL" in os.environ:
            self.DATABASE_URL = os.environ["DATABASE_URL"]
        if "FORCE_FALLBACK" in os.environ:
            self.FORCE_FALLBACK = os.environ["FORCE_FALLBACK"].lower() in ("true", "1", "yes", "on")

    @property
    def is_sqlite_in_memory(self) -> bool:
        return self.DATABASE_URL == "sqlite://" or ":memory:" in self.DATABASE_URL

settings = Settings()
