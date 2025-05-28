import uuid
from datetime import datetime

from sqlmodel import SQLModel

from app.models.transaction import Action, Model


class TransactionBase(SQLModel):
    user_id: uuid.UUID
    model: Model
    action: Action


class TransactionMetaData(SQLModel):
    old_data: str | dict | None = None
    new_data: str | dict | None = None


class TransactionCreate(TransactionBase):
    record_id: str | None = None
    description: str | None = None
    meta_data: TransactionMetaData


class TransactionRead(TransactionBase):
    id: int
    record_id: str | None = None
    description: str | None = None
    meta_data: dict = {}
    created_at: datetime


class TransactionsRead(SQLModel):
    data: list[TransactionRead]
    count: int
