from pydantic import AwareDatetime
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from sqlmodel import Field


class TimestampMixin:
    """A mixin to add created_at and updated_at timestamps to models."""

    created_at: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),
        default=func.now(),
        sa_column_kwargs={"onupdate": func.now()},
        nullable=False,
        index=True,
    )
