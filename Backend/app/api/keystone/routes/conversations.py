from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.api.deps import get_db, get_current_user
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.conversation import (
    Conversation as ConversationSchema,
    ConversationCreate,
    ConversationUpdate,
    Message as MessageSchema,
    MessageCreate,
    MessageUpdate,
    ConversationWithMessages
)

router = APIRouter()


@router.post("/", response_model=ConversationSchema)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation."""
    # Check if conversation already exists between agent and customer
    existing_conversation = db.exec(
        select(Conversation).where(
            Conversation.agent_id == conversation.agent_id,
            Conversation.customer_id == conversation.customer_id
        )
    ).first()
    
    if existing_conversation:
        return existing_conversation
    
    db_conversation = Conversation(**conversation.dict())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.get("/", response_model=List[ConversationSchema])
def get_conversations(
    agent_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversations with optional filtering."""
    query = select(Conversation)
    
    if agent_id:
        query = query.where(Conversation.agent_id == agent_id)
    if customer_id:
        query = query.where(Conversation.customer_id == customer_id)
    
    conversations = db.exec(query).all()
    return conversations


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation with all its messages."""
    conversation = db.exec(
        select(Conversation).where(Conversation.id == conversation_id)
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation


@router.put("/{conversation_id}", response_model=ConversationSchema)
def update_conversation(
    conversation_id: UUID,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a conversation (e.g., add audio URL)."""
    db_conversation = db.exec(
        select(Conversation).where(Conversation.id == conversation_id)
    ).first()
    
    if not db_conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    update_data = conversation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_conversation, field, value)
    
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.post("/{conversation_id}/messages", response_model=MessageSchema)
def create_message(
    conversation_id: UUID,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a message to a conversation."""
    # Verify conversation exists
    conversation = db.exec(
        select(Conversation).where(Conversation.id == conversation_id)
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db_message = Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router.get("/{conversation_id}/messages", response_model=List[MessageSchema])
def get_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all messages for a conversation."""
    messages = db.exec(
        select(Message).where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()
    return messages


@router.put("/messages/{message_id}", response_model=MessageSchema)
def update_message(
    message_id: UUID,
    message_update: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a message (e.g., add audio URL)."""
    db_message = db.exec(
        select(Message).where(Message.id == message_id)
    ).first()
    
    if not db_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    update_data = message_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_message, field, value)
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message