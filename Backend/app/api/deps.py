from collections.abc import AsyncGenerator, Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core import security
from app.core.config import config
from app.core.db import AsyncSessionLocal, SessionLocal
from app.models.user import User
from app.schemas.common import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{config.API_ROOT_URL}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


SessionDep = Annotated[Session, Depends(get_db)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(session: AsyncSessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
        )
    user = await session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def is_superuser(current_user: CurrentUser) -> bool:
    if current_user and current_user.is_superuser:
        return True
    raise HTTPException(
        status_code=403,
        detail="The user doesn't have enough privileges",
    )


Authenticated = Depends(get_current_user)
IsSuperUser = Depends(is_superuser)
