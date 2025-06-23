from sqlmodel import Field, Relationship, SQLModel
from app.models.mixins.timestamp_mixin import TimestampMixin
from app.models.user import User

class Conversation(SQLModel, TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    topic: str
    created_by: uuid.UUID = Field(foreign_key="user.id", ondelete="SET NULL")

    owner: User | None = Relationship(back_populates="conversations")
