import uuid
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import and_, func, select

from app.api.deps import (
    AsyncSessionDep,
    Authenticated,
    CurrentUser,
    IsSuperUser,
)
from app.api.keystone.utils.invitation import (
    create_invitation,
    send_invitation_email,
)
from app.models.invitation import Invitation, InvitationRegistration, InvitationType
from app.models.transaction import Action, Model
from app.models.user import User
from app.schemas.common import Message
from app.schemas.invitation import (
    InvitationCreate,
    InvitationCreateInput,
    InvitationCreateResponse,
    InvitationRead,
    InvitationsRead,
    InvitationTokenRead,
    InvitationTypeCount,
    ReadInvitationsRequestBody,
)
from app.schemas.transaction import TransactionCreate, TransactionMetaData
from app.utils import transaction as transaction_utils

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post(
    "/datatable",
    dependencies=[Authenticated, IsSuperUser],
)
async def read_invitations_advanced(
    session: AsyncSessionDep, body: ReadInvitationsRequestBody
) -> InvitationsRead:
    """
    Retrieve invitations with filters.
    Parameters:
    - offset: pagination offset
    - limit: pagination limit
    - search: search term for email
    - filters: nested filters for type and status
    - order_by: field to sort by
    - order: sort direction (asc/desc)
    """
    query = (
        select(Invitation)
        .options(
            selectinload(Invitation.registered_users),
            selectinload(Invitation.created_by_user),
        )
        .distinct()
    )

    # Apply search
    if body.search:
        query = query.where(Invitation.email.ilike(f"%{body.search}%"))

    # Apply nested filters
    if body.filters.type and body.filters.type != "all":
        query = query.where(Invitation.type == body.filters.type)

    if body.filters.status and body.filters.status != "all":
        if body.filters.status == "registered":
            # Join with User table and filter for invitations with users
            query = query.join(
                InvitationRegistration,
                Invitation.id == InvitationRegistration.invitation_id,
            )
        elif body.filters.status == "active":
            query = query.where(Invitation.expires_at > datetime.now(timezone.utc))
        elif body.filters.status == "inactive":
            query = (
                query.outerjoin(
                    InvitationRegistration,
                    Invitation.id == InvitationRegistration.invitation_id,
                )
                .where(Invitation.expires_at <= datetime.now(timezone.utc))
                .where(InvitationRegistration.invitation_id.is_(None))
            )
    if body.filters.created_by_user_id:
        query = query.where(
            Invitation.created_by_user_id == body.filters.created_by_user_id
        )
    if body.filters.created_at:
        if body.filters.created_at[0]:
            query = query.where(Invitation.created_at >= body.filters.created_at[0])
        if body.filters.created_at[1]:
            query = query.where(Invitation.created_at <= body.filters.created_at[1])

    # Get total count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    count = await session.scalar(count_query)

    # Apply ordering and pagination
    order_column = getattr(Invitation, body.order_by)
    if body.order == "desc":
        order_column = order_column.desc()
    query = query.order_by(order_column)
    query = query.offset(body.offset).limit(body.limit)

    result = await session.exec(query)
    invitations = result.unique()

    return InvitationsRead.model_validate(
        {
            "data": invitations,
            "count": count,
        }
    )


