import uuid
from datetime import datetime, timedelta, timezone

from pydantic import AwareDatetime
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.core.config import config
from app.models.mixins.timestamp_mixin import TimestampMixin
from app.models.user import User


class PasswordReset(SQLModel, TimestampMixin, table=True):
    __tablename__ = "password_reset"
    id: int = Field(default=None, primary_key=True)
    token: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    expires_at: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        + timedelta(hours=config.PASSWORD_RESET_TOKEN_EXPIRY_IN_HOURS),
        nullable=False,
        index=True,
    )

    user: User = Relationship(back_populates="password_reset")

    @property
    def is_active(self) -> bool:
        return self.expires_at > datetime.now(timezone.utc)
