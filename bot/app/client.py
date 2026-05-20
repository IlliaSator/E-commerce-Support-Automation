from __future__ import annotations

from typing import Any

import httpx

from bot.app.config import BotSettings


class BackendClient:
    def __init__(self, settings: BotSettings) -> None:
        self.settings = settings
        self.base_url = settings.backend_url.rstrip("/")

    async def support_message(
        self,
        *,
        customer_id: str,
        chat_id: int,
        username: str | None,
        message_text: str,
    ) -> dict[str, Any]:
        payload = {
            "customer_id": customer_id,
            "channel": "telegram",
            "telegram_chat_id": str(chat_id),
            "username": username,
            "message_text": message_text,
            "metadata": {"interface": "telegram_bot"},
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(f"{self.base_url}/support/message", json=payload)
            response.raise_for_status()
            return response.json()

    async def admin_get(self, path: str) -> Any:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers={"X-Admin-API-Key": self.settings.admin_api_key},
            )
            response.raise_for_status()
            return response.json()

    async def admin_post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=payload or {},
                headers={"X-Admin-API-Key": self.settings.admin_api_key},
            )
            response.raise_for_status()
            return response.json()
