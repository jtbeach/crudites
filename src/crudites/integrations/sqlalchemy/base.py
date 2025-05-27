"""SQLAlchemy declarative base for Crudites applications."""

import datetime
import enum
from typing import Final

from sqlalchemy import TIMESTAMP, Enum as SAEnum, MetaData
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

NAMING_CONVENTION: Final = {
    "ix": "%(table_name)s_%(column_0_N_name)s_idx",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
    "ck": "%(table_name)s_%(column_0_N_name)s_check",
    "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(MappedAsDataclass, DeclarativeBase):
    """Base class for all SQLAlchemy models in Crudites applications.

    By inheriting from this class, models will be converted to dataclasses and their
    constructor will accept kwargs only.

    The metadata is configured with a standard naming convention for indexes,
    unique constraints, check constraints, foreign keys, and primary keys.

    The type_annotation_map is configured with the default type annotations for
    datetime and enum.Enum.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {
        datetime.datetime: TIMESTAMP(timezone=True),
        enum.Enum: SAEnum(enum.Enum, inherit_schema=True),
    }
