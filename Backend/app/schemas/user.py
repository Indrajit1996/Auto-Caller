import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel

from app.core.config import config
from app.models.invitation import InvitationType
from app.models.user import UserStatus
from app.schemas.common import BaseDataTableRequest, BaseFilterParams


class UserMinimal(SQLModel):
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    status: UserStatus = Field(default=config.DEFAULT_USER_APPROVAL_FLOW.value)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_fields(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Name fields cannot be empty")
        return v

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower() if isinstance(v, str) else v


class UserMinimalRead(UserMinimal):
    id: uuid.UUID


class UserBase(UserMinimal):
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    invitation_token: uuid.UUID | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_fields(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Name fields cannot be empty")
        return v

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower() if isinstance(v, str) else v


class UserRegisterAdmin(UserRegister):
    is_superuser: bool = False


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class UserPublic(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None
    updated_at: datetime | None = None


class UserGroupRead(SQLModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime


class UserInvitationRead(SQLModel):
    id: int
    token: uuid.UUID
    type: InvitationType
    created_at: datetime
    created_by_user: UserMinimal


class UserDetail(UserPublic):
    groups: Sequence[UserGroupRead] = []
    invitation: UserInvitationRead | None = None


class UsersDataTable(SQLModel):
    data: list[UserPublic]
    count: int = 0


class UsersMinimalPublic(SQLModel):
    data: list[UserMinimalRead]
    count: int


class UsersFilterParams(BaseFilterParams):
    status: UserStatus | Literal["all", ""] = ""
    role: Literal["all", "user", "superuser", ""] = ""
    group: int | Literal["all", ""] = ""
    exclude_group: int | None = None
    created_at: list[datetime | None] = [None, None]


class ReadUsersRequestBody(BaseDataTableRequest[UsersFilterParams]):
    filters: UsersFilterParams = UsersFilterParams()


class UserStatusCount(SQLModel):
    active: int = 0
    pending_email_verification: int = 0
    pending_admin_approval: int = 0
    deactivated: int = 0
    total: int = 0


class UserStatusUpdate(SQLModel):
    status: UserStatus = Field(
        description="User status - can only be active or deactivated",
    )

    @field_validator("status")
    def validate_status(cls, v: UserStatus) -> UserStatus:
        if v not in [UserStatus.ACTIVE, UserStatus.DEACTIVATED]:
            raise ValueError("Status must be either active or deactivated")
        return v


class UserStatusResponse(SQLModel):
    status: UserStatus
