"""SQLAlchemy integration."""

from pydantic import BaseModel
from sqlalchemy.engine import URL


class ConnectionPoolConfig(BaseModel):
    """Connection pool configuration."""

    enabled: bool = True
    size: int = 10
    max_overflow: int = 10
    timeout: int = 5


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str
    user: str
    password: str | None = None
    echo: bool = False
    connection_pool: ConnectionPoolConfig = ConnectionPoolConfig()

    @property
    def sqlalchemy_url(self) -> str:
        """Get the SQLAlchemy URL."""
        return URL.create(
            "postgresql+psycopg",
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.user,
            password=self.password,
        ).render_as_string(hide_password=False)
