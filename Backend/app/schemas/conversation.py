from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel

from app.models.conversation import MessageType, SenderRole


class ConversationBase(SQLModel):
    agent_id: UUID
    customer_id: UUID


class ConversationCreate(ConversationBase):
    pass


class ConversationPublic(ConversationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ConversationList(SQLModel):
    data: list[ConversationPublic]
    count: int


class MessageBase(SQLModel):
    sender_role: SenderRole
    message_type: MessageType
    text_content: str | None = None
    audio_url: str | None = None


class MessageCreate(MessageBase):
    conversation_id: UUID


class MessagePublic(MessageBase):
    id: UUID
    conversation_id: UUID
    created_at: datetime


class MessageList(SQLModel):
    data: list[MessagePublic]
    count: int