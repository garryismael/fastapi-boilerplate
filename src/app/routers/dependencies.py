import re
from typing import Annotated

from fastapi import Depends
from fastcrud.exceptions.http_exceptions import (
    ForbiddenException,
    UnauthorizedException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.user import USER_FORBIDDEN, USER_NOT_AUTHENTICATED
from app.data.crud.user import crud_users
from app.data.database import async_get_db
from app.domain.user.models import UserRead
from app.services.security import oauth2_scheme, verify_token


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> UserRead:
    token_data = await verify_token(db, token)
    if token_data is None:
        raise UnauthorizedException(USER_NOT_AUTHENTICATED)

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, token_data.username_or_email):
        db_user = await crud_users.get(
            db=db, email=token_data.username_or_email, is_deleted=False
        )
    else:
        db_user = await crud_users.get(
            db=db, username=token_data.username_or_email, is_deleted=False
        )

    if db_user is None:
        raise UnauthorizedException(USER_NOT_AUTHENTICATED)

    return UserRead.model_validate(db_user, from_attributes=True)


async def get_current_superuser(
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    if not current_user.is_superuser:
        raise ForbiddenException(USER_FORBIDDEN)

    return current_user
