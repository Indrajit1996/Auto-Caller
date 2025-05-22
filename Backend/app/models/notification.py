import uuid
from enum import Enum

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from app.models.mixins.timestamp_mixin import TimestampMixin
from app.models.user import User


class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    WEB = "web"
    SMS = "sms"


class Notification(SQLModel, TimestampMixin, table=True):
    id: int = Field(default=None, primary_key=True)
    type: NotificationType = Field(default=NotificationType.INFO)
    channel: NotificationChannel = Field(default=NotificationChannel.WEB)
    message: str
    meta_data: dict = Field(default_factory=dict, sa_column=Column(JSON))
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    is_read: bool = False

    user: User = Relationship(back_populates="notifications")

    @classmethod
    def create(
        cls,
        user_ids: uuid.UUID | list[uuid.UUID],
        message: str,
        type: NotificationType = NotificationType.INFO,
        channel: NotificationChannel = NotificationChannel.WEB,
        meta_data: dict | None = None,
    ) -> list["Notification"]:
        """
        Create notification(s) for one or multiple users.

        Args:
            user_ids: Single user_id or list of user_ids
            message: Notification message
            type: Notification type (default: INFO)
            channel: Notification channel (default: WEB)
            meta_data: Additional metadata for the notification

        Returns:
            List of created Notification objects
        """
        if meta_data is None:
            meta_data = {}

        # Convert single user_id to list
        if not isinstance(user_ids, list):
            user_ids = [user_ids]

        notifications = []
        for user_id in user_ids:
            notification = cls(
                user_id=user_id,
                message=message,
                type=type,
                channel=channel,
                meta_data=meta_data,
            )
            notifications.append(notification)

        return notifications
