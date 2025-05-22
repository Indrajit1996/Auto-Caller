import uuid

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.notification import Notification, NotificationChannel, NotificationType
from app.models.user import User
from app.utils.decorators import with_async_db_session


@with_async_db_session
async def create_notification(
    *,
    session: AsyncSession,
    user_id: uuid.UUID | list[uuid.UUID],
    message: str,
    type: NotificationType = NotificationType.INFO,
    channel: NotificationChannel = NotificationChannel.WEB,
    meta_data: dict | None = None,
) -> Notification | list[Notification]:
    """
    Create notification(s) for one or more users

    Args:
        session: Database session
        user_id: Single user_id or list of user_ids
        message: Notification message
        type: Notification type (default: INFO)
        channel: Notification channel (default: WEB)
        meta_data: Additional metadata for the notification

    Returns:
        Single Notification object or list of created Notification objects,
        depending on the input type of user_id
    """
    try:
        # Handle single user_id case
        if isinstance(user_id, uuid.UUID):
            try:
                notification = Notification(
                    user_id=user_id,
                    message=message,
                    type=type,
                    channel=channel,
                    meta_data=meta_data or {},
                )
                session.add(notification)
                await session.commit()
                await session.refresh(notification)
                return notification
            except Exception as e:
                logger.error(
                    f"Failed to create notification for user {user_id}: {str(e)}"
                )
                await session.rollback()
                raise

        # Handle multiple user_ids case
        else:
            try:
                # Create notification objects
                notifications = Notification.create(
                    user_ids=user_id,
                    message=message,
                    type=type,
                    channel=channel,
                    meta_data=meta_data,
                )

                # Add to session and commit
                session.add_all(notifications)
                await session.commit()

                # Refresh to get the generated IDs
                notification_ids = [
                    notif.id for notif in notifications if notif.id is not None
                ]
                if notification_ids:
                    refreshed = await session.exec(
                        select(Notification).where(
                            Notification.id.in_(notification_ids)
                        )
                    )
                    notifications = refreshed.all()

                return notifications
            except Exception as e:
                logger.error(
                    f"Failed to create notifications for multiple users: {str(e)}"
                )
                await session.rollback()
                raise
    except Exception as e:
        logger.error(f"Unexpected error in create_notification: {str(e)}")
        raise


@with_async_db_session
async def send_notification_to_admins(
    *,
    session: AsyncSession,
    message: str,
    type: NotificationType = NotificationType.INFO,
    channel: NotificationChannel = NotificationChannel.WEB,
    meta_data: dict | None = None,
) -> list[Notification]:
    """
    Send a notification to all admin users (is_superuser=True)

    Args:
        session: Database session
        message: Notification message
        type: Notification type (default: INFO)
        channel: Notification channel (default: WEB)
        meta_data: Additional metadata for the notification

    Returns:
        List of created Notification objects
    """
    try:
        # Query all admin users
        result = await session.exec(select(User).where(User.is_superuser == True))
        admin_users = result.all()

        if not admin_users:
            logger.warning("No admin users found to send notification to")
            return []

        # Get all admin user IDs
        admin_user_ids = [user.id for user in admin_users]

        # Use existing function to create notifications for all admins
        notifications = await create_notification(
            session=session,
            user_id=admin_user_ids,
            message=message,
            type=type,
            channel=channel,
            meta_data=meta_data,
        )

        logger.info(f"Sent notification to {len(admin_user_ids)} admin users")
        return notifications

    except Exception as e:
        logger.error(f"Failed to send notifications to admin users: {str(e)}")
        raise
