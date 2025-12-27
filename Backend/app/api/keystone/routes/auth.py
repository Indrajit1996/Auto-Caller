from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlmodel import select

from app.api.deps import (
    AsyncSessionDep,
    CurrentUser,
)
from app.api.keystone.utils import user as user_utils
from app.api.keystone.utils.auth import (
    STATUS_MESSAGES,
    authenticate,
    send_verification_email,
    update_last_login,
)
from app.api.keystone.utils.password_reset import (
    generate_reset_password_email,
    get_password_reset_record_by_token,
    get_password_reset_record_by_user_id,
)
from app.api.keystone.utils.user import (
    get_user_by_email,
    get_user_by_email_verification_token,
)
from app.core import security
from app.core.config import USER_APPROVAL_FLOW, config
from app.core.security import get_password_hash, verify_password
from app.emails.utils import send_email
from app.models import Invitation, User, UserGroup
from app.models.invitation import InvitationRegistration, InvitationType
from app.models.notification import NotificationType
from app.models.password_reset import PasswordReset
from app.models.user import UserStatus
from app.schemas.auth import UserRegisterResponse
from app.schemas.common import Message, NewPassword, Token
from app.schemas.user import (
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UserUpdateMe,
)
from app.utils.notification import (
    create_notification,
    send_notification_to_admins,
)

router = APIRouter(
    tags=["login"],
)


@router.post("/register")
async def register_user(
    session: AsyncSessionDep, user_in: UserRegister, background_tasks: BackgroundTasks
) -> UserRegisterResponse:
    user = await user_utils.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail={
                "user_status": user.status.name,
                "message": STATUS_MESSAGES[user.status]["detail"]["message"],
            },
        )
    invitation_id = None
    if user_in.invitation_token:
        query = select(Invitation).where(Invitation.token == user_in.invitation_token)
        result = await session.exec(query)
        invitation = result.first()
        if not invitation:
            raise HTTPException(status_code=400, detail="Invalid invitation token")
        if not invitation.active:
            raise HTTPException(status_code=400, detail="Invitation token expired")
        invitation_id = invitation.id
        if invitation.type == InvitationType.EMAIL:
            user_in.email = invitation.email
            invitation.expires_at = datetime.now(timezone.utc)
        session.add(invitation)
        await session.commit()

    user_create = UserCreate.model_validate(user_in)

    if invitation_id:
        user_create.status = (
            UserStatus.ACTIVE
            if invitation.type == InvitationType.EMAIL
            else UserStatus.PENDING_EMAIL_VERIFICATION
        )
    else:
        if config.DEFAULT_USER_APPROVAL_FLOW:
            if config.DEFAULT_USER_APPROVAL_FLOW == USER_APPROVAL_FLOW.ADMIN_APPROVAL:
                user_create.status = UserStatus.PENDING_ADMIN_APPROVAL
            elif (
                config.DEFAULT_USER_APPROVAL_FLOW
                == USER_APPROVAL_FLOW.EMAIL_VERIFICATION
            ):
                user_create.status = UserStatus.PENDING_EMAIL_VERIFICATION

    try:
        user = await user_utils.create_user(session=session, user_create=user_create)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")

    if user and invitation_id:
        invitation_registration = InvitationRegistration(
            user_id=user.id, invitation_id=invitation_id
        )
        session.add(invitation_registration)
        await session.commit()

    if user and user.status == UserStatus.PENDING_EMAIL_VERIFICATION:
        logger.info(f"Email Invitation pending")
        await send_verification_email(user=user, background_tasks=background_tasks)

    background_tasks.add_task(
        create_notification,
        session=session,
        user_id=user.id,
        message=f"Welcome to {config.PROJECT_NAME}, {user.full_name}!",
        type=NotificationType.INFO,
        meta_data={"event": "user_welcome", "email": user.email},
    )

    background_tasks.add_task(
        send_notification_to_admins,
        session=session,
        message=f"New user registered: {user.full_name} ({user.email})",
        type=NotificationType.INFO,
        meta_data={
            "event": "new_registration",
            "user_id": str(user.id),
            "email": user.email,
            "status": user.status.name,
        },
    )

    if user.status == UserStatus.ACTIVE:
        return UserRegisterResponse(
            message="Account created successfully. Please log in.",
            status=user.status.name,
        )

    return UserRegisterResponse(
        message=STATUS_MESSAGES[user.status]["detail"]["message"],
        status=user.status.name,
    )


@router.post("/login/access-token")
async def login_access_token(
    session: AsyncSessionDep,
    background_tasks: BackgroundTasks,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """OAuth2 compatible token login, get an access token for future requests"""
    user = await authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=STATUS_MESSAGES["INVALID_CREDENTIALS"]["status_code"],
            detail=STATUS_MESSAGES["INVALID_CREDENTIALS"]["detail"],
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=STATUS_MESSAGES[user.status]["status_code"],
            detail=STATUS_MESSAGES[user.status]["detail"],
        )

    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    logger.info(f"User {user.id} logged in")

    background_tasks.add_task(update_last_login, user_id=user.id)

    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token")
async def test_token(current_user: CurrentUser) -> UserPublic:
    """
    Test access token
    """
    return UserPublic.model_validate(current_user)


