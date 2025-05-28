from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import AsyncSessionDep, Authenticated, CurrentUser
from app.models.user_settings import UserSettings
from app.schemas.user_settings import (
    UserSettingsRead,
    UserSettingsUpdate,
)

router = APIRouter(
    prefix="/user-settings",
    tags=["user settings"],
    dependencies=[Authenticated],
)


@router.get("/me")
async def read_my_settings(
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> UserSettingsRead:
    """Get current user's settings"""
    settings = await session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = settings.one_or_none()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return UserSettingsRead.model_validate(settings)


@router.patch("/me")
async def update_my_settings(
    session: AsyncSessionDep,
    settings_in: UserSettingsUpdate,
    current_user: CurrentUser,
) -> UserSettingsRead:
    """Update current user's settings"""
    settings = await session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = settings.one_or_none()

    if not settings:
        # create settings if they don't exist
        settings = UserSettings(user_id=current_user.id)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)

    update_dict = settings_in.model_dump(exclude_unset=True)
    settings.sqlmodel_update(update_dict)
    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    return UserSettingsRead.model_validate(settings)
