import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.mixins.timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserSettings(SQLModel, TimestampMixin, table=True):
    __tablename__ = "user_settings"
    id: int = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", unique=True)
    receive_email_notifications: bool = False
    user: "User" = Relationship(back_populates="settings")
