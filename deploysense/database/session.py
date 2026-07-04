"""
DeploySense — Database Engine & Session Management

WHY THIS EXISTS:
Every service that touches PostgreSQL needs a connection pool and a session
factory. This module creates them once and provides dependency-injection
helpers for FastAPI routes.

ARCHITECTURE DECISIONS:
  1. Async-first: We use asyncpg + SQLAlchemy async for non-blocking DB I/O.
     FastAPI is async — blocking DB calls would negate the concurrency benefit.

  2. Single engine per process: Connection pools are expensive. One pool per
     Python process, shared across all requests via the session factory.

  3. Session-per-request: Each HTTP request gets its own session (unit of work).
     The session is committed on success, rolled back on exception.

TRADEOFF:
  - We use SQLAlchemy ORM instead of raw SQL. This adds abstraction overhead
    but gives us: migration support (Alembic), relationship loading, type
    safety, and query composition. At our scale the ORM overhead is negligible.

ALTERNATIVES:
  - Raw asyncpg: Fastest, but no ORM, no migrations, manual SQL everywhere
  - Tortoise ORM: Async-native but smaller ecosystem than SQLAlchemy
  - encode/databases: Lightweight but lacks ORM features we'll need
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from deploysense.core import get_settings

# ─── Engine Creation ─────────────────────────────────────────────────────────
#
# Lazy initialization: engine is created on first import.
# pool_size=20: Handles 20 concurrent DB connections per process.
# max_overflow=10: Allows 10 additional connections during spikes.
# echo: SQL logging in development, silent in production.

_settings = get_settings()

engine = create_async_engine(
    _settings.database_url,
    pool_size=_settings.database_pool_size,
    max_overflow=_settings.database_max_overflow,
    echo=_settings.debug,
    pool_pre_ping=True,  # Detect stale connections before using them
)

# ─── Session Factory ─────────────────────────────────────────────────────────
#
# async_sessionmaker produces AsyncSession instances.
# expire_on_commit=False: Objects remain usable after commit without
# re-fetching. Important for returning data in API responses.

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─── Dependency Injection ────────────────────────────────────────────────────
#
# FastAPI dependency: `async for session in get_db_session():`
# Yields a session, commits on success, rolls back on exception.


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """
    FastAPI dependency that provides a database session per request.

    Usage in a route:
        @router.get("/deployments")
        async def list_deployments(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
