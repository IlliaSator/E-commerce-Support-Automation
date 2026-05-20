from fastapi import Header, HTTPException, status

from backend.app.core.config import get_settings


def require_admin_api_key(x_admin_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not x_admin_api_key or x_admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key is required for this endpoint.",
        )
