from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class UserSettingsBase(SQLModel):
    receive_email_notifications: bool


class UserSettingsCreate(UserSettingsBase):
    user_id: UUID


class UserSettingsUpdate(UserSettingsBase):
    pass


class UserSettingsRead(UserSettingsBase):
    user_id: UUID
    updated_at: datetime
