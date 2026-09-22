from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent
WIB = ZoneInfo("Asia/Jakarta")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    database_url: str = f"sqlite:///{ROOT / 'data' / 'afs.db'}"
    sectors_api_key: str = ""
    sectors_base_url: str = "https://api.sectors.app"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    base_web_url: str = "http://localhost:8000"
    admin_password: str = "admin"
    session_secret: str = "dev-secret-change-me"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    gemini_timeout_seconds: float = 20.0
    run_interval_days: int = 3
    universe_path: Path = ROOT / "config" / "universe.json"
    backtest_cases_path: Path = ROOT / "config" / "backtest_cases.json"
    tts_voice: str = "id-ID-ArdiNeural"
    audio_dir: Path = ROOT / "data" / "audio"

    @property
    def sqlalchemy_url(self) -> str:
        # Heroku provides postgres://; SQLAlchemy + psycopg3 needs postgresql+psycopg://
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
