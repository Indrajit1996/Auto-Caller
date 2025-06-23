from uuid import UUID
from pydantic import BaseModel
from app.schemas.common import BaseRead, BaseCreate, BaseUpdate

class ConversationCreate(BaseCreate):
    topic: str

class ConversationRead(BaseRead):
    id: int
    topic: str
    created_by: UUID

class ConversationUpdate(BaseUpdate):
    topic: str | None = None
