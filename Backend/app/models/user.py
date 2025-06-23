import uuid
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import AwareDatetime, EmailStr
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.core.config import config
from app.models.group import UserGroup
from app.models.invitation import InvitationRegistration
from app.models.mixins.timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.invitation import Invitation
    from app.models.notification import Notification
    from app.models.password_reset import PasswordReset
    from app.models.user_settings import UserSettings
    from app.models.conversation import Conversation


class UserStatus(Enum):
    """User status"""

    ACTIVE = "active"
    PENDING_ADMIN_APPROVAL = "pending_admin_approval"
    PENDING_EMAIL_VERIFICATION = "pending_email_verification"
    DEACTIVATED = "deactivated"


class User(SQLModel, TimestampMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    status: UserStatus = Field(
        default_factory=lambda: config.DEFAULT_USER_APPROVAL_FLOW.value
    )
    email_verification_token: uuid.UUID | None = Field(
        default_factory=uuid.uuid4, nullable=True, unique=True
    )
    is_superuser: bool = False
    last_login: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),
        default=func.now(),
        sa_column_kwargs={"onupdate": func.now()},
        nullable=True,
        index=True,
    )

    settings: "UserSettings" = Relationship(back_populates="user", cascade_delete=True)
    notifications: list["Notification"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    created_invitations: list["Invitation"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "[Invitation.created_by_user_id]"},
    )
    groups: list["Group"] = Relationship(back_populates="users", link_model=UserGroup)
    created_groups: list["Group"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "[Group.created_by_user_id]"},
    )
    invitation: "Invitation" = Relationship(
        back_populates="registered_users", link_model=InvitationRegistration
    )
    password_reset: "PasswordReset" = Relationship(
        back_populates="user", cascade_delete=True
    )
    conversations: list["Conversation"] = Relationship(
        back_populates="agent",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return (
            f"{self.first_name} {self.last_name}"
            if self.first_name and self.last_name
            else self.email
        )
