"""Tests for SQLAlchemy integration."""

from crudites.integrations.sqlalchemy import ConnectionPoolConfig, DatabaseConfig


def test_connection_pool_config_defaults() -> None:
    """Test ConnectionPoolConfig default values."""
    config = ConnectionPoolConfig()
    assert config.enabled is True
    assert config.size == 10
    assert config.max_overflow == 10
    assert config.timeout == 5


def test_connection_pool_config_custom_values() -> None:
    """Test ConnectionPoolConfig with custom values."""
    config = ConnectionPoolConfig(enabled=False, size=20, max_overflow=5, timeout=10)
    assert config.enabled is False
    assert config.size == 20
    assert config.max_overflow == 5
    assert config.timeout == 10


def test_database_config_defaults() -> None:
    """Test DatabaseConfig default values."""
    config = DatabaseConfig(database="testdb", user="testuser")
    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "testdb"
    assert config.user == "testuser"
    assert config.password is None
    assert config.echo is False
    assert isinstance(config.connection_pool, ConnectionPoolConfig)


def test_database_config_custom_values() -> None:
    """Test DatabaseConfig with custom values."""
    config = DatabaseConfig(
        host="db.example.com",
        port=5433,
        database="prod_db",
        user="admin",
        password="secret",
        echo=True,
        connection_pool=ConnectionPoolConfig(size=5),
    )
    assert config.host == "db.example.com"
    assert config.port == 5433
    assert config.database == "prod_db"
    assert config.user == "admin"
    assert config.password == "secret"
    assert config.echo is True
    assert config.connection_pool.size == 5


def test_database_config_sqlalchemy_url() -> None:
    """Test DatabaseConfig sqlalchemy_url property."""
    config = DatabaseConfig(
        host="db.example.com",
        port=5433,
        database="testdb",
        user="testuser",
        password="secret",
    )
    expected_url = "postgresql+psycopg://testuser:secret@db.example.com:5433/testdb"
    assert config.sqlalchemy_url == expected_url


def test_database_config_sqlalchemy_url_no_password() -> None:
    """Test DatabaseConfig sqlalchemy_url property without password."""
    config = DatabaseConfig(
        host="db.example.com", port=5433, database="testdb", user="testuser"
    )
    expected_url = "postgresql+psycopg://testuser@db.example.com:5433/testdb"
    assert config.sqlalchemy_url == expected_url
