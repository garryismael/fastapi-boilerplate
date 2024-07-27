from datetime import UTC, datetime, timedelta
from typing import AsyncGenerator

import pytest
from app.configuration import settings
from app.domain.token_blacklist.models import TokenBlacklistCreate
from app.domain.user.models import User
from app.main import app
from app.services.security import create_access_token
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def token_expiry():
    return timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)


@pytest.fixture
def expired_token_expiry():
    return timedelta(minutes=-settings.ACCESS_TOKEN_EXPIRE_MINUTES - 1)


@pytest.fixture
async def base_url():
    return "http://test/api/v1"


@pytest.fixture
async def user_client(
    base_url: str, user_access_token: str, token_type: str
) -> AsyncGenerator[AsyncClient, None]:
    headers = {"Authorization": f"{token_type} {user_access_token}"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=base_url, headers=headers
    ) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture
async def admin_client(
    base_url: str, admin_access_token: str, token_type: str
) -> AsyncGenerator[AsyncClient, None]:
    headers = {"Authorization": f"{token_type} {admin_access_token}"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=base_url, headers=headers
    ) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture
async def super_admin_client(
    base_url: str, admin_access_token: str, token_type: str
) -> AsyncGenerator[AsyncClient, None]:
    headers = {"Authorization": f"{token_type} {admin_access_token}"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=base_url, headers=headers
    ) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture
async def public_client(base_url: str) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=base_url
    ) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture
async def token_type():
    return "Bearer"


@pytest.fixture
def user_access_token(user: User, token_expiry: timedelta):
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=token_expiry
    )
    return access_token


@pytest.fixture
def user_email_access_token(user: User, token_expiry: timedelta):
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=token_expiry
    )
    return access_token


@pytest.fixture
def expired_access_token(user: User, expired_token_expiry: timedelta):
    return create_access_token(
        data={"sub": user.username}, expires_delta=expired_token_expiry
    )


@pytest.fixture
def access_token_without_sub(user: User, token_expiry: timedelta):
    return create_access_token(
        data={"username": user.username}, expires_delta=token_expiry
    )


@pytest.fixture
def admin_access_token(superuser: User, token_expiry: timedelta):
    access_token = create_access_token(
        data={"sub": superuser.username}, expires_delta=token_expiry
    )
    return access_token


@pytest.fixture
def token_blacklist(admin_access_token: str, token_expiry: timedelta):
    return TokenBlacklistCreate(
        token=admin_access_token,
        expires_at=datetime.now(UTC).replace(tzinfo=None) + token_expiry,
    )