@router.post(
    "/",
    dependencies=[Authenticated, IsSuperUser],
    status_code=status.HTTP_201_CREATED,
)
async def create_new_invitation(
    *,
    invitation_in: InvitationCreateInput,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> InvitationCreateResponse:
    """Create new invitation"""

    if invitation_in.type == InvitationType.EMAIL and invitation_in.emails:
        invitation_in.emails = list(set(invitation_in.emails))
        # Bulk check existing emails in one query
        result = await session.exec(
            select(User.email).where(User.email.in_(invitation_in.emails)).distinct()
        )
        existing_users = result.all()

        result = await session.exec(
            select(Invitation.email)
            .where(
                and_(
                    Invitation.email.in_(invitation_in.emails),
                    Invitation.expires_at > datetime.now(timezone.utc),
                )
            )
            .distinct()
        )
        existing_invitations = result.all()

        existing_emails = set(existing_users).union(set(existing_invitations))

        new_emails = [
            InvitationCreate(
                email=email,
                type=InvitationType.EMAIL,
                created_by_user_id=current_user.id,
                user_expiry_date=invitation_in.user_expiry_date,
            )
            for email in invitation_in.emails
            if email not in existing_emails
        ]

        created_invitations = []

        if new_emails:
            # Bulk create invitations
            invitations = [
                Invitation.model_validate(
                    invitation_in,
                    update={
                        "created_by_user_id": current_user.id,
                    },
                )
                for invitation_in in new_emails
            ]
            session.add_all(invitations)
            await session.commit()

            transaction_logs = [
                TransactionCreate(
                    model=Model.INVITATION,
                    action=Action.CREATE,
                    user_id=current_user.id,
                    record_id=str(invitation.id),
                    description="Email invitation created",
                    meta_data=TransactionMetaData(new_data={"email": invitation.email}),
                )
                for invitation in invitations
            ]

            background_tasks.add_task(
                transaction_utils.log_multiple_transactions,
                transactions_in=transaction_logs,
            )

            # Send emails in background
            for invitation in invitations:
                await send_invitation_email(
                    session=session,
                    invitation=invitation,
                    background_tasks=background_tasks,
                )

            created_invitations = invitations

        return InvitationCreateResponse(
            created_invitations=created_invitations,
            existing_emails=list(existing_emails),
        )

    elif invitation_in.type == InvitationType.LINK:
        invitation = await create_invitation(
            session=session,
            invitation_in=InvitationCreate(
                type=InvitationType.LINK,
                created_by_user_id=current_user.id,
                user_expiry_date=invitation_in.user_expiry_date,
            ),
            creator_id=current_user.id,
        )
        background_tasks.add_task(
            transaction_utils.log_transaction,
            model=Model.INVITATION,
            action=Action.CREATE,
            record_id=str(invitation.id),
            user_id=current_user.id,
            description="Invitation link created",
            meta_data=TransactionMetaData(new_data={"type": invitation.type}),
        )
        return InvitationCreateResponse(
            created_invitations=[invitation], existing_emails=[]
        )
    return InvitationCreateResponse(created_invitations=[], existing_emails=[])


@router.get(
    "/type-counts",
    dependencies=[Authenticated, IsSuperUser],
)
async def get_invitation_type_breakdown(
    session: AsyncSessionDep,
) -> InvitationTypeCount:
    """
    Get breakdown of invitations by type and status. Counts are split into active and inactive.
    """
    counts = {
        "email": 0,
        "link": 0,
        "active_total": 0,
        "inactive_total": 0,
        "total": 0,
        "registered": 0,
    }

    result = await session.exec(select(Invitation))
    invitations = result.all()
    active_invitations = [invite for invite in invitations if invite.active]
    type_counts = Counter(invite.type.value for invite in active_invitations)

    for type_name, count_value in type_counts.items():
        counts[type_name] = count_value

    counts["active_total"] = len(active_invitations)
    counts["inactive_total"] = len(invitations) - counts["active_total"]

    # Count registered users (invitations with associated users)
    registered_count = await session.scalar(
        select(func.count()).select_from(InvitationRegistration)
    )

    counts["registered"] = registered_count or 0
    counts["total"] = counts["active_total"] + counts["inactive_total"]

    return InvitationTypeCount(**counts)


@router.get("/{invitation_id}")
async def read_invitation(
    invitation_id: int,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> InvitationRead:
    """Get specific invitation"""
    invitation = (
        select(Invitation)
        .options(
            selectinload(Invitation.registered_users),
            selectinload(Invitation.created_by_user),
        )
        .where(Invitation.id == invitation_id)
    )
    result = await session.exec(invitation)
    invitation = result.first()
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    if invitation.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return InvitationRead.model_validate(invitation)


@router.get("/token/{token}")
async def read_invitation_by_token(
    token: uuid.UUID,
    session: AsyncSessionDep,
) -> InvitationTokenRead:
    """Get invitation details by token without authentication"""
    statement = select(Invitation).where(Invitation.token == token)
    result = await session.exec(statement)
    invitation = result.first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if not invitation.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation expired. Please contact the inviter for a new invitation.",
        )

    return InvitationTokenRead(
        type=invitation.type,
        email=invitation.email,
    )


@router.post(
    "/{invitation_id}/resend",
    dependencies=[Authenticated, IsSuperUser],
)
async def resend_invitation(
    invitation_id: int,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> Message:
    """Resend invitation email"""
    invitation = await session.get(Invitation, invitation_id)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.type == InvitationType.LINK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link invitations cannot be resent",
        )

    if invitation.type == InvitationType.EMAIL and invitation.email:
        await send_invitation_email(
            session=session,
            invitation=invitation,
            background_tasks=background_tasks,
        )

        background_tasks.add_task(
            transaction_utils.log_transaction,
            model=Model.INVITATION,
            action=Action.CREATE,
            user_id=current_user.id,
            record_id=str(invitation.id),
            description="Invitation email resent",
            meta_data=TransactionMetaData(new_data={"email": invitation.email}),
        )

    return Message(message="Invitation resent successfully")


@router.patch(
    "/{invitation_id}/deactivate",
    dependencies=[Authenticated, IsSuperUser],
)
async def deactivate_invitation(
    invitation_id: int,
    session: AsyncSessionDep,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
) -> Message:
    """Deactivate an invitation"""
    # Check invitation exists
    invitation = await session.get(Invitation, invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )

    # Deactivate invitation
    invitation.expires_at = datetime.now(tz=timezone.utc)

    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)

    background_tasks.add_task(
        transaction_utils.log_transaction,
        model=Model.INVITATION,
        action=Action.UPDATE,
        user_id=current_user.id,
        record_id=str(invitation.id),
        description="Invitation deactivated",
        meta_data=TransactionMetaData(),
    )

    return Message(message="Invitation deactivated")
