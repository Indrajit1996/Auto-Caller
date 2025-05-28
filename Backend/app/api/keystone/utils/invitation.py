from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import config
from app.emails.utils import EmailData, render_email_template, send_email
from app.models.invitation import Invitation
from app.models.user import User
from app.schemas.invitation import InvitationCreate


def render_invitation_email(
    inviter_name: str,
    registration_link: str,
    **kwargs: dict[str, Any],
) -> EmailData:
    """Render invitation email template"""

    context = {
        "project_name": config.PROJECT_NAME,
        "inviter_name": inviter_name,
        "registration_link": registration_link,
        **kwargs,
    }

    html_content = render_email_template(
        template_name="invite_user.html",
        context=context,
    )
    subject = f"{inviter_name} has invited you to join {config.PROJECT_NAME}"

    return EmailData(
        subject=subject,
        html_content=html_content,
    )


async def send_invitation_email(
    *,
    session: AsyncSession,
    invitation: Invitation,
    background_tasks: BackgroundTasks,
) -> None:
    """Send invitation email in background"""
    inviter = await session.get(User, invitation.created_by_user_id)
    if not inviter:
        raise ValueError("Inviter not found")

    token = invitation.token
    registration_link = f"{config.FRONTEND_HOST}/register?token={token}"

    inviter_name = f"{inviter.first_name} {inviter.last_name}".strip()
    if not inviter_name:
        inviter_name = "ASU Decision Theater"

    email = render_invitation_email(
        inviter_name=inviter_name,
        registration_link=registration_link,
    )

    background_tasks.add_task(
        send_email,
        email_to=invitation.email,
        subject=email.subject,
        html_content=email.html_content,
    )

    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)


async def create_invitation(
    *, session: AsyncSession, invitation_in: InvitationCreate, creator_id: UUID
) -> Invitation:
    """Create new invitation"""
    invitation = Invitation.model_validate(
        invitation_in,
        update={"created_by_user_id": creator_id},
    )
    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)
    return invitation