@router.patch("/me")
async def update_user_me(
    *, session: AsyncSessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> UserPublic:
    """
    Update own user.
    """
    db_user = await session.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user_in.model_dump(exclude_unset=True)
    db_user.sqlmodel_update(user_data)

    await session.commit()
    await session.refresh(db_user)

    return UserPublic.model_validate(db_user)


@router.patch("/me/password")
async def update_password_me(
    *, session: AsyncSessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Message:
    """
    Update own password.
    """
    # Get a fresh copy of the user that belongs to this session
    db_user = await session.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(body.current_password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )

    hashed_password = get_password_hash(body.new_password)
    db_user.hashed_password = hashed_password

    await session.commit()
    await session.refresh(db_user)

    logger.info(f"User {db_user.email} updated their password")
    return Message(message="Password updated successfully")


@router.get("/me")
async def read_user_me(current_user: CurrentUser) -> UserPublic:
    """
    Get current user.
    """
    return UserPublic.model_validate(current_user)


@router.patch("/me/deactivate", response_model=Message)
async def deactivate_self(
    session: AsyncSessionDep, current_user: CurrentUser
) -> Message:
    """Deactivate current user account"""

    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Superusers cannot deactivate their own account"
        )

    # Get a fresh copy of the user that belongs to this session
    db_user = await session.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.status == UserStatus.DEACTIVATED:
        raise HTTPException(status_code=400, detail="User already deactivated")

    # Deactivate the user
    db_user.status = UserStatus.DEACTIVATED

    # Remove from all groups
    user_groups = await session.scalars(
        select(UserGroup).where(UserGroup.user_id == db_user.id)
    )
    for user_group in user_groups:
        await session.delete(user_group)
    await session.commit()
    await session.refresh(db_user)

    logger.info(f"User {db_user.id} deactivated their account")

    # Send notification to all admin users about the account deactivation
    await send_notification_to_admins(
        session=session,
        message=f"User account deactivated: {db_user.full_name} ({db_user.email})",
        type=NotificationType.WARNING,
        meta_data={
            "event": "account_deactivation",
            "user_id": str(db_user.id),
            "email": db_user.email,
        },
    )

    return Message(message="Account successfully deactivated")


@router.post("/password-recovery/{email}")
async def recover_password(
    email: str, session: AsyncSessionDep, background_tasks: BackgroundTasks
) -> Message:
    """
    Password Recovery
    """
    user = await get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )

    password_reset_record = await get_password_reset_record_by_user_id(
        session=session, user_id=user.id
    )

    # Create new token if no active token exists for the user
    if not password_reset_record:
        password_reset_record = PasswordReset(user_id=user.id)
        session.add(password_reset_record)
        await session.commit()
        await session.refresh(password_reset_record)

    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_record.token
    )

    session.add(password_reset_record)
    await session.commit()

    logger.info(f"Sending password recovery email to {user.email}")

    background_tasks.add_task(
        send_email,
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )

    return Message(message="Password recovery email sent")


@router.post("/reset-password")
async def reset_password(session: AsyncSessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """

    password_reset_record = await get_password_reset_record_by_token(
        session=session, token=body.token
    )
    logger.info('password_reset_record', password_reset_record)

    if not password_reset_record:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await get_user_by_email(
        session=session, email=password_reset_record.user.email
    )
    logger.info('user info', user)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Check if new password matches current password
    if verify_password(body.new_password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as current password",
        )

    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)

    # Invalidate the reset record
    password_reset_record.expires_at = datetime.now(timezone.utc)
    session.add(password_reset_record)
    await session.commit()
    logger.info(f"Password updated for user {user.email}")

    return Message(message="Password updated successfully")


@router.get("/verify-email/{token}")
async def verify_email(session: AsyncSessionDep, token: str) -> Message:
    """verify email

    Returns:
        Message: success message or failure
    """
    if not token:
        raise HTTPException(status_code=400, detail="No token provided")

    try:
        user = await get_user_by_email_verification_token(token=token, session=session)
        logger.info('inside verify-email', user)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Invalid verification token",
        )

    if not user:
        raise HTTPException(status_code=404, detail="Invalid verification token")

    print('user information', user)
    if user.status == UserStatus.PENDING_EMAIL_VERIFICATION:
        user.status = UserStatus.ACTIVE
        user.email_verification_token = None
        session.add(user)
        await session.commit()
        return Message(message="Email verified successfully")

    elif user.is_active:
        user.email_verification_token = None
        session.add(user)
        await session.commit()
        raise HTTPException(
            status_code=400,
            detail="Email already verified",
        )

    return Message(message="There was an error verifying the email")


@router.post("/verify-email/resend")
async def resend_verification_email(
    session: AsyncSessionDep,
    background_tasks: BackgroundTasks,
    email: str = Body(..., embed=True),
) -> Message:
    user = await get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.status == UserStatus.PENDING_EMAIL_VERIFICATION:
        await send_verification_email(user=user, background_tasks=background_tasks)
        return Message(message="Verification email sent successfully")

    if user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Email already verified",
        )

    return Message(message="There was an error sending the email")
