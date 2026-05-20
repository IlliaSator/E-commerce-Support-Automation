from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    app_timezone: str = "Europe/Minsk"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_url: str = "http://localhost:8000"

    postgres_db: str = "ecommerce_support"
    postgres_user: str = "ecommerce_user"
    postgres_password: str = "ecommerce_password"
    database_url: str = "sqlite:///./local_ecommerce_support.db"

    telegram_bot_token: str | None = None
    manager_chat_ids: str = ""
    telegram_polling_enabled: bool = True

    admin_api_key: str = "change-me-local-only"

    openai_api_key: str | None = None
    llm_enabled: bool = False
    ai_provider: str = "local"
    ai_model_name: str = "local-mock"

    n8n_escalation_webhook_url: str | None = None
    n8n_report_webhook_url: str | None = None
    n8n_feedback_webhook_url: str | None = None
    n8n_logging_webhook_url: str | None = None

    data_dir: Path = Field(default_factory=lambda: Path("data"))

    @property
    def manager_chat_id_list(self) -> list[int]:
        ids: list[int] = []
        for raw in self.manager_chat_ids.split(","):
            raw = raw.strip()
            if not raw:
                continue
            try:
                ids.append(int(raw))
            except ValueError:
                continue
        return ids


@lru_cache
def get_settings() -> Settings:
    return Settings()
