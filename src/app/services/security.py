import re
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from app.configuration import settings
from app.constants.user import USER_UNAUTHORIZED
from app.data.crud.token_blacklist import crud_token_blacklist
from app.data.crud.user import crud_users
from app.domain.token_blacklist.models import Token, TokenData
from app.domain.user.models import User
from fastapi import Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastcrud.exceptions.http_exceptions import UnauthorizedException
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", scheme_name="OAuth2"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def authenticate_user(
    db: AsyncSession, form_data: OAuth2PasswordRequestForm
) -> User | None:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, form_data.username):
        db_user = await crud_users.get(
            db=db,
            schema_to_select=User,
            return_as_model=True,
            email=form_data.username,
            is_deleted=False,
        )
    else:
        db_user = await crud_users.get(
            db, username=form_data.username, is_deleted=False
        )

    if not db_user:
        return None

    user_model = User.model_validate(db_user, from_attributes=True)

    if not verify_password(form_data.password, user_model.hashed_password):
        return None

    return user_model


def create_access_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_token(
    response: Response, db: AsyncSession, form: OAuth2PasswordRequestForm
) -> Token:
    user = await authenticate_user(db, form)
    if user is None:
        raise UnauthorizedException(USER_UNAUTHORIZED)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    expire = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=expire
    )
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=max_age,
    )

    return Token(access_token=access_token, token_type=settings.TOKEN_TYPE)


async def verify_token(db: AsyncSession, token: str) -> TokenData | None:
    """Verify a JWT token and return TokenData if valid.

    Parameters
    ----------
    token: str
        The JWT token to be verified.

    Returns
    -------
    TokenData | None
        TokenData instance if the token is valid, None otherwise.
    """
    is_blacklisted = await crud_token_blacklist.exists(db=db, token=token)
    if is_blacklisted:
        return None
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except Exception:
        return None
    username_or_email: str | None = payload.get(
        "sub",
    )
    if username_or_email is None:
        return None
    return TokenData(username_or_email=username_or_email)
