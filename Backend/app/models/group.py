import uuid
from typing import TYPE_CHECKING

from pydantic import AwareDatetime
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.mixins.timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserGroup(SQLModel, table=True):
    __tablename__ = "user_groups"
    user_id: uuid.UUID = Field(
        foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    group_id: int = Field(foreign_key="group.id", primary_key=True, ondelete="CASCADE")
    created_at: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True,
    )


class Group(SQLModel, TimestampMixin, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    description: str | None = None
    created_by_user_id: uuid.UUID = Field(foreign_key="user.id")
    is_active: bool = Field(default=True)

    created_by_user: "User" = Relationship(
        back_populates="created_groups",
        sa_relationship_kwargs={
            "foreign_keys": "[Group.created_by_user_id]",
            "lazy": "selectin",
        },
    )
    users: list["User"] = Relationship(back_populates="groups", link_model=UserGroup)
