from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "FPTU DMS Vision Backend Engine"
    SERVICE_NAME: str = "dms-backend"
    VERSION: str = "1.0.0"
    APP_ENV: Literal["development", "test", "production"] = "development"
    API_V1_PREFIX: str = "/api/v1"
    LEGACY_API_PREFIX: str = "/api"

    DATASET_DIR: Path = Path("./data")
    OUTPUT_SUBMISSION_DIR: Path = Path("./submissions")
    STREAM_FPS: float = Field(default=20, gt=0)
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    AI_SOURCE_MODE: Literal["file", "external_api"] = "file"
    AI_API_BASE_URL: str = ""
    AI_API_PATH: str = "/v1/analyze/trip"
    AI_API_KEY: str = ""
    AI_API_TIMEOUT_SEC: float = Field(default=30, gt=0)
    AI_API_MAX_RETRIES: int = Field(default=2, ge=0)
    AI_API_CONCURRENCY: int = Field(default=4, ge=1)
    AI_FALLBACK_TO_FILE: bool = True

    LLM_PROVIDER: Literal["none", "openai_compatible"] = "none"
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""

    CARSKY_ENABLED: bool = False
    CARSKY_MODE: Literal["external", "offline"] = "offline"
    CARSKY_BASE_URL: str = ""
    CARSKY_API_KEY: str = ""
    CARSKY_ROOM_ID: str = ""
    CARSKY_NODE_KEY: str = ""
    CARSKY_TIMEOUT_SEC: float = Field(default=1.5, gt=0)

    @field_validator("API_V1_PREFIX", "LEGACY_API_PREFIX", "AI_API_PATH")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        return normalized.rstrip("/") or "/"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def reject_wildcard_cors(self) -> "Settings":
        if "*" in self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS cannot contain '*' when credentials are enabled")
        return self

    @computed_field
    @property
    def FRAME_INTERVAL_SEC(self) -> float:
        return 1.0 / self.STREAM_FPS

    @property
    def external_ai_configured(self) -> bool:
        if self.AI_SOURCE_MODE == "file":
            return True
        return bool(self.AI_API_BASE_URL.strip() and self.AI_API_KEY.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
