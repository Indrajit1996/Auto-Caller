from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import func, or_, select

from app.api.deps import (
    AsyncSessionDep,
    Authenticated,
    CurrentUser,
    IsSuperUser,
)
from app.models.group import Group
from app.models.notification import NotificationType
from app.models.transaction import Action, Model
from app.models.user import User
from app.schemas.common import Message
from app.schemas.group import (
    GroupCreate,
    GroupCreateInput,
    GroupRead,
    GroupReadWithUsers,
    GroupsDataTable,
    GroupsDataTableRequestBody,
    GroupsRead,
    GroupUpdate,
    GroupUserAdd,
)
from app.schemas.transaction import TransactionMetaData
from app.utils import notification as notification_utils
from app.utils import transaction as transaction_utils

router = APIRouter(prefix="/groups", tags=["groups"], dependencies=[Authenticated])


@router.get("/", dependencies=[IsSuperUser])
async def read_groups(
    session: AsyncSessionDep, offset: int = 0, limit: int = 100
) -> GroupsRead:
    """Retrieve groups with total count."""
    count_statement = select(func.count()).select_from(Group).where(Group.is_active)
    count = await session.scalar(count_statement)

    statement = select(Group).where(Group.is_active).offset(offset).limit(limit)
    groups = await session.scalars(statement)

    return GroupsRead.model_validate({"data": groups, "count": count})


@router.post(
    "/datatable",
    response_model=GroupsDataTable,
    dependencies=[IsSuperUser],
)
async def read_groups_advanced(
    session: AsyncSessionDep, body: GroupsDataTableRequestBody
) -> GroupsDataTable:
    """Read groups with advanced filtering, searching, and pagination."""
    # Create a subquery to count users for each group
    user_count_subquery = (
        select(Group.id.label("group_id"), func.count(User.id).label("user_count"))
        .join(Group.users)
        .group_by(Group.id)
        .subquery()
    )

    # Main query with user count
    query = (
        select(
            Group,
            func.coalesce(user_count_subquery.c.user_count, 0).label("user_count"),
        )
        .outerjoin(user_count_subquery, Group.id == user_count_subquery.c.group_id)
        .where(Group.is_active)
    )

    if body.search:
        search_terms = body.search.split()
        for term in search_terms:
            query = query.where(
                or_(
                    Group.name.ilike(f"%{term}%"),
                    Group.description.ilike(f"%{term}%"),
                )
            )

    if body.filters.user_id:
        query = query.where(Group.users.any(User.id == body.filters.user_id))

    # Count total matches for pagination
    count_query = select(func.count()).select_from(query.subquery())
    count = await session.scalar(count_query)

    # Apply sorting
    order_column = getattr(Group, body.order_by)
    if body.order == "desc":
        order_column = order_column.desc()
    query = query.order_by(order_column)

    # Apply pagination
    query = query.offset(body.offset).limit(body.limit)

    # Execute query
    result = await session.exec(query)
    groups_with_counts = result.all()

    # Process results
    groups = []
    for group, user_count in groups_with_counts:
        group_data = GroupRead.model_validate(group)
        group_data.user_count = user_count
        groups.append(group_data)

    return GroupsDataTable(data=groups, count=count or 0)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[IsSuperUser],
)
async def create_new_group(
    session: AsyncSessionDep,
    group_in: GroupCreateInput,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> GroupRead:
    """Create new group."""
    group_create = GroupCreate(
        name=group_in.name,
        description=group_in.description,
        created_by_user_id=current_user.id,
    )
    db_group = Group.model_validate(group_create)
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)

    background_tasks.add_task(
        transaction_utils.log_transaction,
        user_id=current_user.id,
        model=Model.GROUP,
        record_id=str(db_group.id),
        action=Action.CREATE,
        meta_data=TransactionMetaData(),
        description=f"Group {db_group.name} created",
    )

    # Send notification to admins about the group creation
    background_tasks.add_task(
        notification_utils.send_notification_to_admins,
        message=f"New group '{db_group.name}' was created by {current_user.full_name}",
        type=NotificationType.INFO,
        meta_data={"group_id": db_group.id, "created_by": str(current_user.id)},
    )

    return GroupRead.model_validate(db_group)


@router.get("/{group_id}")
async def read_group(session: AsyncSessionDep, group_id: int) -> GroupRead:
    """Get group by ID."""
    statement = (
        select(Group)
        .options(
            selectinload(Group.created_by_user),
        )
        .where(Group.id == group_id, Group.is_active)
    )
    group = await session.exec(statement)
    group = group.first()
    if not group or not group.is_active:
        raise HTTPException(status_code=404, detail="Group not found")
    return GroupRead.model_validate(group)


