from fastcrud.exceptions.http_exceptions import (
    DuplicateValueException,
    ForbiddenException,
    NotFoundException,
)
from fastcrud.paginated import compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.user import (
    EMAIL_ALREADY_REGISTERED,
    USER_DELETED,
    USER_FORBIDDEN,
    USER_NOT_FOUND,
    USERNAME_NOT_AVAILABLE,
)
from app.data.crud.token_blacklist import crud_token_blacklist
from app.data.crud.user import crud_users
from app.domain.user.models import (
    PaginatedListUserRead,
    UserCreate,
    UserCreateInternal,
    UserRead,
    UserUpdate,
)
from app.services.security import get_password_hash


async def _check_permission(db: AsyncSession, id: int, current_user: UserRead):
    db_user = await crud_users.get(db, id=id, is_delete=False)
    if db_user is None:
        raise NotFoundException(USER_NOT_FOUND)

    user = UserRead.model_validate(db_user, from_attributes=True)

    if user.username != current_user.username:
        raise ForbiddenException(USER_FORBIDDEN)

    return user


async def create_user(db: AsyncSession, user: UserCreate) -> UserRead:
    email_row = await crud_users.exists(db=db, email=user.email, is_delete=False)

    if email_row:
        raise DuplicateValueException(EMAIL_ALREADY_REGISTERED)

    username_row = await crud_users.exists(
        db=db, username=user.username, is_delete=False
    )

    if username_row:
        raise DuplicateValueException(USERNAME_NOT_AVAILABLE)

    hashed_password = get_password_hash(user.password)

    user_internal = UserCreateInternal(
        hashed_password=hashed_password, **user.model_dump(exclude={"password"})
    )

    created_user = await crud_users.create(db=db, object=user_internal)

    return UserRead.model_validate(created_user, from_attributes=True)


async def get_paginated_users(
    db: AsyncSession, page: int, items_per_page: int, is_superuser: bool
):
    users_data = await crud_users.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        schema_to_select=UserRead,
        return_as_model=True,
        is_superuser=is_superuser,
        is_delete=False,
    )

    response = paginated_response(
        crud_data=users_data, page=page, items_per_page=items_per_page
    )
    return PaginatedListUserRead.model_validate(response)


async def find_user(db: AsyncSession, id: int):
    db_user = await crud_users.get(db, id=id, is_delete=False)
    if db_user is None:
        raise NotFoundException(USER_NOT_FOUND)

    return UserRead.model_validate(db_user, from_attributes=True)


async def update_user(
    db: AsyncSession, id: int, values: UserUpdate, current_user: UserRead
):
    user = await _check_permission(db, id, current_user)

    if values.username != user.email:
        email_row = await crud_users.exists(db=db, email=values.email, is_delete=False)

        if email_row:
            raise DuplicateValueException(EMAIL_ALREADY_REGISTERED)

    if values.email != user.username:
        username_row = await crud_users.exists(
            db=db, username=values.username, is_delete=False
        )

        if username_row:
            raise DuplicateValueException(USERNAME_NOT_AVAILABLE)

    await crud_users.update(db, object=values, id=id, is_delete=False)

    response = {**user.model_dump(), **values.model_dump()}
    return UserRead(**response)


async def remove_user(db: AsyncSession, id: int, current_user: UserRead, token: str):
    user = await _check_permission(db, id, current_user)

    await crud_token_blacklist.db_delete(db, token=token)
    await crud_users.delete(db, id=user.id)

    return {"message": USER_DELETED}


async def remove_db_user(db: AsyncSession, id: int, current_user: UserRead, token: str):
    user = await _check_permission(db, id, current_user)

    await crud_token_blacklist.db_delete(db, token=token)
    await crud_users.db_delete(db, id=user.id)

    return {"message": USER_DELETED}
