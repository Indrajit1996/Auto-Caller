from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, EmailStr, field_validator
from sqlmodel import Field, SQLModel

from app.models.invitation import InvitationType
from app.schemas.user import UserMinimalRead


class InvitationBase(SQLModel):
    type: InvitationType = InvitationType.EMAIL
    email: EmailStr | None = None

    @field_validator("email")
    def lowercase_email(cls, v: str | None) -> str | None:
        return v.lower() if isinstance(v, str) else v


class InvitationCreate(InvitationBase):
    user_expiry_date: AwareDatetime | None = None
    created_by_user_id: UUID


class InvitationCreateInput(SQLModel):
    type: InvitationType = InvitationType.EMAIL
    emails: list[EmailStr] | None = None
    user_expiry_date: AwareDatetime | None = None

    @field_validator("emails")
    def email_required(cls, v: str | None, info) -> str | None:
        invitation_type = info.data["type"]

        if invitation_type == InvitationType.EMAIL and not v:
            raise ValueError("Email is required for email invitations")
        elif invitation_type == InvitationType.LINK and v:
            raise ValueError("Email should not be set for link invitations")

        return v


class InvitationRead(InvitationBase):
    id: int
    token: UUID
    created_by_user: UserMinimalRead
    user_expiry_date: datetime | None
    expires_at: datetime
    created_at: datetime
    active: bool
    registered_users: list[UserMinimalRead] = []


class CreateInvitationResponse(InvitationBase):
    token: UUID


class InvitationCreateResponse(SQLModel):
    existing_emails: list[EmailStr] = []
    created_invitations: list[CreateInvitationResponse] = []


class InvitationTokenRead(SQLModel):
    type: InvitationType
    email: str | None = None


class InvitationsRead(SQLModel):
    data: list[InvitationRead]
    count: int


class InvitationsFilterParams(SQLModel):
    type: InvitationType | Literal["all", ""] = "all"
    status: Literal["active", "inactive", "registered", "all", ""] = "all"
    created_by_user_id: UUID | None = None
    created_at: list[datetime | None] = [None, None]


class ReadInvitationsRequestBody(SQLModel):
    offset: int = 0
    limit: int = Field(default=10, le=100, gt=0)
    search: str = ""
    filters: InvitationsFilterParams = InvitationsFilterParams()
    order_by: str = "created_at"
    order: Literal["asc", "desc"] = "desc"


class InvitationTypeCount(SQLModel):
    email: int = 0
    link: int = 0
    registered: int = 0
    active_total: int = 0
    inactive_total: int = 0
    total: int = 0
