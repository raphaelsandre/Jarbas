from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

import secrets

from app.config import settings


api_key_scheme = APIKeyHeader(
    name="X-Jarbas-Key",
    auto_error=False,
)


async def authenticate_request(
    request: Request,
    api_key: Annotated[str | None, Depends(api_key_scheme)],
) -> None:
    if request.headers.get("user-agent") != settings.jarbas_user_agent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    if api_key is None or not secrets.compare_digest(
        api_key,
        settings.jarbas_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
