import uuid
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def create_user(*, session: AsyncSession, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e

    await session.refresh(db_obj)

    return db_obj


async def update_user(
    *, session: AsyncSession, db_user: User, user_in: UserUpdate
) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    """Get user by email asynchronously"""
    result = await session.exec(select(User).where(User.email == email.lower()))
    return result.first()


async def get_user_by_email_verification_token(
    *, token: str, session: AsyncSession
) -> User | None:
    """Get user by email verification token asynchronously"""
    try:
        uuid_token = uuid.UUID(token)
        result = await session.exec(
            select(User).where(User.email_verification_token == uuid_token)
        )
        return result.first()
    except ValueError:
        return None


def get_user_dict(*, user: User) -> dict:
    filtered_user_data = {
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_superuser": user.is_superuser,
        "status": user.status.name,
    }
    return filtered_user_data
