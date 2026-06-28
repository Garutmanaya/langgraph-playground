from __future__ import annotations

import os

from fastapi import Header, HTTPException


API_KEY = os.getenv("AGENT_API_KEY", "dev-secret")


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
