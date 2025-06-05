from datetime import datetime, timezone
from uuid import UUID

from fastapi import BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.keystone.utils.user import get_user_by_email
from app.core.config import config
from app.core.security import verify_password
from app.emails.utils import EmailData, render_email_template, send_email
from app.models.user import User, UserStatus
from app.utils.decorators import with_async_db_session
from loguru import logger

STATUS_MESSAGES = {
    UserStatus.ACTIVE: {
        "status_code": 200,
        "detail": {
            "status": UserStatus.ACTIVE.name,
            "severity": "success",
            "title": "Account Active",
            "message": "Account is already active. Please log in.",
        },
    },
    UserStatus.PENDING_ADMIN_APPROVAL: {
        "status_code": 400,
        "detail": {
            "status": UserStatus.PENDING_ADMIN_APPROVAL.name,
            "severity": "warning",
            "title": "Pending Admin Approval",
            "message": "Please wait for the admin to approve your account. Contact the admin for more information.",
        },
    },
    UserStatus.PENDING_EMAIL_VERIFICATION: {
        "status_code": 400,
        "detail": {
            "status": UserStatus.PENDING_EMAIL_VERIFICATION.name,
            "severity": "info",
            "title": "Email Verification Required",
            "message": "Please verify your email address to activate your account.",
        },
    },
    UserStatus.DEACTIVATED: {
        "status_code": 400,
        "detail": {
            "status": UserStatus.DEACTIVATED.name,
            "severity": "error",
            "title": "Account Deactivated",
            "message": "Your account has been deactivated. Contact the admin for more information.",
        },
    },
    "INVALID_CREDENTIALS": {
        "status_code": 400,
        "detail": {
            "status": "INVALID_CREDENTIALS",
            "severity": "error",
            "title": "Invalid Credentials",
            "message": "Incorrect email or password",
        },
    },
}


async def authenticate(
    *, session: AsyncSession, email: str, password: str
) -> User | None:
    """Authenticate a user asynchronously"""
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def render_verification_email(verification_link, username, **kwargs) -> EmailData:
    context = {
        "project_name": config.PROJECT_NAME,
        "verification_link": verification_link,
        "username": username,
        **kwargs,
    }

    html_content = render_email_template(
        template_name="verify_email.html",
        context=context,
    )
    subject = f"Verify your email address for {config.PROJECT_NAME}"

    return EmailData(
        subject=subject,
        html_content=html_content,
    )


async def send_verification_email(
    *,
    user: User,
    background_tasks: BackgroundTasks,
) -> None:
    """Send verification email asynchronously"""
    logger.info(f"Sending verification email to {user.email}")
    token = user.email_verification_token
    verification_link = f"{config.FRONTEND_HOST}/verify-email?token={token}"

    email_data = render_verification_email(
        verification_link=verification_link,
        username=user.first_name,
    )

    background_tasks.add_task(
        send_email,
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )


@with_async_db_session
async def update_last_login(*, session: AsyncSession, user_id: UUID) -> None:
    """Update user's last_login timestamp"""
    db_user = await session.get(User, user_id)
    if db_user:
        db_user.last_login = datetime.now(timezone.utc)
        session.add(db_user)
        await session.commit()
