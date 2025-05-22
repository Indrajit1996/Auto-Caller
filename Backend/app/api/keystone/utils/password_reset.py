from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import config
from app.emails.utils import EmailData, render_email_template
from app.models.password_reset import PasswordReset


def generate_reset_password_email(email_to: str, email: str, token: UUID) -> EmailData:
    project_name = config.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{config.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": config.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": config.PASSWORD_RESET_TOKEN_EXPIRY_IN_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


async def get_password_reset_record_by_user_id(
    *, session: AsyncSession, user_id: str
) -> PasswordReset | None:
    """Get password reset record by user ID asynchronously"""
    result = await session.exec(
        select(PasswordReset).where(
            PasswordReset.user_id == user_id,
            PasswordReset.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.first()


async def get_password_reset_record_by_token(
    *, session: AsyncSession, token: str
) -> PasswordReset | None:
    """Get password reset record by token asynchronously"""
    result = await session.exec(
        select(PasswordReset)
        .options(
            joinedload(PasswordReset.user),
        )
        .where(
            PasswordReset.token == token,
            PasswordReset.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.first()
