"""
Async SQLAlchemy engine and session factory.
Import get_session in repositories; import engine in Alembic env.py.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Engine is created at startup via init_db(); repositories receive sessions via DI.
_engine = None
_session_factory = None


def init_db(database_url: str) -> None:
    """Call once at application startup with the DATABASE_URL."""
    global _engine, _session_factory

    # asyncpg requires postgresql+asyncpg:// scheme
    async_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    _engine = create_async_engine(async_url, echo=False, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine():
    if _engine is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _engine


def get_session_factory() -> async_sessionmaker:
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _session_factory