@router.patch("/{group_id}")
async def update_existing_group(
    session: AsyncSessionDep,
    group_id: int,
    group_in: GroupUpdate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
) -> GroupRead:
    """Update a group."""
    statement = (
        select(Group)
        .options(
            selectinload(Group.users),
        )
        .where(Group.id == group_id, Group.is_active)
    )
    result = await session.exec(statement)
    group = result.first()
    if not group or not group.is_active:
        raise HTTPException(status_code=404, detail="Group not found")

    # Convert model to dict with datetime serialization
    old_data = group.model_dump(exclude_unset=True, mode="json")

    group_data = group_in.model_dump(exclude_unset=True)
    for key, value in group_data.items():
        setattr(group, key, value)

    session.add(group)
    await session.commit()
    await session.refresh(group)

    background_tasks.add_task(
        transaction_utils.log_transaction,
        user_id=current_user.id,
        model=Model.GROUP,
        record_id=str(group_id),
        action=Action.UPDATE,
        meta_data=TransactionMetaData(
            old_data=old_data, new_data=group.model_dump(mode="json")
        ),
        description=f"Group {group.name} updated",
    )
    return GroupRead.model_validate(group)


@router.post("/{group_id}/users")
async def update_group_users(
    session: AsyncSessionDep,
    group_id: int,
    users_in: GroupUserAdd,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
) -> GroupReadWithUsers:
    """Update group users. Empty list removes all users."""
    # Verify group exists
    statement = (
        select(Group)
        .options(
            selectinload(Group.users),
        )
        .where(Group.id == group_id, Group.is_active)
    )
    result = await session.exec(statement)
    group = result.first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if not users_in.user_ids:
        group.users = []
        await session.commit()
        return GroupReadWithUsers.model_validate(group)

    # Verify all users exist
    query = select(User).where(User.id.in_(users_in.user_ids))
    result = await session.exec(query)
    users = result.all()
    found_user_ids = {user.id for user in users}
    invalid_user_ids = set(users_in.user_ids) - found_user_ids
    if invalid_user_ids:
        raise HTTPException(
            status_code=400, detail=f"Users not found: {invalid_user_ids}"
        )

    old_user_ids = [user.id for user in group.users]
    # Replace existing users with new list
    group.users = users
    await session.commit()
    await session.refresh(group)

    background_tasks.add_task(
        transaction_utils.log_transaction,
        user_id=current_user.id,
        model=Model.GROUP,
        record_id=str(group_id),
        action=Action.UPDATE,
        meta_data=TransactionMetaData(
            old_data={"users": [str(u) for u in old_user_ids]},
            new_data={"users": [str(u) for u in users_in.user_ids]},
        ),
        description=f"Group {group.name} users updated",
    )

    return GroupReadWithUsers.model_validate(group)


@router.delete("/{group_id}")
async def delete_existing_group(
    session: AsyncSessionDep,
    group_id: int,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
) -> Message:
    """Delete a group."""
    statement = select(Group).where(Group.id == group_id, Group.is_active)
    result = await session.exec(statement)
    group = result.first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group_name = group.name  # Store name before deletion for notification

    group.is_active = False
    session.add(group)
    await session.commit()

    background_tasks.add_task(
        transaction_utils.log_transaction,
        user_id=current_user.id,
        model=Model.GROUP,
        record_id=str(group_id),
        action=Action.DELETE,
        meta_data=TransactionMetaData(),
        description=f"Group {group.name} deleted",
    )

    # Send notification to admins about the group deletion
    background_tasks.add_task(
        notification_utils.send_notification_to_admins,
        message=f"Group '{group_name}' was deleted by {current_user.full_name}",
        type=NotificationType.WARNING,
        meta_data={"group_id": group_id, "deleted_by": str(current_user.id)},
    )

    return Message(message="Group deleted successfully")


@router.delete("/{group_id}/users/{user_id}")
async def remove_user_from_group(
    session: AsyncSessionDep,
    group_id: int,
    user_id: str,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
) -> Message:
    """Remove a specific user from a group."""
    # Verify group exists
    statement = (
        select(Group)
        .options(
            selectinload(Group.users),
        )
        .where(Group.id == group_id, Group.is_active)
    )
    result = await session.exec(statement)
    group = result.first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify user exists and is in the group
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user not in group.users:
        raise HTTPException(status_code=400, detail="User is not in this group")

    # Remove user from group
    old_user_ids = [str(u.id) for u in group.users]
    group.users.remove(user)
    await session.commit()
    await session.refresh(group)

    background_tasks.add_task(
        transaction_utils.log_transaction,
        user_id=current_user.id,
        model=Model.GROUP,
        record_id=str(group_id),
        action=Action.UPDATE,
        meta_data=TransactionMetaData(
            old_data={"users": old_user_ids},
            new_data={"users": [str(u.id) for u in group.users]},
        ),
        description=f"User {user_id} removed from group {group.name}",
    )

    return Message(message="User removed from group successfully")
