import uuid
from enum import Enum

from pydantic import AwareDatetime
from sqlalchemy import JSON, Column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from sqlmodel import Field, SQLModel


class Model(Enum):
    GROUP = "group"
    INVITATION = "invitation"
    USER = "user"


class Action(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    id: int = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", ondelete="SET NULL", nullable=True
    )
    model: Model
    record_id: str | None = Field(
        nullable=True
    )  # This is a string because it can be a UUID or int
    action: Action
    description: str | None = Field(default=None)
    meta_data: dict = Field(sa_column=Column(JSON), default={})
    created_at: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True,
    )
