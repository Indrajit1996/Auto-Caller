from typing import Generic, Literal, TypeVar

from pydantic import Field
from sqlmodel import SQLModel


class BaseFilterParams(SQLModel):
    """Base filter parameters that can be extended by specific models"""

    pass


T = TypeVar("T", bound=BaseFilterParams)


class BaseDataTableRequest(SQLModel, Generic[T]):
    """Base request body for datatable operations"""

    offset: int = 0
    limit: int = Field(default=10, le=100, gt=0)
    search: str = ""
    order_by: str = "created_at"
    order: Literal["asc", "desc"] = "desc"
    filters: T


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
