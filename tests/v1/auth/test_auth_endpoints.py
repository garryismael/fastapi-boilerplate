from unittest.mock import AsyncMock, patch

import pytest
from app.constants.user import USER_UNAUTHORIZED
from app.data.crud.user import crud_users
from app.domain.user.models import User
from fastapi import status
from httpx import AsyncClient


@pytest.mark.parametrize(
    "login_request",
    [
        {"username": "john@gmail.com", "password": "root"},
        {"username": "john", "password": "root"},
    ],
)
@patch.object(crud_users, "get", return_value=None, new_callable=AsyncMock)
async def test_login_unauthorized_user(
    mock_crud_users_get: AsyncMock,
    login_request: dict[str, str],
    user_client: AsyncClient,
):
    response = await user_client.post("/auth/login", data=login_request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == USER_UNAUTHORIZED
    mock_crud_users_get.assert_called_once()


@patch.object(crud_users, "get", new_callable=AsyncMock)
async def test_login_invalid_password(
    mock_crud_users_get: AsyncMock,
    super_admin_client: AsyncClient,
    superuser: User,
):
    mock_crud_users_get.return_value = superuser

    response = await super_admin_client.post(
        "/auth/login", data={"username": superuser.email, "password": "invalid"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == USER_UNAUTHORIZED
    mock_crud_users_get.assert_called_once()


@patch.object(crud_users, "get", new_callable=AsyncMock)
async def test_login_valid(
    mock_crud_users_get: AsyncMock,
    super_admin_client: AsyncClient,
    superuser: User,
    password: str,
    token_type: str,
):
    mock_crud_users_get.return_value = superuser

    response = await super_admin_client.post(
        "/auth/login", data={"username": superuser.email, "password": password}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.cookies.get("refresh_token") is not None
    assert response.json()["access_token"] is not None
    assert response.json()["token_type"] == token_type
    mock_crud_users_get.assert_called_once()
