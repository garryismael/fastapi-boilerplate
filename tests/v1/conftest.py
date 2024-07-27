from collections.abc import Callable

import pytest
from app.domain.user.models import (
    PaginatedListUserRead,
    User,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services.security import get_password_hash


@pytest.fixture
def password() -> str:
    return "root"


@pytest.fixture
def user(password: str) -> User:
    return User(
        id=1,
        name="User",
        email="user@gmail.com",
        username="user",
        hashed_password=get_password_hash(password),
        is_superuser=False,
    )


@pytest.fixture
def superuser(password: str) -> User:
    return User(
        id=3,
        name="Super Admin",
        email="superuser@gmail.com",
        username="superadmin",
        hashed_password=get_password_hash(password),
        is_superuser=True,
    )


@pytest.fixture
def user_create_request() -> UserUpdate:
    return UserCreate(
        email="john@gmail.com",
        name="John Doe",
        password="root",
        is_superuser=True,
        username="johndoe",
    )


@pytest.fixture
def user_update_request() -> UserUpdate:
    return UserUpdate(
        email="johndoe@gmail.com",
        name="John Doe",
        username="johndoe",
    )


@pytest.fixture
def model_user(user_create_request: UserCreate) -> User:
    return User(
        id=1,
        name=user_create_request.name,
        username=user_create_request.username,
        email=user_create_request.email,
        hashed_password=get_password_hash(user_create_request.password),
        is_superuser=user_create_request.is_superuser,
    )


@pytest.fixture
def paginated_users(superuser: User) -> PaginatedListUserRead:
    return PaginatedListUserRead(
        data=[UserRead(**superuser.model_dump())],
        has_more=False,
        items_per_page=10,
        page=1,
        total_count=1,
    )


@pytest.fixture
async def get_current_user_override(user: User) -> Callable[[], User]:
    def get_current_user() -> User:
        return user

    return get_current_user


@pytest.fixture
async def get_current_superuser_override(superuser: User) -> Callable[[], User]:
    def get_current_user() -> User:
        return superuser

    return get_current_user


@pytest.fixture
async def get_regular_current_user_override(user: User) -> Callable[[], User]:
    def get_current_user() -> User:
        return user

    return get_current_user
