from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import AsyncSessionDep, Authenticated, CurrentUser
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationList,
    NotificationPublic,
)

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    dependencies=[Authenticated],
)


@router.get("/")
async def get_notifications(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    offset: int = 0,
    limit: int = 100,
) -> NotificationList:
    """Get all unread notifications"""
    statement = select(Notification).where(
        Notification.user_id == current_user.id, Notification.is_read == False
    )
    count_statement = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
    )
    count = await session.scalar(count_statement)

    notifications = await session.scalars(statement.offset(offset).limit(limit))

    return NotificationList.model_validate({"data": notifications, "count": count})


@router.get("/{notification_id}")
async def get_notification(
    session: AsyncSessionDep,
    notification_id: int,
    current_user: CurrentUser,
) -> NotificationPublic:
    """Get a single notification"""
    result = await session.exec(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return NotificationPublic.model_validate(notification)


@router.patch("/{notification_id}/read")
async def mark_notification_as_read(
    session: AsyncSessionDep,
    notification_id: int,
    current_user: CurrentUser,
) -> NotificationPublic:
    """Mark a notification as read"""
    result = await session.exec(
        select(Notification).where(Notification.id == notification_id)
    )
    db_notification = result.first()

    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if db_notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_notification.is_read = True
    session.add(db_notification)
    await session.commit()
    await session.refresh(db_notification)
    return NotificationPublic.model_validate(db_notification)


@router.patch("/read-all")
async def mark_all_notifications_as_read(
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> dict:
    """Mark all of the current user's notifications as read"""
    result = await session.exec(
        select(Notification).where(
            Notification.user_id == current_user.id, Notification.is_read == False
        )
    )
    notifications = result.all()

    for notification in notifications:
        notification.is_read = True
        session.add(notification)

    await session.commit()
    return {"success": True, "count": len(notifications)}
