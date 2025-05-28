from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel

from app.models.notification import NotificationChannel, NotificationType


class NotificationBase(SQLModel):
    message: str
    type: NotificationType = NotificationType.INFO
    channel: NotificationChannel = NotificationChannel.WEB
    meta_data: dict = {}


class NotificationCreate(NotificationBase):
    user_id: UUID


class NotificationUpdate(SQLModel):
    message: str | None = None
    type: NotificationType | None = None
    channel: NotificationChannel | None = None
    meta_data: dict | None = None
    is_read: bool | None = None


class NotificationPublic(NotificationBase):
    id: int
    user_id: UUID
    is_read: bool
    created_at: datetime


class NotificationList(SQLModel):
    data: list[NotificationPublic]
    count: int
