"""Reusable SQLAlchemy mixins."""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import text, func
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column


class ColumnSortOrder(Enum):
    """See https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column.params.sort_order.

    We want to make sure that primary key columns and first and that audit columns are last when we create tables
    in the database from the models.
    """

    PRIMARY_KEY = -1
    DEFAULT = 0
    AUDIT = 1


class UUIDPrimaryKeyMixin(MappedAsDataclass):
    """Mixin which adds our standard definition of a UUID primary key to the model."""

    id: Mapped[UUID] = mapped_column(  # noqa: A003
        init=False,
        default=None,
        server_default=text("gen_random_uuid()"),
        primary_key=True,
        sort_order=ColumnSortOrder.PRIMARY_KEY.value,
    )


class AuditTimestampMixin(MappedAsDataclass):
    """Mixin which adds our standard timestamp fields for auditing purposes."""

    created_at: Mapped[datetime] = mapped_column(
        default=None,
        server_default=func.now(),
        index=True,
        sort_order=ColumnSortOrder.AUDIT.value,
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        default=None,
        server_default=func.now(),
        index=True,
        sort_order=ColumnSortOrder.AUDIT.value,
    )


class SoftDeleteMixin(MappedAsDataclass):
    """Mixin which adds our standard soft delete fields."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        default=None, sort_order=ColumnSortOrder.AUDIT.value
    )
