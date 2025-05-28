from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.invitation import Invitation, InvitationRegistration
from app.models.user import User, UserStatus
from app.utils.decorators import with_async_db_session


@with_async_db_session
async def expire_users(session: AsyncSession) -> None:
    """
    Expire users that were invited and are past their status expiration date.
    Updates User status to DEACTIVATED if Invitation.user_expiry_date is in the past.
    """

    now = datetime.now(timezone.utc)
    two_days_ago = now - timedelta(days=2)

    try:
        invitation_query = select(Invitation.id).where(
            Invitation.user_expiry_date.is_not(None),
            Invitation.user_expiry_date < now,
            Invitation.user_expiry_date > two_days_ago,
        )
        result = await session.exec(invitation_query)
        expired_invitation_ids = result.all()

        # If no expired invitations, early return
        if not expired_invitation_ids:
            logger.info("No expired invitations found")
            return

        # Find users to expire
        user_query = (
            select(User)
            .join(InvitationRegistration)
            .where(
                InvitationRegistration.invitation_id.in_(expired_invitation_ids),
                User.status == UserStatus.ACTIVE,
            )
        )
        result = await session.exec(user_query)
        users_to_be_expired = result.all()

        # Update user statuses
        for user in users_to_be_expired:
            user.status = UserStatus.DEACTIVATED
            session.add(user)
            logger.info(f"Expired user {user.id}")

        # Commit the transaction
        await session.commit()

        logger.info(f"Expired {len(users_to_be_expired)} users")

    except Exception as e:
        await session.rollback()
        logger.error(f"Error expiring users: {e}")
        raise
