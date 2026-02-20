"""Application settings via Pydantic."""
import os
from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://adem@/social_empires?host=/var/run/postgresql"

    # JWT
    JWT_SECRET: str = "super-secret-mini-games-jwt-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # Paths (relative to project root)
    ASSETS_DIR: str = os.path.join(BASE_DIR, "assets")
    SAVES_DIR: str = os.path.join(BASE_DIR, "saves")
    VILLAGES_DIR: str = os.path.join(BASE_DIR, "villages")
    CONFIG_DIR: str = os.path.join(BASE_DIR, "config")
    CONFIG_PATCH_DIR: str = os.path.join(BASE_DIR, "config", "patch")
    MODS_DIR: str = os.path.join(BASE_DIR, "mods")
    QUESTS_DIR: str = os.path.join(BASE_DIR, "villages", "quests")
    STUB_DIR: str = os.path.join(BASE_DIR, "stub")

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 5050
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
