from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from sqlmodel import SQLModel

from app.schemas.common import BaseDataTableRequest, BaseFilterParams

from .user import UserMinimalRead


class GroupBase(SQLModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None


class GroupCreateInput(GroupBase):
    pass


class GroupCreate(GroupBase):
    created_by_user_id: UUID


class GroupUpdate(SQLModel):
    name: str | None = None
    description: str | None = None


class GroupRead(GroupBase):
    id: int
    created_by_user: UserMinimalRead
    user_count: int = 0
    created_at: datetime


class GroupReadWithUsers(GroupRead):
    users: list[UserMinimalRead] = []


class GroupsRead(SQLModel):
    data: list[GroupRead]
    count: int


class GroupsFilterParams(SQLModel):
    created_by_user_id: UUID | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


class GroupUserAdd(SQLModel):
    user_ids: list[UUID]


class GroupFilters(BaseFilterParams):
    """Filters for group datatable."""

    user_id: UUID | None = None


class GroupsDataTableRequestBody(BaseDataTableRequest[GroupFilters]):
    """Request body for reading groups with advanced filtering."""

    filters: GroupFilters = Field(default_factory=GroupFilters)


class GroupsDataTable(BaseModel):
    """Response model for groups datatable."""

    data: Sequence[GroupRead]
    count: int
