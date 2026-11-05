import json
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite+aiosqlite:///{BACKEND_DIR.as_posix()}/chatur.db"
    secret_key: str = "chatur-dev-secret-key-change-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    first_superadmin_email: str = "admin@chatur.school"
    first_superadmin_password: str = "Admin@CHATUR2024"
    first_school_name: str = "CHATUR Demo School"
    # AI content provider (backend only). ai_provider: gemini | anthropic | none
    ai_provider: str = "none"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"
    ai_timeout_seconds: float = 60.0
    reference_dir: str = ""  # local dir holding NCERT chapter PDFs (never bundled)
    cors_origins: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    return [i.strip() for i in v[1:-1].split(",") if i.strip()]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
