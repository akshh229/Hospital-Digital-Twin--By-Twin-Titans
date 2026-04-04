"""
Lazarus Backend Configuration

Stack Choice: FastAPI + Python 3.11
Rationale: Python excels at data processing (pandas), cryptography,
and scientific computing. FastAPI provides async support, automatic
OpenAPI docs, and Pydantic type safety - critical for medical data.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "Lazarus Medical Forensic Recovery System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = (
        "postgresql://lazarus_user:lazarus_password_change_me@localhost:5432/lazarus"
    )
    REDIS_URL: str = "redis://:redis_password_change_me@localhost:6379/0"

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    ALERT_BPM_LOW: int = 60
    ALERT_BPM_HIGH: int = 100
    ALERT_DEBOUNCE_COUNT: int = 2

    TELEMETRY_BYTE_ORDER: str = "big"
    BPM_OFFSET: int = 0
    BPM_LENGTH: int = 2
    SPO2_OFFSET: int = 2
    SPO2_LENGTH: int = 2

    BPM_MIN: int = 20
    BPM_MAX: int = 220
    SPO2_MIN: int = 50
    SPO2_MAX: int = 100

    PARITY_SAMPLE_COUNT: int = 10
    MIN_CONFIDENCE_THRESHOLD: float = 0.5

    WS_HEARTBEAT_INTERVAL: int = 30
    WS_POLL_INTERVAL_SECONDS: int = 2
settings = Settings()
