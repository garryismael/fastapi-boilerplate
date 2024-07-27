from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.database import async_get_db
from app.domain.user.models import (
    PaginatedListUserRead,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.domain.user.use_cases import (
    create_user,
    find_user,
    get_paginated_users,
    remove_db_user,
    remove_user,
    update_user,
)
from app.routers.dependencies import get_current_superuser, get_current_user
from app.services.security import oauth2_scheme

router = APIRouter(tags=["users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_superuser)],
)
async def add_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> UserRead:
    return await create_user(db, user)


@router.get(
    "",
    response_model=PaginatedListUserRead,
    dependencies=[Depends(get_current_superuser)],
)
async def read_users(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    items_per_page: int = 10,
    is_superuser: bool = False,
):
    return await get_paginated_users(db, page, items_per_page, is_superuser)


@router.get(
    "/me",
    response_model=UserRead,
)
async def get_authenticated_user(
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    return current_user


@router.get(
    "/{id}",
    response_model=UserRead,
    dependencies=[Depends(get_current_superuser)],
)
async def get_user(id: int, db: Annotated[AsyncSession, Depends(async_get_db)]):
    return await find_user(db, id)


@router.patch(
    "/{id}",
    response_model=UserRead,
)
async def patch_user(
    id: int,
    values: UserUpdate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    return await update_user(db, id, values, current_user)


@router.delete("/{id}")
async def delete_user(
    id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    return await remove_user(db, id, current_user, token)


@router.delete("/db/{id}")
async def erase_db_user(
    id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    current_user: Annotated[UserRead, Depends(get_current_superuser)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    return await remove_db_user(db, id, current_user, token)
