import tempfile
import uuid

import aiofiles
import aiofiles.os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from sqlmodel import func, or_, select

from app.api.deps import (
    AsyncSessionDep,
    Authenticated,
    CurrentUser,
    IsSuperUser,
)
from app.api.keystone.utils import user as user_utils
from app.core.config import config
from app.emails.utils import generate_new_account_email, send_email
from app.models import Group, User, UserGroup
from app.models.invitation import Invitation, InvitationRegistration
from app.models.transaction import Action, Model
from app.schemas.transaction import TransactionMetaData
from app.schemas.user import (
    ReadUsersRequestBody,
    UserCreate,
    UserDetail,
    UserGroupRead,
    UserInvitationRead,
    UserPublic,
    UserRegisterAdmin,
    UsersDataTable,
    UserStatus,
    UserStatusCount,
    UserStatusResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.utils import transaction as transaction_utils

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Authenticated, IsSuperUser],
)


@router.post("/datatable")
async def read_users_advanced(
    session: AsyncSessionDep, body: ReadUsersRequestBody
) -> UsersDataTable:
    query = select(User)

    if body.search:
        search_terms = body.search.split()
        for term in search_terms:
            query = query.where(
                or_(
                    User.first_name.ilike(f"%{term}%"),
                    User.last_name.ilike(f"%{term}%"),
                    User.email.ilike(f"%{term}%"),
                )
            )

    # Apply nested filters
    if body.filters.status and body.filters.status != "all":
        query = query.where(User.status == body.filters.status)
    if body.filters.role and body.filters.role != "all":
        query = query.where(User.is_superuser == (body.filters.role == "superuser"))
    if body.filters.group and body.filters.group != "all":
        query = query.where(
            User.groups.any(UserGroup.group_id == int(body.filters.group))
        )
    if body.filters.exclude_group and body.filters.exclude_group != "all":
        query = query.where(
            ~User.groups.any(UserGroup.group_id == int(body.filters.exclude_group))
        )
    if body.filters.created_at:
        if body.filters.created_at[0]:
            query = query.where(User.created_at >= body.filters.created_at[0])
        if body.filters.created_at[1]:
            query = query.where(User.created_at <= body.filters.created_at[1])

    count_query = select(func.count()).select_from(query.subquery())
    count = await session.scalar(count_query)

    order_column = getattr(User, body.order_by)
    if body.order == "desc":
        order_column = order_column.desc()
    query = query.order_by(order_column)
    query = query.offset(body.offset).limit(body.limit)

    users = await session.scalars(query)

    return UsersDataTable.model_validate(
        {
            "data": users,
            "count": count,
        }
    )


@router.post("/")
async def create_user(
    *,
    session: AsyncSessionDep,
    user_in: UserRegisterAdmin,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
) -> UserPublic:
    """
    Create new user from Admin panel.
    """
    user = await user_utils.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail={
                "user_status": user.status.name,
                "message": "User with this email already exists",
            },
        )

    user_create = UserCreate.model_validate(
        user_in, update={"status": UserStatus.ACTIVE}
    )

    try:
        user = await user_utils.create_user(
            session=session,
            user_create=user_create,
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")

    if config.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        background_tasks.add_task(
            send_email,
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )

    background_tasks.add_task(
        transaction_utils.log_transaction,
        user_id=current_user.id,
        model=Model.USER,
        record_id=str(user.id),
        action=Action.CREATE,
        description="User created",
        meta_data=TransactionMetaData(new_data={"user_id": str(user.id)}),
    )  # type: ignore

    return UserPublic.model_validate(user)


@router.get("/status-counts")
async def get_user_status_breakdown(
    session: AsyncSessionDep,
) -> UserStatusCount:
    """
    Get breakdown of users by status.
    """

    status_counts = select(User.status, func.count(User.id)).group_by(User.status)
    results = await session.exec(status_counts)
    status_results = results.all()

    return UserStatusCount(
        **{status.value: count for status, count in status_results},
        total=sum(count for _, count in status_results),
    )


@router.get("/export")
async def export_user_data(session: AsyncSessionDep) -> FileResponse:
    """
    Export user data to CSV.
    """
    try:
        users = await session.scalars(
            select(User)
            .where(User.status == UserStatus.ACTIVE)
            .order_by(User.created_at.desc())
            .limit(1000)
        )

        if not users:
            raise HTTPException(status_code=404, detail="No users found")

        # Create a temporary file
        tmp_path = tempfile.mktemp(suffix=".csv")

        # Use aiofiles to write asynchronously
        async with aiofiles.open(tmp_path, mode="w") as tmp:
            fieldnames = ["id", "first_name", "last_name", "email", "created_at"]

            await tmp.write(",".join(fieldnames) + "\n")

            for user in users:
                row = {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "created_at": user.created_at.isoformat(),
                }
                # Escape commas and quotes in field values
                csv_line = ",".join(f'"{str(row[field])}"' for field in fieldnames)
                await tmp.write(csv_line + "\n")

        return FileResponse(path=tmp_path, filename="users.csv", media_type="text/csv")
    except Exception:
        logger.warning("Error exporting data")
        raise HTTPException(status_code=500, detail="Error exporting data")


@router.get("/{user_id}")
async def read_user_by_id(user_id: uuid.UUID, session: AsyncSessionDep) -> UserDetail:
    """
    Get a specific user by id.
    """
    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    groups_query = (
        select(Group)
        .join(UserGroup)
        .where(UserGroup.user_id == user.id, Group.is_active == True)
    )
    groups = await session.exec(groups_query)

    invitation_query = (
        select(Invitation)
        .join(InvitationRegistration)
        .where(InvitationRegistration.user_id == user.id)
        .limit(1)
    )
    invitation = await session.exec(invitation_query)
    invitation = invitation.first()

    return UserDetail(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        status=user.status,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        groups=[UserGroupRead.model_validate(group) for group in groups],
        invitation=UserInvitationRead.model_validate(invitation)
        if invitation
        else None,
        is_active=user.is_active,
        updated_at=user.updated_at,
        last_login=user.last_login,
    )


@router.patch("/{user_id}")
async def update_user(
    *,
    session: AsyncSessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> UserPublic:
    """
    Update a user.
    """

    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )

    if user_id == current_user.id and current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="Superusers cannot update their own account"
        )

    if user_in.email:
        existing_user = await user_utils.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    old_user = user_utils.get_user_dict(user=db_user)
    db_user = await user_utils.update_user(
        session=session, db_user=db_user, user_in=user_in
    )
    new_user = user_utils.get_user_dict(user=db_user)

    background_tasks.add_task(
        transaction_utils.log_transaction,
        user_id=current_user.id,
        record_id=str(db_user.id),
        model=Model.USER,
        action=Action.UPDATE,
        description="User updated",
        meta_data=TransactionMetaData(old_data=old_user, new_data=new_user),
    )
    return UserPublic.model_validate(db_user)


@router.patch("/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    status_update: UserStatusUpdate,
    session: AsyncSessionDep,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
) -> UserStatusResponse:
    """Update user status to active or deactivated (superuser only)"""
    # Get user
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-status change
    if user.id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot change your own status")

    old_status = user.status
    user.status = status_update.status

    session.add(user)
    await session.commit()
    await session.refresh(user)

    background_tasks.add_task(
        transaction_utils.log_transaction,
        user_id=current_user.id,
        record_id=str(user.id),
        model=Model.USER,
        action=Action.UPDATE,
        description="User status updated",
        meta_data=TransactionMetaData(
            old_data={"status": old_status.name}, new_data={"status": user.status.name}
        ),
    )

    return UserStatusResponse.model_validate(user)
