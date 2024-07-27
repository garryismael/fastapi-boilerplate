from collections.abc import Callable
from unittest.mock import AsyncMock, patch

import pytest
from app.constants.user import (
    EMAIL_ALREADY_REGISTERED,
    USER_DELETED,
    USER_FORBIDDEN,
    USER_NOT_AUTHENTICATED,
    USER_NOT_FOUND,
    USERNAME_NOT_AVAILABLE,
)
from app.data.crud.token_blacklist import crud_token_blacklist
from app.data.crud.user import crud_users
from app.domain.token_blacklist.models import TokenBlacklistCreate
from app.domain.user.models import PaginatedListUserRead, User, UserCreate, UserUpdate
from app.main import app
from app.routers.dependencies import get_current_superuser, get_current_user
from fastapi import status
from httpx import AsyncClient


@patch.object(crud_users, "get", return_value=None)
@patch.object(
    crud_token_blacklist, "exists", return_value=False, new_callable=AsyncMock
)
async def test_get_current_user_not_found(
    mock_token_blacklist_exists: AsyncMock,
    mock_get_user: AsyncMock,
    admin_client: AsyncClient,
):
    response = await admin_client.get("/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == USER_NOT_AUTHENTICATED
    mock_token_blacklist_exists.assert_called_once()
    mock_get_user.assert_called_once()


@patch.object(crud_users, "get", return_value=None)
@patch.object(crud_token_blacklist, "exists", return_value=True, new_callable=AsyncMock)
async def test_get_current_user_token_blacklisted(
    mock_token_blacklist_exists: AsyncMock,
    mock_get_user: AsyncMock,
    admin_client: AsyncClient,
):
    response = await admin_client.get("/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == USER_NOT_AUTHENTICATED
    mock_token_blacklist_exists.assert_called_once()
    mock_get_user.assert_not_called()


@patch.object(crud_users, "get")
@patch.object(
    crud_token_blacklist, "exists", return_value=False, new_callable=AsyncMock
)
async def test_get_current_user_token_invalid(
    mock_token_blacklist_exists: AsyncMock,
    mock_get_user: AsyncMock,
    token_type: str,
    public_client: AsyncClient,
):
    response = await public_client.get(
        "/users/me",
        headers={"Authorization": f"{token_type} INVALID_TOKEN"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == USER_NOT_AUTHENTICATED
    mock_token_blacklist_exists.assert_called_once()
    mock_get_user.assert_not_called()


@patch.object(crud_users, "get")
@patch.object(
    crud_token_blacklist, "exists", return_value=False, new_callable=AsyncMock
)
async def test_get_current_user_token_expired(
    mock_token_blacklist_exists: AsyncMock,
    mock_get_user: AsyncMock,
    public_client: AsyncClient,
    token_type: str,
    expired_token_expiry: str,
):
    response = await public_client.get(
        "/users/me",
        headers={"Authorization": f"{token_type} ${expired_token_expiry}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == USER_NOT_AUTHENTICATED
    mock_token_blacklist_exists.assert_called_once()
    mock_get_user.assert_not_called()


@patch.object(crud_users, "get")
@patch.object(
    crud_token_blacklist, "exists", return_value=False, new_callable=AsyncMock
)
async def test_get_current_user_token_without_sub(
    mock_token_blacklist_exists: AsyncMock,
    mock_get_user: AsyncMock,
    public_client: AsyncClient,
    token_type: str,
    access_token_without_sub: str,
):
    response = await public_client.get(
        "/users/me",
        headers={"Authorization": f"{token_type} ${access_token_without_sub}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == USER_NOT_AUTHENTICATED
    mock_token_blacklist_exists.assert_called_once()
    mock_get_user.assert_not_called()


@patch.object(crud_users, "get")
@patch.object(
    crud_token_blacklist, "exists", return_value=False, new_callable=AsyncMock
)
async def test_get_current_user(
    mock_token_blacklist_exists: AsyncMock,
    mock_get_user: AsyncMock,
    public_client: AsyncClient,
    superuser: User,
    token_type: str,
    user_email_access_token: str,
):
    mock_get_user.return_value = superuser
    headers = {"Authorization": f"{token_type} {user_email_access_token}"}

    response = await public_client.get("/users/me", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == superuser.model_dump(exclude={"hashed_password"})
    mock_token_blacklist_exists.assert_called_once()
    mock_get_user.assert_called_once()


async def test_create_user_forbidden(
    user_client: AsyncClient,
    user_create_request: UserCreate,
    get_regular_current_user_override,
):
    app.dependency_overrides[get_current_user] = get_regular_current_user_override

    response = await user_client.post(
        "/users",
        json=user_create_request.model_dump(),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == USER_FORBIDDEN


@pytest.mark.parametrize(
    "scenarios",
    [
        {"side_effect": [True], "detail": EMAIL_ALREADY_REGISTERED},
        {"side_effect": [False, True], "detail": USERNAME_NOT_AVAILABLE},
    ],
)
@patch.object(crud_users, "exists", new_callable=AsyncMock)
async def test_create_user_email_or_username_exists(
    mock_crud_users_exists: AsyncMock,
    super_admin_client: AsyncClient,
    scenarios: dict[str, list[bool] | str | None],
    user_create_request: UserCreate,
    get_current_superuser_override: Callable[[], User],
):
    app.dependency_overrides[get_current_superuser] = get_current_superuser_override
    mock_crud_users_exists.side_effect = scenarios.get("side_effect")

    response = await super_admin_client.post(
        "/users",
        json=user_create_request.model_dump(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"] == scenarios.get("detail")
    mock_crud_users_exists.assert_called()


@patch.object(crud_users, "create", new_callable=AsyncMock)
@patch.object(crud_users, "exists", side_effect=[False, False], new_callable=AsyncMock)
async def test_create_user(
    mock_crud_users_exists: AsyncMock,
    mock_crud_users_create: AsyncMock,
    super_admin_client: AsyncClient,
    user_create_request: UserCreate,
    model_user: User,
    get_current_superuser_override: Callable[[], User],
):
    mock_crud_users_create.return_value = model_user
    app.dependency_overrides[get_current_superuser] = get_current_superuser_override

    response = await super_admin_client.post(
        "/users",
        json=user_create_request.model_dump(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    mock_crud_users_exists.assert_called()
    mock_crud_users_create.assert_called_once()


@patch.object(crud_users, "get", return_value=None, new_callable=AsyncMock)
async def test_get_user_not_found(
    mock_crud_users_get: AsyncMock,
    super_admin_client: AsyncClient,
    get_current_superuser_override: Callable[[], User],
):
    app.dependency_overrides[get_current_superuser] = get_current_superuser_override

    response = await super_admin_client.get(
        "/users/1",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    mock_crud_users_get.assert_called()


@patch.object(crud_users, "get", new_callable=AsyncMock)
async def test_get_user(
    mock_crud_users_get: AsyncMock,
    super_admin_client: AsyncClient,
    superuser: User,
    get_current_superuser_override: Callable[[], User],
):
    app.dependency_overrides[get_current_superuser] = get_current_superuser_override
    mock_crud_users_get.return_value = superuser

    response = await super_admin_client.get(
        "/users/1",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == superuser.model_dump(exclude={"hashed_password"})
    mock_crud_users_get.assert_called()


@patch.object(crud_users, "get_multi", new_callable=AsyncMock)
async def test_get_admin_users(
    mock_crud_users_get_multi: AsyncMock,
    admin_client: AsyncClient,
    paginated_users: PaginatedListUserRead,
    get_current_superuser_override: Callable[[], User],
):
    mock_crud_users_get_multi.return_value = paginated_users.model_dump()
    params = {
        "page": paginated_users.page,
        "items_per_page": paginated_users.items_per_page,
        "is_superuser": True,
    }
    app.dependency_overrides[get_current_superuser] = get_current_superuser_override

    response = await admin_client.get(
        "/users",
        params=params,
    )

    assert response.json() == {
        "data": [user.model_dump() for user in paginated_users.data],
        "total_count": paginated_users.total_count,
        "has_more": (paginated_users.page * paginated_users.items_per_page)
        < paginated_users.total_count,
        "page": paginated_users.page,
        "items_per_page": paginated_users.items_per_page,
    }


@patch.object(crud_users, "get", return_value=None, new_callable=AsyncMock)
async def test_patch_user_not_found(
    mock_crud_users_get: AsyncMock,
    admin_client: AsyncClient,
    user_update_request: UserUpdate,
    get_current_user_override,
):
    app.dependency_overrides[get_current_user] = get_current_user_override

    response = await admin_client.patch(
        "/users/1",
        json=user_update_request.model_dump(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == USER_NOT_FOUND
    mock_crud_users_get.assert_called()


@patch.object(crud_users, "get")
async def test_patch_user_forbidden(
    mock_crud_users_get: AsyncMock,
    user: User,
    admin_client: AsyncClient,
    user_update_request: UserUpdate,
    get_current_superuser_override: Callable[[], User],
):
    app.dependency_overrides[get_current_user] = get_current_superuser_override
    mock_crud_users_get.return_value = user

    response = await admin_client.patch(
        "/users/1",
        json=user_update_request.model_dump(),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == USER_FORBIDDEN
    mock_crud_users_get.assert_called_once()


@pytest.mark.parametrize(
    "scenarios",
    [
        {"side_effect": [True], "detail": EMAIL_ALREADY_REGISTERED},
        {"side_effect": [False, True], "detail": USERNAME_NOT_AVAILABLE},
    ],
)
@patch.object(crud_users, "exists")
@patch.object(crud_users, "get")
async def test_patch_user_duplicate_email_or_username(
    mock_crud_users_get: AsyncMock,
    mock_crud_users_exists: AsyncMock,
    admin_client: AsyncClient,
    scenarios: dict[str, list[bool] | str],
    user_update_request: UserUpdate,
    user: User,
    get_current_user_override: Callable[[], User],
):
    mock_crud_users_get.return_value = user
    mock_crud_users_exists.side_effect = scenarios.get("side_effect")
    app.dependency_overrides[get_current_user] = get_current_user_override

    response = await admin_client.patch(
        "/users/1",
        json=user_update_request.model_dump(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"] == scenarios.get("detail")
    mock_crud_users_get.assert_called_once()
    mock_crud_users_exists.assert_called()


@patch.object(crud_users, "update", return_value=None)
@patch.object(crud_users, "exists", side_effect=[False, False])
@patch.object(crud_users, "get")
async def test_patch_user(
    mock_crud_users_get: AsyncMock,
    mock_crud_users_exists: AsyncMock,
    mock_crud_users_update: AsyncMock,
    admin_client: AsyncClient,
    user_update_request: UserUpdate,
    superuser: User,
    get_current_superuser_override: Callable[[], User],
):
    mock_crud_users_get.return_value = superuser
    app.dependency_overrides[get_current_user] = get_current_superuser_override

    response = await admin_client.patch(
        "/users/1",
        json=user_update_request.model_dump(),
    )

    assert response.status_code == status.HTTP_200_OK
    mock_crud_users_get.assert_called_once()
    mock_crud_users_exists.assert_called()
    mock_crud_users_update.assert_called_once()


@patch.object(crud_users, "get", return_value=None)
async def test_delete_user_not_found(
    mock_crud_users: AsyncMock, admin_client: AsyncClient, get_current_user_override
):
    app.dependency_overrides[get_current_user] = get_current_user_override

    response = await admin_client.delete("/users/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == USER_NOT_FOUND
    mock_crud_users.assert_called_once()


@patch.object(crud_users, "get")
async def test_delete_user_forbidden(
    mock_crud_users_get: AsyncMock,
    user: User,
    admin_client: AsyncClient,
    get_current_superuser_override: Callable[[], User],
):
    mock_crud_users_get.return_value = user
    app.dependency_overrides[get_current_user] = get_current_superuser_override

    response = await admin_client.delete("/users/1")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == USER_FORBIDDEN
    mock_crud_users_get.assert_called_once()


@patch.object(crud_token_blacklist, "db_delete", new_callable=AsyncMock)
@patch.object(crud_users, "delete", new_callable=AsyncMock)
@patch.object(crud_users, "get")
async def test_delete_user(
    mock_crud_users_get: AsyncMock,
    mock_crud_users_delete: AsyncMock,
    mock_crud_token_blacklist_db_delete: AsyncMock,
    admin_client: AsyncClient,
    superuser: User,
    token_blacklist: TokenBlacklistCreate,
    get_current_superuser_override: Callable[[], User],
):
    mock_crud_users_get.return_value = superuser
    mock_crud_token_blacklist_db_delete.return_value = token_blacklist
    app.dependency_overrides[get_current_user] = get_current_superuser_override

    response = await admin_client.delete("/users/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == USER_DELETED
    mock_crud_users_get.assert_called_once()
    mock_crud_users_delete.assert_called_once()
    mock_crud_token_blacklist_db_delete.assert_called_once()


@patch.object(crud_users, "get", return_value=None)
async def test_erase_db_user_not_found(
    mock_crud_users_get: AsyncMock,
    admin_client: AsyncClient,
    get_current_superuser_override: Callable[[], User],
):
    app.dependency_overrides[get_current_user] = get_current_superuser_override

    response = await admin_client.delete("/users/db/1")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == USER_NOT_FOUND
    mock_crud_users_get.assert_called_once()


@patch.object(crud_users, "get")
async def test_erase_user_forbidden(
    mock_crud_users_get: AsyncMock,
    user: User,
    admin_client: AsyncClient,
    get_current_superuser_override: Callable[[], User],
):
    mock_crud_users_get.return_value = user
    app.dependency_overrides[get_current_user] = get_current_superuser_override

    response = await admin_client.delete("/users/db/1")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == USER_FORBIDDEN
    mock_crud_users_get.assert_called_once()


@patch.object(crud_token_blacklist, "db_delete", new_callable=AsyncMock)
@patch.object(crud_users, "db_delete", new_callable=AsyncMock)
@patch.object(crud_users, "get", new_callable=AsyncMock)
async def test_erase_db_user(
    mock_crud_users_get: AsyncMock,
    mock_crud_users_db_delete: AsyncMock,
    mock_crud_token_blacklist_db_delete: AsyncMock,
    admin_client: AsyncClient,
    token_blacklist: TokenBlacklistCreate,
    superuser: User,
    get_current_superuser_override: Callable[[], User],
):
    mock_crud_users_get.return_value = superuser
    mock_crud_token_blacklist_db_delete.return_value = token_blacklist
    app.dependency_overrides[get_current_superuser] = get_current_superuser_override

    response = await admin_client.delete("/users/db/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == USER_DELETED
    mock_crud_users_get.assert_called_once()
    mock_crud_users_db_delete.assert_called_once()
    mock_crud_token_blacklist_db_delete.assert_called_once()
