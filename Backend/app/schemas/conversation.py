from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel


class MessageBase(BaseModel):
    sender_role: str
    message_type: str
    text_content: Optional[str] = None
    audio_url: Optional[str] = None


class MessageCreate(MessageBase):
    conversation_id: UUID


class MessageUpdate(BaseModel):
    text_content: Optional[str] = None
    audio_url: Optional[str] = None


class Message(MessageBase):
    id: UUID
    conversation_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    agent_id: UUID
    customer_id: UUID
    audio: Optional[str] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    audio: Optional[str] = None


class Conversation(ConversationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []

    class Config:
        from_attributes = True


class ConversationWithMessages(Conversation):
    messages: List[Message] = [] 