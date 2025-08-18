from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import AsyncSessionDep, CurrentUser
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ConversationList,
    ConversationPublic,
    MessageList,
    MessagePublic,
)

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get("/")
async def get_conversations(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    offset: int = 0,
    limit: int = 100,
) -> ConversationList:   
    """Get all conversations for the logged-in user"""
    
    print('Fetching', current_user)
    statement = select(Conversation).where(
        Conversation.agent_id == current_user.id
    )
    count_statement = (
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.agent_id == current_user.id)
    )
    count = await session.scalar(count_statement)

    conversations = await session.scalars(statement.offset(offset).limit(limit))

    return ConversationList.model_validate({"data": conversations, "count": count})


# @router.get("/{customer_id}")
# async def get_messages(
#     session: AsyncSessionDep,
#     customer_id: UUID,
#     current_user: CurrentUser,
#     offset: int = 0,
#     limit: int = 100,
# ) -> MessageList:
#     """Get all messages for a specific conversation by customer_id"""
#     # Find conversation by customer_id
#     conversation_result = await session.exec(
#         select(Conversation).where(
#             Conversation.customer_id == customer_id,
#             Conversation.agent_id == current_user.id
#         )
#     )
#     conversation = conversation_result.first()

#     if not conversation:
#         raise HTTPException(status_code=404, detail="Conversation not found")
#     if conversation.agent_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not enough permissions")

#     # Get messages for the conversation
#     statement = select(Message).where(
#         Message.conversation_id == conversation.id
#     ).order_by(Message.created_at)
    
#     count_statement = (
#         select(func.count())
#         .select_from(Message)
#         .where(Message.conversation_id == conversation.id)
#     )
#     count = await session.scalar(count_statement)

#     messages = await session.scalars(statement.offset(offset).limit(limit))

#     return MessageList.model_validate({"data": messages, "count": count})