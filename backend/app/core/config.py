"""Application configuration loaded from environment variables."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration — all values overridable via env vars or .env file."""

    # Database
    DATABASE_URL: str = "sqlite:///./wine_cellar.db"

    # JWT
    JWT_SECRET: str = "grapehub-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 h

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 10

    # CORS
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
