"""Central application settings, loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://negspace:negspace@localhost:5432/negative_space"
    redis_url: str = "redis://localhost:6379/0"
    nats_url: str = "nats://localhost:4222"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    # Detection engine tuning defaults (overridable per-entity via the API)
    default_heartbeat_tolerance: float = 2.5   # multiples of expected interval std-dev
    default_min_confidence: float = 0.55
    silence_poll_interval_seconds: int = 15


settings = Settings()
