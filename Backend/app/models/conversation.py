import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.mixins.timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class SenderRole(str, Enum):
    AGENT = "agent"
    CUSTOMER = "customer"


class MessageType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"


class Conversation(SQLModel, TimestampMixin, table=True):
    __tablename__ = "conversations"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    customer_id: uuid.UUID
    
    agent: "User" = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(back_populates="conversation", cascade_delete=True)


class Message(SQLModel, TimestampMixin, table=True):
    __tablename__ = "messages"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversations.id", ondelete="CASCADE")
    sender_role: SenderRole
    message_type: MessageType
    text_content: str | None = None
    audio_url: str | None = None
    
    conversation: "Conversation" = Relationship(back_populates="messages")