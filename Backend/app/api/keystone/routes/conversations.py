from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import AsyncSessionDep, Authenticated, CurrentUser
from app.models.conversation import Conversation
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
)

router = APIRouter(prefix="/conversations", tags=["conversations"], dependencies=[Authenticated])

@router.get("/", response_model=list[ConversationRead])
async def read_conversations(
    session: AsyncSessionDep, offset: int = 0, limit: int = 100
):
    statement = select(Conversation).offset(offset).limit(limit)
    results = await session.exec(statement)
    return results.all()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ConversationRead)
async def create_conversation(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    conversation_in: ConversationCreate,
):
    conversation = Conversation.model_validate(conversation_in, update={"created_by": current_user.id})
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation

@router.put("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    session: AsyncSessionDep,
    conversation_id: int,
    conversation_in: ConversationUpdate,
):
    conversation = await session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation.sqlmodel_update(conversation_in, exclude_unset=True)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation
