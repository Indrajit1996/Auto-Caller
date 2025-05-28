import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import AwareDatetime, EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.core.config import config
from app.models.mixins.timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class InvitationType(str, Enum):
    LINK = "link"
    EMAIL = "email"


class InvitationRegistration(SQLModel, table=True):
    __tablename__ = "invitation_registrations"
    invitation_id: int = Field(
        foreign_key="invitation.id", primary_key=True, ondelete="CASCADE"
    )
    user_id: uuid.UUID = Field(
        foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )


class Invitation(SQLModel, TimestampMixin, table=True):
    id: int = Field(default=None, primary_key=True)
    type: InvitationType = Field(default=InvitationType.EMAIL)
    token: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: EmailStr | None = None
    created_by_user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    user_expiry_date: AwareDatetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    expires_at: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        + timedelta(hours=config.INVITATION_EXPIRY_IN_HOURS),
    )

    created_by_user: "User" = Relationship(
        back_populates="created_invitations",
        sa_relationship_kwargs={"foreign_keys": "{Invitation.created_by_user_id}"},
    )
    registered_users: list["User"] = Relationship(
        back_populates="invitation", link_model=InvitationRegistration
    )

    @property
    def active(self) -> bool:
        return self.expires_at > datetime.now(timezone.utc)
