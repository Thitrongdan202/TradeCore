"""
TradeCore — Application Settings
Uses Pydantic BaseSettings to load from environment / .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────────────
    app_env: str = "development"
    app_debug: bool = True

    # Security (JWT)
    jwt_secret: str = "super-secret-tradecore-key" # In production, set via env
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    app_secret_key: str = "change-me" # Used for older/other things, keeping to not break .env
    
    # Password Encryption
    tradecore_password_encryption_key: str = "" # MUST be 32 url-safe base64-encoded bytes for Fernet

    # Database
    postgres_user: str = "tradecore"
    app_title: str = "TradeCore API"
    app_version: str = "0.1.0"

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+psycopg2://tradecore:tradecore_dev_pw@localhost:5432/tradecore"
    )
    async_database_url: str = (
        "postgresql+asyncpg://tradecore:tradecore_dev_pw@localhost:5432/tradecore"
    )

    # ── JWT ──────────────────────────────────────────────────────────────
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # ── CORS ─────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Pagination ───────────────────────────────────────────────────────
    default_page_size: int = 50
    max_page_size: int = 500

    # ── Storage ──────────────────────────────────────────────────────────
    tradecore_storage_path: str = "C:/Users/thitr/.gemini/antigravity/scratch/tradecore/storage"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
