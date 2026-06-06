"""
DeploySense — SQLAlchemy Base Model

WHY THIS EXISTS:
All database models inherit from this base. It provides:
  1. A shared metadata object (Alembic needs this for autogenerate)
  2. Common columns (id, created_at, updated_at) — every table needs these
  3. A consistent __tablename__ convention

ARCHITECTURE DECISION:
We use UUIDs as primary keys instead of auto-incrementing integers.

WHY UUIDs:
  - No sequential ID guessing (security)
  - Safe for distributed ID generation (no coordination needed)
  - Works across services without a central ID authority
  - Aligns with the architecture doc schema

WHY NOT auto-increment:
  - Leaks information (how many records exist)
  - Problematic in multi-service or multi-region setups
  - Requires DB round-trip to get the ID after insert
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all DeploySense database models."""

    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at to any model.

    WHY a mixin instead of putting these in Base:
    Some tables (like deployment_events) only need created_at.
    Mixins let us compose behavior selectively.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    """
    Abstract base model with UUID primary key and timestamps.

    Every DeploySense table gets:
      - id: UUID primary key (generated in Python, not DB — allows pre-insert ID knowledge)
      - created_at: Set on insert
      - updated_at: Set on insert, updated on every modification
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
