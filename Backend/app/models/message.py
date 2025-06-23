import uuid
from typing import TYPE_CHECKING

from pydantic import AwareDatetime
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from sqlmodel import Field, Relationship, SQLModel

from .mixins.timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from .conversation import Conversation


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversations.id")
    sender_role: str = Field(max_length=10)
    message_type: str = Field(max_length=50)
    text_content: str | None = None
    audio_url: str | None = None
    created_at: AwareDatetime = Field(
        sa_type=DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )

    conversation: "Conversation" = Relationship(back_populates="messages")