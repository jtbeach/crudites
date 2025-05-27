"""FastAPI integration."""

from pydantic import BaseModel


class CorsConfig(BaseModel):
    """CORS configuration."""

    allow_origins: list[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
