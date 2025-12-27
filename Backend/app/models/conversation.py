from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlmodel import SQLModel, Field, Relationship
from app.models.mixins.timestamp_mixin import TimestampMixin


class Conversation(SQLModel, TimestampMixin, table=True):
    """Model for storing conversations between agents and customers."""
    __tablename__ = "conversations"
    
    id: UUID = Field(primary_key=True, index=True)
    agent_id: UUID = Field(foreign_key="user.id", nullable=False)
    customer_id: UUID = Field(nullable=False)
    audio: Optional[str] = Field(default=None, max_length=500)  # Audio URL for the conversation
    
    # Relationships
    messages: List["Message"] = Relationship(back_populates="conversation", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, agent_id={self.agent_id}, customer_id={self.customer_id})>"


class Message(SQLModel, TimestampMixin, table=True):
    """Model for storing individual messages within a conversation."""
    __tablename__ = "messages"
    
    id: UUID = Field(primary_key=True, index=True)
    conversation_id: UUID = Field(foreign_key="conversations.id", nullable=False)
    sender_role: str = Field(max_length=10)  # 'agent' or 'customer'
    message_type: str = Field(max_length=50)  # 'text', 'audio', etc.
    text_content: Optional[str] = None
    audio_url: Optional[str] = Field(max_length=500)
    
    # Relationships
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, sender_role={self.sender_role})>" 