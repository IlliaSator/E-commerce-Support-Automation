from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str | None = None
    manager_chat_ids: str = ""
    backend_url: str = "http://localhost:8000"
    admin_api_key: str = "change-me-local-only"
    telegram_polling_enabled: bool = True

    @property
    def manager_ids(self) -> set[int]:
        result: set[int] = set()
        for raw in self.manager_chat_ids.split(","):
            raw = raw.strip()
            if not raw:
                continue
            try:
                result.add(int(raw))
            except ValueError:
                continue
        return result


@lru_cache
def get_settings() -> BotSettings:
    return BotSettings()
